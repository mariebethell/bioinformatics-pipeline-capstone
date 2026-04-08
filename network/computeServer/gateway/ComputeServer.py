from rest_framework.response import Response

from . import LocalPolicy

class ComputeServer:
    def __init__(self):
        self.filter = LocalPolicy.LocalPolicy()
    
    def ingest_datagram(self, cmdType, request):
        print(f"INFO: Packet ingested")
        if not self.filter.allow_inbound_datagram(request): return Response("Bad source IP")
        return Response("NYI")
        #TODO - deserialize based upon type, forward to next layer
        #raise NotImplementedError()
        
    def send_to_target_async(self, IP, port, cmd):
        raise NotImplementedError()
        
    def serve_file(self, cmd):
        raise NotImplementedError()
        
compute_server = ComputeServer() # Singleton