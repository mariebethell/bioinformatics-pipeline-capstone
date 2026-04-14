import sys
[sys.path.append(i) for i in ['.', '..']] # Tells Python to search for modules in the parent directories.

from shared.graph import Graph, Node
from backend.tool_registry import ToolRegistry
from backend.tools.fastqc import fastqc_tool
from backend.tools.trimmomatic import trimmomatic_tool
from backend.tools.base import apply_defaults
from abc import ABC, abstractmethod
import os

# Extensions have to be concatenated with the process name to form the output channel name
OUTPUT_CHANNEL_EXTS = {
    "fastqc": ".out.zip",
    "trimmomatic": ".out.trimmed_reads",
    "trinity": ".out.transcript_fasta"
}

class Pipeline(ABC):
    def __init__(self, graph: Graph, tool_registry):
        self.graph = graph
        self.registry = tool_registry

    @abstractmethod
    def run_pipeline(self):
        pass

    @abstractmethod
    def stop_pipeline(self):
        pass

class NextflowPipeline(Pipeline):
    def __init__(self, graph: Graph, tool_registry, pipeline_script_path):
        super().__init__(graph, tool_registry)
        self.pipeline_script_path = pipeline_script_path

    def run_pipeline(self):
        generator = NextflowGenerator(self.graph, self.registry)

        generator.prepare_graph()
        script = generator.generate_pipeline(self.graph)

        print("Generated pipeline:")
        print(script)
        
        with open(self.pipeline_script_path, 'w') as f:
            f.write(script)

        # TODO: Execute generated script with Nextflow (use subprocess to call nextflow run with the generated script)

    def stop_pipeline(self):
        # TODO: Write logic to stop the Nextflow pipeline
        print("Stopping Nextflow pipeline...")
        # subprocess.run(['pkill', '-f', 'nextflow'], check=True)

    def revise_stage_params(self, stage_num, param_key, new_val):
        # TODO: Write logic to revise parameters of a specific stage in the pipeline
        print(f"Revising parameters for stage {stage_num}: setting {param_key} to {new_val}")

class PipelineFactory:
    def __init__(self):
        self.pipelines = {}

    def build_pipeline(self, pipeline_type, graph, input_folder, tool_registry, **kwargs):
        if pipeline_type == "nextflow":

            return NextflowPipeline(graph, tool_registry, **kwargs)
        else:
            raise ValueError(f"Unknown pipeline type: {pipeline_type}")

class NextflowGenerator:
    def __init__(self, graph: Graph, tool_registry):
        self.graph = graph
        self.registry = tool_registry

    def _linearize_graph(self):
        ordered = []
        curr = self.graph.get_first_node()

        while curr:
            ordered.append(curr)
            curr = curr.next_node

        return ordered
    
    def prepare_graph(self):
        ordered_nodes = self._linearize_graph()

        prev_outputs = None

        for node in ordered_nodes:
            # validate using schema rules
            if (node.tool != "input"):
                errors = self.registry.validate_tool_args(node.tool, node.args)
                if errors:
                    raise Exception(f"{node.tool} validation failed: {errors}")
                
                # apply defaults
                node.args = apply_defaults(
                    node.args,
                    self.registry.get_tool_arg_schema(node.tool)
                )

                # resolve inputs
                if node.inputs is None:
                    if node.prev_node is None:
                        node.inputs = node.outputs
                    else:
                        node.inputs = prev_outputs

                # resolve outputs
                context = {
                    "stage_work_dir": f"/work/stage_{node.node_num}",
                    "output_prefix": f"sample{node.node_num}"
                }

                #import pdb; pdb.set_trace()
                node.outputs = self.registry.resolve_tool_outputs(
                    node.tool,
                    node.args,
                    context
                )

                prev_outputs = node.outputs

    def generate_stage(self, node: Node) -> str:
        """
        Generate the command string for a single stage based on the node's tool, args, inputs, and outputs.
        """
        command = self.registry.render_tool_command(
            node.tool,
            node.args,
            node.inputs,
            node.outputs
        )

        # Convert list of command parts into a single string for Nextflow
        command_string = ""
        for part in command:
            if ' ' in part:
                part = f'"{part}"'  # Quote parts with spaces
            command_string += part + " "

        return command_string.strip()
    
    def generate_module(self, node: Node) -> str:
        """
        Generate a Nextflow module for the given node. 
        Loads the module template and fills in the command and input/output definitions.

        Returns the file path of the generated module script.
        """

        template_file_path = os.path.join("backend", "templates", "module_template.nf")
        output_file_path = os.path.join("backend", "modules", f"stage_{node.node_num}_{node.tool}.nf")

        print(template_file_path)

        with open(template_file_path, 'r') as f:
            module_template = f.read()

            command = self.generate_stage(node)
            process_name = node.tool.upper()
            module_template = module_template.replace("TOOL_NAME", process_name)
            module_template = module_template.replace("COMMAND", command)
            module_template = module_template.replace("OUTPUT", node.outputs["outdir"])

            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w') as out_f:
                out_f.write(module_template)

        return process_name, output_file_path

    def generate_input_parameters(self, node: Node) -> str:
        """
        Generate the input parameters for the pipeline script based on the input node.
        """
        input_files = node.outputs["reads"]
        input_param_string = "params.input = [\n"
        input_param_string += ",\n".join([f'    "{file}"' for file in input_files])
        input_param_string += "\n]\n"
        return input_param_string

    def generate_input_channel_str(self) -> str:
        """
        Generate the input channel definition for the pipeline script based on the input node.
        """
        input_channel_string = "    reads_ch = Channel.fromPath(params.input, checkIfExists: true)\n"
        input_channel_string += """        .map { f ->
        def name = f.getName()

        def sample_id = name
            .replaceAll(/_R?1(_\d+)?\.fastq$/, '')
            .replaceAll(/_R?2(_\d+)?\.fastq$/, '')

        tuple(sample_id, f  )
        }
        .groupTuple()
        .map { sample_id, files ->

            def files_list = files.toList()

            def r1 = files_list.find { it.getName() ==~ /.*_R?1(_\d+)?\.fastq$/ }
            def r2 = files_list.find { it.getName() ==~ /.*_R?2(_\d+)?\.fastq$/ }

            def meta = [ id: sample_id ]

            if (r1 && r2) {
                tuple(meta, [ r1, r2 ])
            } else {
                tuple(meta, files_list[0])
            }
        }\n"""
        return input_channel_string
    
    def generate_output_channel_str(self, node: Node, tool_alias: str=None) -> str:
        """
        Generate the output channel definition for the pipeline script based on the node's outputs.
        """
        channel_name = "ch_" + (tool_alias.lower() if tool_alias else node.tool.lower())
        output_channel_string = f"    {channel_name} = {node.tool.upper()}{OUTPUT_CHANNEL_EXTS.get(node.tool.lower())}\n"
        if tool_alias:
            output_channel_string = f"    {channel_name} = {tool_alias}{OUTPUT_CHANNEL_EXTS.get(node.tool.lower())}\n"
        return output_channel_string

    def generate_nfcore_include_statement(self, node: Node, tool_alias : str=None) -> str:
        """
        Given a node, generate the include statement for a nf-core module.
        """
        process_name = node.tool.upper()
        module_path = f"./modules/nf-core/{node.tool}/main"
        if tool_alias:
            return f"include {{ {process_name} as {tool_alias} }} from '{module_path}'\n"

        return f"include {{ {process_name} }} from '{module_path}'\n"
    
    def generate_execution_block(self, node: Node, tool_alias: str=None) -> str:
        """
        Given a node, generate the execution block for a nf-core module.
        Assumes the module takes a single input channel called "reads_ch" and produces an output channel called "output_ch".
        """
        process_name = node.tool.upper()

        if tool_alias:
            process_name = tool_alias

        if node.prev_node.tool == "input":
            return f"    {process_name}(reads_ch)\n"
        else:
            prev_process_name = node.prev_node.tool.upper()
            output_channel_name = self.generate_output_channel_str(node.prev_node, tool_alias=prev_process_name if node.prev_node.tool != "input" else None).strip().split()[0]
            return f"    {process_name}({output_channel_name})\n"

    
    def generate_pipeline(self, graph) -> str:
        """
        Generate the Nextflow pipeline script as a string.
        """

        pipeline_script = ""
        
        tools_in_graph = {}
        for node in graph.nodes.values():
            if node.tool not in tools_in_graph:
                tools_in_graph[node.tool] = 1
            else:
                tools_in_graph[node.tool] += 1

        alias_counts = {}

        workflow_header = "nextflow.enable.dsl=2\n\n"
        workflow_body = "\nworkflow {\n\n"
        for node_num, node in graph.nodes.items():
            if node.tool == "input":
                workflow_header += self.generate_input_parameters(node) + "\n"
                workflow_body += self.generate_input_channel_str() + "\n"

            tool_alias = None
            if node.tool != "input":
                if tools_in_graph[node.tool] > 1:
                    if node.tool not in alias_counts:
                        alias_counts[node.tool] = 1
                    else:
                        alias_counts[node.tool] += 1

                    tool_alias = node.tool.upper() + str(alias_counts[node.tool])
                    workflow_header += self.generate_nfcore_include_statement(node,tool_alias)
                else:
                    workflow_header += self.generate_nfcore_include_statement(node)
                
                workflow_body += self.generate_execution_block(node, tool_alias if tools_in_graph[node.tool] > 1 else None)
                workflow_body += self.generate_output_channel_str(node, tool_alias=tool_alias if tools_in_graph[node.tool] > 1 else None) + "\n"
            
            """"
            if (node.tool == "input"):
                workflow_header = "workflow {\n"
                workflow_body += f"    read_ch = Channel.fromPath('{node.outputs['reads'][0]}')\n"
            if (node.tool != "input"):
                process_name, module_path = self.generate_module(node) 
                pipeline_script += f"include {{ {process_name} }} from '{module_path}'\n"
                
                workflow_body += f"    {process_name}(read_ch)\n"

            """

        workflow_body += "}\n"
        pipeline_script += workflow_header + workflow_body

        return pipeline_script
    
if __name__ == "__main__":
    # Testing code to build and run a pipeline with the NextflowPipeline class.
    # This would normally be triggered by the "Run Pipeline" button in the UI.
    pipeline_factory = PipelineFactory()
    tool_registry = ToolRegistry()
    graph = Graph()

    node0 = graph.create_node("input")
    node0.outputs = {
        "reads": ['../data/Test01_L001_R1_001.fastq', '../data/Test01_L001_R2_001.fastq', '../data/Test02_L001_R1_001.fastq', '../data/Test02_L001_R2_001.fastq']
    }

    node1 = graph.create_node("fastqc")
    node1.args = {'threads': 1, 'kmers': 7, 'format': 'fastq'}

    node2 = graph.create_node("trimmomatic")
    node2.args = {'threads': 1, 'mode': 'SE', 'compress_level': 1, 'steps': [
        {
            "name": "sliding_window",
            "parameters": {
                "window_size": 4,
                "required_quality": 20
            }
        }
    ]}

    node3 = graph.create_node("fastqc")
    node3.args = {'threads': 1, 'kmers': 7, 'format': 'fastq'}

    graph.add_node(node0, prev=None, next=node1)
    graph.add_node(node1, prev=node0,next=node2)
    graph.add_node(node2, prev=node0, next=node3)
    graph.add_node(node3, prev=node2, next=None)

    node1.inputs = {'reads': ['../data/Test01_L001_R1_001.fastq']} # use same input for testing, in reality this would be node0.outputs after resolution
    node2.inputs = {'reads': ['../data/Test01_L001_R1_001.fastq']} # use same input for testing, in reality this would be node1.outputs after resolution
    node3.inputs = {'reads': ['../data/Test01_L001_R1_001.fastq']} # use same input for testing, in reality this would be node2.outputs after resolution

    pipeline = pipeline_factory.build_pipeline("nextflow", graph, "input_folder", tool_registry, pipeline_script_path="backend/main.nf")
    
    pipeline.run_pipeline()