from uuid import UUID
from datetime import datetime

from session.Session import Session

from network.server.computeServer.gateway.ComputeServer import ComputeServer, compute_server

from shared.Command import Command, NewPipeline, Response
from shared.CommandFactory import CommandFactory
from shared.APIStatus import APIStatus

#For stub, remove when done with stub
from shared.Command import ClientConnect, ClientConnectResponse, NewPipelineResponse
from uuid import uuid4


class SessionManager:
    """
    Handles mapping between users and their Pipelines
    
    """

    def __init__(self):
        self.user_uuid_map: dict[UUID, Session] = {} # Maps user UUID to their session
        self.pipeline_uuid_map: dict[UUID, Session] = {} # Maps pipeline UUID to it's parent session

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
        
        #TODO call PipelineManager
        #TODO if cmd was NewPipeline make a new session, add to user_uuid_map and pipeline_uuid_map
        raise NotImplementedError
        
    def send_client_update_async(self, pipeline_uuid, cmd: Command):
        user_uuid = self.pipeline_uuid_map.get(pipeline_uuid, None)
        
        if user_uuid is None:
            print("WARNING: Pipeline attempted to send update to nonexistant user session")
            return # Just drop it
            
        compute_server.send_to_target_async(user_uuid, cmd)


class SessionManagerStub(SessionManager):
    """
    Temporary stub until pipeline layer is ready

    """
    def route_pipeline_command(self, cmd: Command) -> Response:
        test_resp = None
        if (type(cmd) is ClientConnect):
            params = {"PIPELINE_ID": uuid4(), "STATUS": APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(ClientConnectResponse, params)

        elif (type(cmd) is NewPipeline):
            test_params = {"PIPELINE_ID": uuid4(), "STATUS": APIStatus.SUCCESS}
            test_resp = CommandFactory.new_command(NewPipelineResponse, test_params)


        if test_resp is None:
            params = {'STATUS': APIStatus.ERR_UNKNOWN}
            test_resp = CommandFactory.new_command(Response, params)

        return test_resp
        

session_manager = SessionManager() # Singleton