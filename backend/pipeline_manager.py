"""
Receive and handle pipeline commands from the Session Manager (client -> server)
Sends commands to Session Manager (server -> client)

Commands received and handled by this class:
- GetPipeline: Retrieves graph information for a given pipeline ID.
- NewPipeline: Creates a Nextflow pipeline object from the provided graph and input folder.
- OverwritePipeline: Overwrites an existing pipeline (keeps the uuid the same).
- ModifyPipelineParams: Updates a specific node in an existing pipeline.
- RunPipeline: Generates and executes a Nextflow script for a pipeline object.
- StopPipeline: Stops a running pipeline script.
- RerunStage: Reruns a specific stage of a pipeline.

Commands sent by this class to client:
- OnStageComplete: Notifies the client that a pipeline stage has completed.
- OnPipelineError: Contains error information that indicates what stage a pipeline failed and the type of error.
"""

from shared import Command, APIStatus
from shared.CommandFactory import CommandFactory
from shared.graph import Graph, Node
from backend.pipeline_builder import NextflowPipeline
from backend.tool_registry import ToolRegistry
from uuid import UUID

class PipelineManager:
    def __init__(self):
        self.pipelines: dict[UUID, NextflowPipeline] = {} # pipeline_id -> pipeline object
        self.tool_registry = ToolRegistry()

    def handlePipelineCommand(self, cmd:Command.Command):
        """
        Handles commands received from the client.
        """
        print("Entered handlePipelineCommand")

        if isinstance(cmd, Command.GetPipeline):
            pipeline = self.pipelines.get(cmd.pipeline_id)

            if pipeline is None:
                # Return error response - no pipeline with given ID
                params = {"ERROR_INFO": APIStatus.APIStatus.ERR_BAD_PIPELINE_ID, "STATUS": APIStatus.APIStatus.ERR_BAD_PIPELINE_ID}
                return CommandFactory.new_command(Command.GetPipelineResponse, params)
            else:
                # Return pipeline graph info
                params = {"GRAPH": pipeline.graph, "STATUS": APIStatus.APIStatus.SUCCESS}
                return CommandFactory.new_command(Command.GetPipelineResponse, params)

        elif isinstance(cmd, Command.NewPipeline):
            pipeline_uuid = self.newPipeline(cmd.graph)

            print(pipeline_uuid)
            # Return new pipeline response with pipeline ID
            params = {"PIPELINE_ID": pipeline_uuid, "STATUS": APIStatus.APIStatus.SUCCESS}
            return CommandFactory.new_command(Command.NewPipelineResponse, params)
        
        elif isinstance(cmd, Command.OverwritePipeline):
            pipeline = self.pipelines.get(cmd.pipeline_id)

            existing_id = None
            if pipeline:
                pipeline.stop_pipeline()
                existing_id = pipeline.uuid
            
            pipeline = NextflowPipeline(graph=cmd.graph, tool_registry=self.tool_registry, uuid=existing_id) # Preserve pipeline ID for overwrite. If id was none initially, a new one will have been created by NextflowPipeline constructor.

            self.pipelines[pipeline.uuid] = pipeline

            params = {"PIPELINE_ID": pipeline.uuid, "STATUS": APIStatus.APIStatus.SUCCESS}
            return CommandFactory.new_command(Command.OverwritePipelineResponse, params)

        elif isinstance(cmd, Command.ModifyPipelineParams):
            pipeline = self.pipelines.get(cmd.pipeline_id)
            if pipeline is None:
                params = {"ERROR_INFO": APIStatus.APIStatus.ERR_BAD_PIPELINE_ID, "STATUS": APIStatus.APIStatus.ERR_BAD_PIPELINE_ID}
                return CommandFactory.new_command(Command.ModifyPipelineParamsResponse, params)
            else:
                node = pipeline.graph.get_node(cmd.node_num)
                node.args = cmd.new_args
                pipeline.graph.nodes[cmd.node_num] = node

                params = {"STATUS": APIStatus.APIStatus.SUCCESS}
                return CommandFactory.new_command(Command.ModifyPipelineParamsResponse, params)

        elif isinstance(cmd, Command.RunPipeline):
            pipeline = self.pipelines.get(cmd.pipeline_id)
            if pipeline is None:
                params = {"ERROR_INFO": APIStatus.APIStatus.ERR_BAD_PIPELINE_ID, "STATUS": APIStatus.APIStatus.SUCCESS}
                return CommandFactory.new_command(Command.RunPipelineResponse, params)
            else:
                pipeline.run_pipeline()
                params = {"STATUS": APIStatus.APIStatus.SUCCESS}
                return CommandFactory.new_command(Command.RunPipelineResponse, params)

        elif isinstance(cmd, Command.StopPipeline):
            pipeline = self.pipelines.get(cmd.pipeline_id)
            if pipeline is None:
                params = {"ERROR_INFO": APIStatus.APIStatus.ERR_BAD_PIPELINE_ID, "STATUS": APIStatus.APIStatus.ERR_BAD_PIPELINE_ID}
                return CommandFactory.new_command(Command.StopPipelineResponse, params)
            else:
                pipeline.stop_pipeline()
                params = {"STATUS": APIStatus.APIStatus.SUCCESS}
                return CommandFactory.new_command(Command.StopPipelineResponse, params)

        elif isinstance(cmd, Command.RerunStage):
            # nothing here for now since we don't have a way to rerun a stage yet.
            params = {"STATUS": APIStatus.APIStatus.SUCCESS}
            return CommandFactory.new_command(Command.RerunStageResponse)

        elif isinstance(cmd, Command.GetArtifactDownload):
            # return path to bindmount (not implemented)

            # Only return relative path to file in bindmount
            # Client will combine this with the environment variable set by installer
            # Nextflow needs to output files to bindmount
            params = {"URI": "path/to/bindmount", "STATUS": APIStatus.APIStatus.SUCCESS} 
            return CommandFactory.new_command(Command.GetArtifactDownloadResponse, params)

    def newPipeline(self, graph: Graph) -> str:
        pipeline = NextflowPipeline(graph=graph, tool_registry=self.tool_registry)
        self.pipelines[pipeline.uuid] = pipeline

        return pipeline.uuid
    
    def deletePipeline(self, pipelineUUID: str):
        if pipelineUUID in self.pipelines:
            del self.pipelines[pipelineUUID]

if __name__ == '__main__':
    print("test")