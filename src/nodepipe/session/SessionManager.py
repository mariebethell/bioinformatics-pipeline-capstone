from uuid import UUID
from datetime import datetime

from session.Session import Session

from shared.Command import Command, NewPipeline, OnStageComplete, OnPipelineError, Response, SendDummyWebsocketUpdate, GraphUIUpdate
from shared.CommandFactory import CommandFactory
from shared.APIStatus import APIStatus
from shared.graph import StageState, Graph

#For stub, remove when done with stub
from shared.Command import ClientConnect, ClientConnectResponse, GetPipeline, GetPipelineResponse, NewPipelineResponse, ModifyPipelineParams, ModifyPipelineParamsResponse, RunPipeline, RunPipelineResponse, StopPipeline, StopPipelineResponse, RerunStage, RerunStageResponse, GetArtifactDownload, GetArtifactDownloadResponse
from uuid import uuid4

from backend.pipeline_manager import PipelineManager

class SessionManager:
    """
    Handles mapping between users and their Pipelines
    
    """

    def __init__(self, compute_server):
        self.compute_server = compute_server
        self.user_uuid_map: dict[UUID, Session] = {} # Maps user UUID to their session
        self.pipeline_uuid_map: dict[UUID, Session] = {} # Maps pipeline UUID to it's parent session

        self.pipeline_manager = PipelineManager() # Spawn pipeline manager

    def route_pipeline_command(self, cmd: Command) -> Response:
        """
        Routes an incoming Command to a users Pipeline by looking up their Session. Useful if the user closes their client and opens it later

        Args:
            cmd (Command): The command to route

        Returns:
            A response containing the command's result or a base Response type containing an error code if the Command could not be routed

        Raises:
            TypeError if given a type other than Command
            ValueError if a Command lacks a user UUID

        """

        if not isinstance(cmd, Command):
            raise TypeError("cmd must be a Command or derivative thereof")
        
        cmd_type = type(cmd)
        print(f"DBG: cmd_type {cmd_type}")
        
        user_uuid = None
        try:
            user_uuid = cmd.user_uuid
            print(f"DBG: got user from packet {user_uuid}")

        except AttributeError:
            print("DBG: packet did not have user")
            if cmd_type is OnStageComplete or cmd_type is OnPipelineError:
                print("DBG: packet is stage update, thats why")
                user_session = self.pipeline_uuid_map.get(cmd.pipeline_id, None)

                if user_session is None:
                    # Just drop the packet, session for this pipeline no longer exists
                    print(f"WARNING: Pipeline {cmd.pipeline_id} sent an update for a session which does not exist")
                    params = {"STATUS": APIStatus.SUCCESS}
                    response = CommandFactory.new_command(Response, params)

                    return response
                
                user_uuid = user_session.user_uuid
                print(f"DBG: uuid map returned user session for user {user_uuid}")

        if user_uuid is None:
            raise ValueError("Command lacks user UUID? Dev, command is malformed OR command should have been handled in networking layer")
        
        user_session = self.user_uuid_map.get(user_uuid, None)

        if user_session is None:
            print("DBG: user session was not found")
            if cmd_type is not NewPipeline:
                print("WARNING: Client attempted to access non-existing session")
                params = {'STATUS': APIStatus.ERR_BAD_PIPELINE_ID} # User has no session and therefore no pipeline. User needs to send a NewPipeline command
                return CommandFactory.new_command(Response, params)
            
        print("DBG: got user session")
         
        if cmd_type is ClientConnect:
            # Find pipeline by user_session and return if it exists, otherwise don't include it in the response
            
            pipeline_uuid = None
            # Iterate over pipelines till we find the one corresponding to the session
            for pipeline_id, session in self.pipeline_uuid_map.items():
                if session.session_id == user_session.session_id:
                    pipeline_uuid = pipeline_id
                    break

            if pipeline_uuid:
                params = {"PIPELINE_ID": pipeline_uuid, "STATUS": APIStatus.SUCCESS}
            else:
                params = {"STATUS": APIStatus.SUCCESS}

            response = CommandFactory.new_command(ClientConnectResponse, params)

        elif cmd_type is OnStageComplete or cmd_type is OnPipelineError:
            print("DEBUG: Handling stage update from pipeline")
            async_params = {
                'PIPELINE_ID': cmd.pipeline_id,
                'UPDATES': {str(cmd.stage_num): StageState.COMPLETED if cmd_type is OnStageComplete else StageState.ERROR}
            }
            async_cmd = CommandFactory.new_command(GraphUIUpdate, async_params)
            self.send_client_update_async(cmd.pipeline_id, async_cmd)
            print("DEBUG: Handed off to async netcode")

            params = {"STATUS": APIStatus.SUCCESS}
            response = CommandFactory.new_command(Response, params)

            return response

        else:
            response = self.pipeline_manager.handlePipelineCommand(cmd)

        if cmd_type is NewPipeline:
            pipeline_uuid = response.PIPELINE_ID
            user_session = Session(user_uuid, pipeline_uuid)

            self.user_uuid_map[user_uuid] = user_session
            self.pipeline_uuid_map[pipeline_uuid] = user_session

        user_session.last_update_time = datetime.now()

        return response

        
    def send_client_update_async(self, pipeline_uuid: UUID, cmd: Command):
        """
        Sends the given command to the owner of the given pipeline over websocket connection.
            - Mostly intended for sending GraphUIUpdate commands

        Args:
            pipeline_uuid (UUID): The UUID for the pipeline which is issuing the Command
            cmd (Command): The command to send over the websocket

        Raises:
            Nothing, it will just print a warning and drop the command. This should not be used for
                state critical updates
        
        """

        user_session = self.pipeline_uuid_map.get(pipeline_uuid, None)
        
        if user_session is None:
            print("WARNING: Pipeline attempted to send update to nonexistant user session")
            return # Just drop it
            
        user_uuid = user_session.user_uuid

        self.compute_server.send_to_target_async(user_uuid, cmd)


class SessionManagerStub(SessionManager):
    """
    Temporary stub for testing until pipeline layer is ready

    """

    def route_pipeline_command(self, cmd: Command) -> Response:
        test_resp = None
        if (type(cmd) is ClientConnect):
            params = {"PIPELINE_ID": UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4'), "STATUS": APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(ClientConnectResponse, params)

        elif (type(cmd) is NewPipeline):
            test_params = {"PIPELINE_ID": UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4'), "STATUS": APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(NewPipelineResponse, test_params)

        elif (type(cmd) is GetPipeline):
            test_graph = Graph()
            n1 = test_graph.create_node("tool 1")
            n2 = test_graph.create_node("tool 2")
            n3 = test_graph.create_node("tool 3")
            test_graph.connect(n1, n2)
            test_graph.connect(n2, n3)

            test_params = {"GRAPH": test_graph, "STATUS": APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(GetPipelineResponse, test_params)

        elif (type(cmd) is SendDummyWebsocketUpdate):
            dummy_update = {"1": StageState.COMPLETED, "2": StageState.RUNNING}
            async_params = {
                'PIPELINE_ID': cmd.pipeline_id,
                'UPDATES': dummy_update
            }
            async_cmd = CommandFactory.new_command(GraphUIUpdate, async_params)

            self.compute_server.send_to_target_async(cmd.user_id, async_cmd)

            params = {'STATUS': APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(Response, params)

        elif (type(cmd) is ModifyPipelineParams):
            test_params = {'STATUS': APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(ModifyPipelineParamsResponse, test_params)

        elif (type(cmd) is RunPipeline):
            test_params = {'STATUS': APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(RunPipelineResponse, test_params)

        elif (type(cmd) is StopPipeline):
            test_params = {'STATUS': APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(StopPipelineResponse, test_params)

        elif (type(cmd) is RerunStage):
            test_params = {'STATUS': APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(RerunStageResponse, test_params)

        elif (type(cmd) is GetArtifactDownload):
            test_params = {"URI": 'some/dir/relative/to/bindmount', "STATUS": APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(GetArtifactDownloadResponse, test_params)


        if test_resp is None:
            params = {'STATUS': APIStatus.ERR_UNKNOWN}
            test_resp = CommandFactory.new_command(Response, params)

        return test_resp
        