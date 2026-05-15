"""
Pipeline compilation and execution for the backend Nextflow workflow system.

This module takes the backend graph representation of a pipeline, validates,
and normalizes its nodes, compiles those nodes into nf-core module calls, and
generates the final manin.nf workflow script plus the matching conf/modules.config
override file.

-this file is part of the newer nf-core based architecture. It doesnt build raw
shell commands for tools directly. Tool specific argument serialization is handled
by modules_config_builder.py, while nf-core module metadata is defined in compiled_node.py

  Current limitation:
- the compiler supports simple branching through multiple outgoing edges.
- Each node still tracks one primary previous node, so merge-heavy graphs
and tools with multiple required inputs will need future edge/channel 
compilation logic.
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
from collections import deque # for BFS graph traversal

from uuid import UUID, uuid4

ArgDict = dict[str, Any]


class Pipeline(ABC):
    """
    Abstract base class for backend pipeline implementations.

    Pipeline subclasses own a backend graph and know how to run or stop that
    graph using a specific workflow engine.
    """
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
    """
    Pipeline implementation that generates and runs a Nextflow workflow.

    This class owns the output paths for main.nf, conf/modules.config, and
    the base Nextflow config file. The graph to Nextflow conversion itself is
    delegated to NextflowGenerator.
    """
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
        """
        Generate Nextflow files for this pipeline and execute them.

        This writes the generated main.nf and conf/modules.config files to
        disk, then starts Nextflow using both the base backend config and the
        generated module override config.
        """
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
    """
    Factory for creating backend pipeline implementations.

     The project currently supports Nextflow pipelines, but this class leaves a
     clear extension point for adding other workflow engines later.
    """
    def __init__(self):
        self.pipelines = {}

    def build_pipeline(self, pipeline_type, graph, input_folder, tool_registry, **kwargs):
        if pipeline_type == 'nextflow':
            return NextflowPipeline(graph, tool_registry, **kwargs)
        raise ValueError(f'Unknown pipeline type: {pipeline_type}')


class NextflowGenerator:
    """
    Compile a backend graph into Nextflow DSL2 source code.

    The generator prepares graph nodes, normalizes tool names and arguments,
    creates CompiledNode objects, and renders the strings used for main.nf
    and conf/modules.config .
    """
    def __init__(self, graph: Graph, tool_registry: ToolRegistry):
        self.graph = graph
        self.registry = tool_registry
        self._prepared = False
        self._input_files: list[str] = []
        self._compiled_nodes: list[CompiledNode] | None = None

    def _linearize_graph(self) -> list[Node]:
        """
        Traverse the graph with breadth-first search and return nodes in run order.

        The input node is kept first because the generated Nextflow workflow needs
         to build the initial reads channel before running tool stages.
        """
        ordered = []
        curr = self.graph.get_first_node()
        ordered.append(curr)
        queue = deque(curr.next_nodes)

        while queue:
            current_node = queue.popleft()
            if current_node is not None:
                if current_node not in ordered:
                    # If the node is an input, insert it as the first node in the ordered list
                    if current_node.tool == 'input':
                        ordered.insert(0, current_node)
                    ordered.append(current_node) # For all other nodes, append to the ordered list

                # Traverse all connected tools
                for node in current_node.next_nodes:
                    if node not in ordered:
                        ordered.append(node)
                        queue.append(node)

        return ordered

    def _normalize_input_reads(self, node: Node) -> list[str]:
        """
        Extract input FASTQ paths from an input node.

        Input nodes may store reads directly as a string/list or inside nested
        dictionaries such as `{"reads": {"reads": [...]}}`. This normalizes those
        shapes into a flat list of path strings for `params.input`.
        """
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
        """
        Validate and normalize the graph before Nextflow code generation.

        This method ensures the graph starts with an input node, extracts input
        file paths, canonicalizes tool names, applies registry validation/defaults,
        and resolves each stage's expected outputs.
        """
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
        """
        Convert prepared graph nodes into nf-core-ready compiled nodes.

        Each compiled node stores the process alias, module path, input/output
        channel names, output accessor, and rendered `ext.args` values needed for
        Nextflow generation.

        """
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
        """
        Generate the Nextflow param.input list from input FASTQ paths.
        """
        lines = ['params.input = [']
        lines.extend(f'    "{path}",' for path in input_files)
        if input_files:
            lines[-1] = lines[-1].rstrip(',')
        lines.append(']')
        return '\n'.join(lines)

    def generate_input_channel_str(self) -> str:
        """
        Generate the Nextflow input channel for FASTQ reads.

        The generated channel groups files by sample ID and detects whether a
        sample is single-end or paired-end based on R1/R2 FASTQ filename patterns.
        """
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
            '                tuple(meta, r1s + r2s)\n'
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