from uuid import UUID
from datetime import datetime

from session.Session import Session

from shared.Command import Command, NewPipeline, Response, SendDummyWebsocketUpdate, GraphUIUpdate
from shared.CommandFactory import CommandFactory
from shared.APIStatus import APIStatus
from shared.graph import StageState

#For stub, remove when done with stub
from shared.Command import ClientConnect, ClientConnectResponse, NewPipelineResponse
from uuid import uuid4


class SessionManager:
    """
    Handles mapping between users and their Pipelines
    
    """

    def __init__(self, compute_server):
        self.compute_server = compute_server
        self.user_uuid_map: dict[UUID, Session] = {} # Maps user UUID to their session
        self.pipeline_uuid_map: dict[UUID, Session] = {} # Maps pipeline UUID to it's parent session

        #self.pipeline_manager = TODO spawn pipeline manager here when ready

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

        if cmd is not Command:
            raise TypeError("cmd must be a Command or derivative thereof")
        
        user_uuid = None
        try:
            user_uuid = cmd.user_uuid

        except AttributeError:
            raise ValueError("Command lacks user UUID? Dev, command is malformed OR command should have been handled in networking layer")
        
        user_session = self.user_uuid_map.get(user_uuid, None)

        if user_session is None:
            if cmd is not NewPipeline:
                params = {'STATUS': APIStatus.ERR_BAD_PIPELINE_ID} # User has no session and therefore no pipeline. User needs to send a NewPipeline command
                return CommandFactory.new_command(Response, params)
            
        user_session.last_update_time = datetime.now()
        
        # self.pipeline_manager.handle_pipeline_command(cmd) TODO call PipelineManager when it is ready
        #TODO if cmd was NewPipeline make a new session, add to user_uuid_map and pipeline_uuid_map
        raise NotImplementedError
        
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

        user_uuid = self.pipeline_uuid_map.get(pipeline_uuid, None)
        
        if user_uuid is None:
            print("WARNING: Pipeline attempted to send update to nonexistant user session")
            return # Just drop it
            
        self.compute_server.send_to_target_async(user_uuid, cmd)


class SessionManagerStub(SessionManager):
    """
    Temporary stub for testing until pipeline layer is ready

    """

    def route_pipeline_command(self, cmd: Command) -> Response:
        test_resp = None
        if (type(cmd) is ClientConnect):
            params = {"PIPELINE_ID": uuid4(), "STATUS": APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(ClientConnectResponse, params)

        elif (type(cmd) is NewPipeline):
            test_params = {"PIPELINE_ID": uuid4(), "STATUS": APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(NewPipelineResponse, test_params)

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



        if test_resp is None:
            params = {'STATUS': APIStatus.ERR_UNKNOWN}
            test_resp = CommandFactory.new_command(Response, params)

        return test_resp
        