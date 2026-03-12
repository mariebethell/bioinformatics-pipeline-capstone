"""
Endpoints defined here
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .gateway import ComputeServer

# Create your views here.
@api_view(['GET'])
def test(request):
    return Response("Hello!")

# Client HTTP API
@api_view(['POST'])
def connect(request):
    return Response("NYI")
    
@api_view(['GET'])
def get_pipeline(request):
    return Response("NYI")

@api_view(['POST'])
def new_pipeline(request):
    return Response("NYI")

@api_view(['PUT'])
def overwrite_pipeline(request):
    return Response("NYI")
    
@api_view(['PATCH'])
def modify_pipeline_params(request):
    return Response("NYI")
    
@api_view(['PATCH'])
def run_pipeline(request):
    #TODO - Implement type map
    cmdType = None
    return ComputeServer.compute_server.ingest_datagram(cmdType, request)
    #return Response("NYI")
    
@api_view(['PATCH'])
def stop_pipeline(request):
    return Response("NYI")
    
@api_view(['PATCH'])
def rerun_pipeline(request):
    return Response("NYI")
    
@api_view(['GET'])
def get_download_uri(request):
    return Response("NYI")


# Container HTTP API
@api_view(['PUT'])
def on_stage_complete(request):
    return Response("NYI")
    
@api_view(['PUT'])
def on_pipeline_error(request):
    return Response("NYI")