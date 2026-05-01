"""
Pipeline compilation and execution for the backend Nextflow workflow system.

This module is responsible for taking the backend graph representation of a
pipeline, validating and normalizing its nodes, compiling those nodes into
nf-core module calls, generating the final `main.nf` workflow script plus the
corresponding `conf/modules.config` overrides file, and then optionally
launching the workflow with Nextflow.

- this file is part of the newer nf-core-based architecture
- it does not build raw shell commands for tools directly
- tool-specific argument serialization is delegated to
  `modules_config_builder.py`
- nf-core module metadata such as process names, module paths, and output
  accessors are defined in `compiled_node.py`

  Current limitation:
- the compiler currently assumes a primarily linear pipeline flow
  (input -> stage -> stage -> ...)
- branching and merge-heavy graphs will require a future refactor toward
  explicit edge/channel-based compilation
"""

from __future__ import annotations


import os
import sys
from abc import ABC, abstractmethod
from typing import Any

[sys.path.append(i) for i in ['.', '..']]

from backend.compiled_node import CompiledNode, get_module_spec
from backend.modules_config_builder import (
    build_ext_args2_for_tool,
    build_ext_args_for_tool,
    render_modules_config,
)
from backend.tool_registry import ToolRegistry
from shared.graph import Graph, Node

from uuid import UUID, uuid4

ArgDict = dict[str, Any]


class Pipeline(ABC):
    def __init__(self, graph: Graph, tool_registry: ToolRegistry):
        self.graph = graph
        self.registry = tool_registry

    @abstractmethod
    def run_pipeline(self):
        pass

    @abstractmethod
    def stop_pipeline(self):
        pass


class NextflowPipeline(Pipeline):
    def __init__(
        self,
        graph: Graph,
        tool_registry: ToolRegistry,
        uuid: UUID | None = None,
        pipeline_script_path: str | None = None,
        modules_config_path: str | None = None,
        nextflow_config_path: str | None = None,
    ):
        super().__init__(graph, tool_registry)

        backend_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(backend_dir, ".."))

        self.pipeline_script_path = os.path.abspath(
            pipeline_script_path or os.path.join(repo_root, "main.nf"))

        self.uuid: UUID = uuid if uuid is not None else uuid4()

        self.modules_config_path = os.path.abspath(
            modules_config_path
            or os.path.join(repo_root, "conf", "modules.config",
            )
        )

        self.nextflow_config_path = os.path.abspath(
            nextflow_config_path or os.path.join(backend_dir, "nextflow.config")
        )

    def run_pipeline(self):
        generator = NextflowGenerator(self.graph, self.registry)

        generator.prepare_graph()
        main_nf = generator.generate_pipeline()
        modules_config = generator.generate_modules_config()

        pipeline_dir = os.path.dirname(self.pipeline_script_path)
        modules_dir = os.path.dirname(self.modules_config_path)

        if pipeline_dir:
            os.makedirs(pipeline_dir, exist_ok=True)
        if modules_dir:
            os.makedirs(modules_dir, exist_ok=True)

        with open(self.pipeline_script_path, "w", encoding="utf-8") as f:
            f.write(main_nf)

        with open(self.modules_config_path, "w", encoding="utf-8") as f:
            f.write(modules_config)

        print("Generated pipeline script:")
        print(main_nf)
        print("\nGenerated modules config:")
        print(modules_config)

        import subprocess
        subprocess.run(
            [
                "nextflow",
                "run",
                self.pipeline_script_path,
                "-c",
                self.nextflow_config_path,
                "-c",
                self.modules_config_path,
            ],
            check=True,
        )

    def stop_pipeline(self):
        print('Stopping Nextflow pipeline...')

    def revise_stage_params(self, stage_num, param_key, new_val):
        print(f'Revising parameters for stage {stage_num}: setting {param_key} to {new_val}')


class PipelineFactory:
    def __init__(self):
        self.pipelines = {}

    def build_pipeline(self, pipeline_type, graph, input_folder, tool_registry, **kwargs):
        if pipeline_type == 'nextflow':
            return NextflowPipeline(graph, tool_registry, **kwargs)
        raise ValueError(f'Unknown pipeline type: {pipeline_type}')


class NextflowGenerator:
    def __init__(self, graph: Graph, tool_registry: ToolRegistry):
        self.graph = graph
        self.registry = tool_registry
        self._prepared = False
        self._input_files: list[str] = []
        self._compiled_nodes: list[CompiledNode] | None = None

    def _linearize_graph(self) -> list[Node]:
        ordered = []
        curr = self.graph.get_first_node()

        while curr:
            ordered.append(curr)
            curr = curr.next_node

        return ordered

    def _normalize_input_reads(self, node: Node) -> list[str]:
        payload = node.outputs if node.outputs else node.inputs

        while isinstance(payload, dict) and 'reads' in payload:
            payload = payload['reads']

        if isinstance(payload, str):
            return [payload]
        if isinstance(payload, (list, tuple)):
            return [str(item) for item in payload]

        raise ValueError(
            'error.'
        )
    
    def _canonical_tool_key(self, tool_name: str) -> str:
        return self.registry.normalize_tool_key(tool_name)
    
    def _apply_registry_validation(self, tool: str, args: ArgDict) -> None:
        errors = self.registry.validate_tool_args(tool, args, context={'graph': self.graph})
        if errors:
            raise ValueError(f'{tool} validation failed: {errors}')
        
    def _apply_registry_defaults(self, tool: str, args: ArgDict) -> ArgDict:
        raw_args: ArgDict = dict(args or {})
        defaults: ArgDict = dict(self.registry.get_default_tool_args(tool) or {})
        defaults.update(raw_args)
        return defaults
    
    def _resolve_stage_outputs(self, node: Node, tool: str, normalized_args: ArgDict) -> ArgDict:
        context = {
            'stage_work_dir': f'/work/stage_{node.node_num}',
            'output_prefix': f'sample{node.node_num}',
        }
        return dict(self.registry.resolve_tool_outputs(tool, normalized_args, context) or {})


    def prepare_graph(self):
        ordered_nodes = self._linearize_graph()
        if not ordered_nodes:
            raise ValueError('Cannot compile an empty graph.')

        input_node = ordered_nodes[0]
        input_tool = (input_node.tool or "").strip().lower()
        if input_tool != 'input':
            raise ValueError('The first node in the graph must be an input node.')

        input_node.tool = 'input'
        self._input_files = self._normalize_input_reads(input_node)

        prev_outputs = input_node.outputs

        for node in ordered_nodes[1:]:
            tool = self._canonical_tool_key(node.tool)
            raw_args = dict(node.args or {})

            print(tool)
            print(raw_args)

            self._apply_registry_validation(tool, raw_args)
            normalized_args = self._apply_registry_defaults(tool, raw_args)

            node.tool = tool
            node.args = normalized_args

            if node.inputs is None:
                if node.prev_node is None:
                    node.inputs = node.outputs
                else:
                    node.inputs = prev_outputs

            resolved_outputs = self._resolve_stage_outputs(node, tool, node.args)
            if resolved_outputs is not None:
                node.outputs = resolved_outputs

            prev_outputs = node.outputs

        self._prepared = True
        self._compiled_nodes = None
        return ordered_nodes

    def _tool_counts(self, ordered_nodes: list[Node]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for node in ordered_nodes:
            if node.tool == 'input':
                continue
            counts[node.tool] = counts.get(node.tool, 0) + 1
        return counts

    def _build_alias(self, process_name: str, tool: str, alias_counts: dict[str, int], tool_counts: dict[str, int]) -> str:
        if tool_counts.get(tool, 0) <= 1:
            return process_name

        alias_counts[tool] = alias_counts.get(tool, 0) + 1
        return f'{process_name}{alias_counts[tool]}'

    def _channel_name_from_alias(self, alias: str) -> str:
        return f'ch_{alias.lower()}'

    def compile_graph(self) -> tuple[list[str], list[CompiledNode]]:
        if not self._prepared:
            self.prepare_graph()
        if self._compiled_nodes is not None:
            return self._input_files, self._compiled_nodes

        ordered_nodes = self._linearize_graph()
        tool_counts = self._tool_counts(ordered_nodes)
        alias_counts: dict[str, int] = {}
        compiled_nodes: list[CompiledNode] = []
        active_data_channel = 'reads_ch'

        for node in ordered_nodes[1:]:
            tool = str(node.tool)
            normalized_args: ArgDict = dict(node.args or {})

            spec = get_module_spec(tool)
            alias = self._build_alias(spec.process_name, tool, alias_counts, tool_counts)
            output_channel = self._channel_name_from_alias(alias)

            compiled_node = CompiledNode(
                node_num=node.node_num,
                tool=tool,
                module_path=spec.module_path,
                process_name=spec.process_name,
                alias=alias,
                input_channel=active_data_channel,
                output_channel=output_channel,
                output_accessor=spec.output_accessor,
                advances_primary_channel=spec.advances_primary_channel,
                normalized_args=normalized_args,
                ext_args=build_ext_args_for_tool(tool, normalized_args),
                ext_args2=build_ext_args2_for_tool(tool, normalized_args),
                publish_subdir=spec.publish_subdir,
            )

            compiled_nodes.append(compiled_node)

            if compiled_node.advances_primary_channel:
                active_data_channel = compiled_node.output_channel

        self._compiled_nodes = compiled_nodes
        return self._input_files, compiled_nodes

    def generate_input_parameters(self, input_files: list[str]) -> str:
        lines = ['params.input = [']
        lines.extend(f'    "{path}",' for path in input_files)
        if input_files:
            lines[-1] = lines[-1].rstrip(',')
        lines.append(']')
        return '\n'.join(lines)

    def generate_input_channel_str(self) -> str:
        return (
            '    reads_ch = Channel.fromPath(params.input, checkIfExists: true)\n'
            '        .map { f ->\n'
            '            def name = f.getName()\n\n'
            '            def sample_id = name\n'
            '                .replaceAll(/_R?1(_\\d+)?\\.(fastq|fq)(\\.gz)?$/, \'\')\n'
            '                .replaceAll(/_R?2(_\\d+)?\\.(fastq|fq)(\\.gz)?$/, \'\')\n\n'
            '            tuple(sample_id, f)\n'
            '        }\n'
            '        .groupTuple()\n'
            '        .map { sample_id, files ->\n\n'
            '            def r1s = files.findAll { it.name ==~ /.*_R?1(_\\d+)?\\.(fastq|fq)(\\.gz)?$/ }.sort()\n'
            '            def r2s = files.findAll { it.name ==~ /.*_R?2(_\\d+)?\\.(fastq|fq)(\\.gz)?$/ }.sort()\n\n'
            '            if (r1s && r2s) {\n'
            '                def meta = [ id: sample_id, single_end: false ]\n'
            '                tuple(meta, [ r1s, r2s ])\n'
            '            } else {\n'
            '                def meta = [ id: sample_id, single_end: true ]\n'
            '                tuple(meta, files[0])\n'
            '            }\n'
            '        }\n'
        )

    def generate_nfcore_include_statement(self, node: CompiledNode) -> str:
        if node.alias == node.process_name:
            return f"include {{ {node.process_name} }} from '{node.module_path}'"
        return f"include {{ {node.process_name} as {node.alias} }} from '{node.module_path}'"

    def generate_execution_block(self, node: CompiledNode) -> str:
        return f'    {node.alias}({node.input_channel})'

    def generate_output_channel_str(self, node: CompiledNode) -> str:
        return f'    {node.output_channel} = {node.alias}.{node.output_accessor}'

    def generate_pipeline(self, graph=None) -> str:
        input_files, compiled_nodes = self.compile_graph()

        lines = [
            'nextflow.enable.dsl=2',
            '',
            self.generate_input_parameters(input_files),
            '',
        ]

        for node in compiled_nodes:
            lines.append(self.generate_nfcore_include_statement(node))

        lines.extend(['', 'workflow {', '', self.generate_input_channel_str(), ''])

        for node in compiled_nodes:
            lines.append(self.generate_execution_block(node))
            lines.append(self.generate_output_channel_str(node))
            lines.append('')

        lines.append('}')
        lines.append('')
        return '\n'.join(lines)

    def generate_modules_config(self) -> str:
        _, compiled_nodes = self.compile_graph()
        return render_modules_config(compiled_nodes)

    def render_main_nf(self, input_files: list[str] | None = None, compiled_nodes: list[CompiledNode] | None = None) -> str:
        if input_files is None or compiled_nodes is None:
            return self.generate_pipeline()

        lines = [
            'nextflow.enable.dsl=2',
            '',
            self.generate_input_parameters(input_files),
            '',
        ]

        for node in compiled_nodes:
            lines.append(self.generate_nfcore_include_statement(node))

        lines.extend(['', 'workflow {', '', self.generate_input_channel_str(), ''])

        for node in compiled_nodes:
            lines.append(self.generate_execution_block(node))
            lines.append(self.generate_output_channel_str(node))
            lines.append('')

        lines.append('}')
        lines.append('')
        return '\n'.join(lines)
