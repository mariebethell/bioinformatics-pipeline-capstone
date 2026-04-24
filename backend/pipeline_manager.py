"""
Receive and handle pipeline commands from the Session Manager (client -> server)
Sends commands to Session Manager (server -> client)

Commands received and handled by this class:
- GetPipeline: Retrieves graph information for a given pipeline ID.
- NewPipeline: Creates a Nextflow pipeline object from the provided graph and input folder.
- OverwritePipeline: Overwrites an existing pipeline (keeps the uid the same).
- ModifyPipelineParams: Updates a specific node in an existing pipeline.
- RunPipeline: Generates and executes a Nextflow script for a pipeline object.
- StopPipeline: Stops a running pipeline script.
- RerunStage: Reruns a specific stage of a pipeline.

Commands sent by this class to client:
- OnStageComplete: Notifies the client that a pipeline stage has completed.
- OnPipelineError: Contains error information that indicates what stage a pipeline failed and the type of error.
"""

from session import session_manager # Use singleton (netcode-v3 branch)
from shared import Command
from shared import APIStatus
from shared.graph import Graph, Node
from pipeline_builder import NextflowPipeline

class PipelineManager:
    def __init__(self):
        self.session_manager = session_manager # Use singleton (netcode-v3 branch)
        self.pipelines = dict[str, NextflowPipeline] # pipeline_id -> pipeline object

    def handlePipelineCommand(self, cmd:Command.Command):
        """
        Handles commands received from the client.
        """
        if isinstance(cmd, Command.ClientConnect):
            # will change to getactivepipelineid or something similar
            pass

        elif isinstance(cmd, Command.GetPipeline):
            pipeline = self.pipelines.get(cmd.pipeline_id)

            if pipeline is None:
                # Send error response to client - no pipeline with given ID
                self.session_manager.sendCommand(Command.GetPipelineResponse(ERROR_INFO=APIStatus.ERR_BAD_PIPELINE_ID))
            else:
                # Send pipeline graph info to client
                self.session_manager.sendCommand(Command.GetPipelineResponse(graph=pipeline.graph))

        elif isinstance(cmd, Command.NewPipeline):
            pipeline_uid = self.newPipeline(cmd.graph)

            # Send new pipeline response to client with pipeline ID
            self.session_manager.sendCommand(Command.NewPipelineResponse(PIPELINE_ID=pipeline_uid))
        
        elif isinstance(cmd, Command.OverwritePipeline):
            pipeline = self.pipelines.get(cmd.pipeline_id)

            existing_id = None
            if pipeline:
                pipeline.stop_pipeline()
                existing_id = pipeline.uid
            
            pipeline = NextflowPipeline(graph=cmd.graph, uid=existing_id) # Preserve pipeline ID for overwrite. If id was none initially, a new one will have been created by NextflowPipeline constructor.

            self.pipelines[pipeline.uid] = pipeline

            self.session_manager.sendCommand(Command.OverwritePipelineResponse(PIPELINE_ID=pipeline.uid))

        elif isinstance(cmd, Command.ModifyPipelineParams):
            pipeline = self.pipelines.get(cmd.pipeline_id)
            if pipeline is None:
                self.session_manager.sendCommand(Command.ModifyPipelineParamsResponse(ERROR_INFO=APIStatus.ERR_BAD_PIPELINE_ID))
            else:
                node = pipeline.graph.get_node(cmd.node_num)
                node.args = cmd.new_args
                pipeline.graph.nodes[cmd.node_num] = node

                self.session_manager.sendCommand(Command.ModifyPipelineParamsResponse())

        elif isinstance(cmd, Command.RunPipeline):
            pipeline = self.pipelines.get(cmd.pipeline_id)
            if pipeline is None:
                self.session_manager.sendCommand(Command.RunPipelineResponse(ERROR_INFO=APIStatus.ERR_BAD_PIPELINE_ID))
            else:
                pipeline.run_pipeline()
                self.session_manager.sendCommand(Command.RunPipelineResponse())

        elif isinstance(cmd, Command.StopPipeline):
            pipeline = self.pipelines.get(cmd.pipeline_id)
            if pipeline is None:
                self.session_manager.sendCommand(Command.StopPipelineResponse(ERROR_INFO=APIStatus.ERR_BAD_PIPELINE_ID))
            else:
                pipeline.stop_pipeline()
                self.session_manager.sendCommand(Command.StopPipelineResponse())

        elif isinstance(cmd, Command.RerunStage):
            # nothing here for now since we don't have a way to rerun a stage yet.
            self.session_manager.sendCommand(Command.RerunStageResponse())
            pass

        elif isinstance(cmd, Command.GetArtifactDownload):
            # return path to bindmount (not implemented)
            self.session_manager.sendCommand(Command.GetArtifactDownloadResponse(URI="/path/to/bindmount"))
            pass

    def newPipeline(self, graph: Graph) -> str:
        pipeline = NextflowPipeline(graph)
        self.pipelines[pipeline.uid] = pipeline

        return pipeline.uid
    
    def deletePipeline(self, pipelineUUID: str):
        if pipelineUUID in self.pipelines:
            del self.pipelines[pipelineUUID]