import sys
[sys.path.append(i) for i in ['.', '..']] # Tells Pyhton to search for modules in the parent directories.

from shared.graph import Graph, Node
from backend.tool_registry import ToolRegistry
from backend.tools.fastqc import fastqc_tool
from backend.tools.trimmomatic import trimmomatic_tool
from backend.tools.base import apply_defaults
from abc import ABC, abstractmethod
import os
import shlex

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
        command_string = " ".join(shlex.quote(part) for part in command)
            
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

    def generate_pipeline(self, graph) -> str:
        """
        Generate the Nextflow pipeline script as a string.
        """

        pipeline_script = "nextflow.enable.dsl=2\n\n"

        workflow_header = "workflow {\n"
        workflow_body = ""

        current_channel = None  # tracks output of previous step

        for node_num, node in graph.nodes.items():
            # Input node
            if node.tool == "input":
                input_path = node.outputs['reads'][0]
                workflow_body += f"    read_ch = Channel.fromPath('{input_path}')\n"
                current_channel = "read_ch"
                continue

            # Generate module
            process_name, module_path = self.generate_module(node)

            # include statement
            pipeline_script += f"include {{ {process_name} }} from '{module_path}'\n"

            # create variable name for output
            output_var = f"{node.tool}_{node.node_num}_out"

            # chain execution
            workflow_body += f"    {output_var} = {process_name}({current_channel})\n"

            # update current channel
            current_channel = output_var

        workflow_body += "}\n"

        pipeline_script += "\n" + workflow_header + workflow_body

        return pipeline_script
    
if __name__ == "__main__":
    # Testing code to build and run a pipeline with the NextflowPipeline class.
    # This would normally be triggered by the "Run Pipeline" button in the UI.
    pipeline_factory = PipelineFactory()
    tool_registry = ToolRegistry()
    graph = Graph()

    node0 = graph.create_node("input")
    node0.outputs = {
        "reads": ['C:/Users/Marie Bethell/projects/bioinformatics-pipeline-capstone/data/Test01_L001_R1_001.fastq']
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

    graph.add_node(node0, prev=None, next=node1)
    graph.add_node(node1, prev=node0,next=node2)
    graph.add_node(node2, prev=node1, next=None)

    node1.inputs = {'reads': ['/data/Test01-L001_R1_001.fastq']}
    node2.inputs = {'reads': ['/data/Test01-L001_R1_001.fastq']} # use same input for testing, in reality this would be node1.outputs after resolution

    pipeline = pipeline_factory.build_pipeline("nextflow", graph, "input_folder", tool_registry, pipeline_script_path="backend/main.nf")
    pipeline.run_pipeline()