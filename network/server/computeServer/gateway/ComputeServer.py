from rest_framework.response import Response as RestResp
from rest_framework.request import Request
from typing import Type

from network.server.computeServer.gateway.LocalPolicy import LocalPolicy
from network.server.computeServer.gateway.DatagramTools import DatagramTools

from shared.Command import Command, Response
from shared.CommandFactory import CommandFactory
from shared.APIStatus import APIStatus

from session.SessionManager import SessionManager
from session.SessionManager import SessionManagerStub #TODO remove after testing


class ComputeServer:
    """
    Ingests incoming Commands from Django and services them

    """

    def __init__(self):
        self.filter = LocalPolicy()
        self.session_manager = SessionManagerStub() #TODO change to real class when ready
    
    def ingest_datagram(self, cmd_type: Type[Command], request: Request):
        """
        Entry point for incoming server Commands. Filters and forwards whichever is allowed onto the session layer, returns Responses over the network

        Args:
            cmd_type (Type where type refers to a Command or derived class): The expected Command type, determined by which endpoint the Command arrived on
            request (Request): The incoming network Request to filter and pull the Command out of

        Raises:
            TypeError: If supplied command is not a Command or if there is a mismatch between expected and actual Command types

        """

        print("INFO: Packet ingested")

        if not self.filter.allow_inbound_datagram(request):
            params = {'STATUS': APIStatus.ERR_DATAGRAM_REJECTED}
            rej_resp = CommandFactory.new_command(Response, params)
            rej_json = CommandFactory.serialize_command(rej_resp)
            return RestResp(rej_json)
        
        if not issubclass(cmd_type, Command):
            raise TypeError("Given type is not a Command derivative")

        cmd = request.data # Parser should have automatically made the Command for us

        if not issubclass(type(cmd), Command):
            raise TypeError(f"Parser produced a non Command object (type: {type(cmd)})")
        
        if type(cmd) is not cmd_type:
            raise TypeError(f"Actual command type does not match expected command type. Expected {cmd_type}, got {type(cmd)}")
        
        # Inject source IP into command for use later
        cmd.source = DatagramTools.extract_ip(request)

        # Forward to session layer
        cmd_result = self.session_manager.route_pipeline_command(cmd)
        result_json = CommandFactory.serialize_command(cmd_result)
        return RestResp(result_json)

        
    def send_to_target_async(self, IP, port, cmd):
        raise NotImplementedError()
        
    def serve_file(self, cmd):
        raise NotImplementedError()

        
compute_server = ComputeServer() # Singleton