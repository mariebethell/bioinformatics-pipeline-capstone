"""
Endpoints defined here
"""

from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response as RestResp

from network.server.computeServer.gateway import ComputeServer
from shared.Command import *

# Create your views here.
@api_view(['GET'])
def test(request: Request):
    return RestResp("Hello!")

# Client HTTP API
@api_view(['POST'])
def connect(request: Request):
    cmd_type = ClientConnect
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)
    
@api_view(['GET'])
def get_pipeline(request: Request):
    cmd_type = GetPipeline
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)

@api_view(['POST'])
def new_pipeline(request: Request):
    cmd_type = NewPipeline
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)

@api_view(['PUT'])
def overwrite_pipeline(request: Request):
    cmd_type = OverwritePipeline
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)
    
@api_view(['PATCH'])
def modify_pipeline_params(request: Request):
    cmd_type = ModifyPipelineParams
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)
    
@api_view(['PATCH'])
def run_pipeline(request: Request):
    cmd_type = RunPipeline
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)
    
@api_view(['PATCH'])
def stop_pipeline(request: Request):
    cmd_type = StopPipeline
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)
    
@api_view(['PATCH'])
def rerun_pipeline(request: Request):
    cmd_type = RerunStage
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)
    
@api_view(['GET'])
def get_download_uri(request: Request):
    cmd_type = GetArtifactDownload
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)


# Container HTTP API
@api_view(['PUT'])
def on_stage_complete(request: Request):
    cmd_type = OnStageComplete
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)
    
@api_view(['PUT'])
def on_pipeline_error(request: Request):
    cmd_type = OnPipelineError
    request.parser_context['cmd_type'] = cmd_type
    return ComputeServer.compute_server.ingest_datagram(cmd_type, request)