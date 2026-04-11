from rest_framework.response import Response as RestResp
from rest_framework.request import Request
from typing import Type

from network.computeServer.gateway.LocalPolicy import LocalPolicy
from shared.Command import Command
from network.computeServer.gateway.DatagramTools import DatagramTools

from shared import CommandFactory


class ComputeServer:
    def __init__(self):
        self.filter = LocalPolicy()
    
    def ingest_datagram(self, cmd_type: Type[Command.Command], request: Request):
        print("INFO: Packet ingested")

        if not self.filter.allow_inbound_datagram(request):
            return RestResp("Bad source IP")
        
        if not issubclass(cmd_type, Command):
            raise TypeError("Given type is not a Command derivative")

        cmd = request.data # Parser should have automatically made the Command for us

        if not issubclass(type(cmd), Command):
            raise TypeError("Parser produced a non Command object")
        
        # Inject source IP into command for use later
        cmd.source = DatagramTools.extract_ip(request)
        
        #TODO call route_pipeline_command in SessionManager once SessionManager is created
        
        return RestResp(f"Command processed. Contents: {CommandFactory.CommandFactory.serialize_command(cmd)}")

        
    def send_to_target_async(self, IP, port, cmd):
        raise NotImplementedError()
        
    def serve_file(self, cmd):
        raise NotImplementedError()
        
compute_server = ComputeServer() # Singleton