import uuid
import inspect
import ipaddress

from datetime import datetime
from typing import Annotated, get_args
from dataclasses import dataclass

from shared import graph
from shared import APIStatus

"""
For future devs adding new commands - type annotations are REQUIRED for the serialization system to work properly. Each field MUST have an annotation or they will be ignored by the serializer
    First index of the annotation object should be the field's type, second field should be a Nullable class which defines if the field is allowed to be None/null

"""

###########################################################
# COMMANDS
###########################################################

# Metaclass for defining what command fields are allowed to be None
class Nullable:
    def __init__(self, is_nullable: bool):
        self.is_nullable = is_nullable

@dataclass
class Command:
    timestamp: Annotated[datetime, Nullable(False)] = None # Unfortunately = None has to be there on every field to prevent Python from forcing each param to be set immediately
    source: Annotated[ipaddress.IPv4Address | ipaddress.IPv6Address, Nullable(True)] = None # Must be nullable because IP address is injected by networking layer upon receipt

    def validate(self):
        polymorphs = self.__class__.__mro__[:-1] # Get tuple of self's type and all ancestors types. Last element is always object, which is cut off

        for desc_type in polymorphs:
            for field, annotation in inspect.get_annotations(desc_type).items():
                annotations = get_args(annotation)
                field_nullable = next((md for md in annotations if type(md) is Nullable), None)
                if (field_nullable is None): 
                    raise TypeError(f"Command of type {type(self)} is missing nullable annotations!")

                # Check if all fields are present in the obj, or if not are the missing ones allowed to be missing
                if not hasattr(self, field) and not field_nullable.is_nullable:
                    print(f"Command {type(self)} failed validation due to missing non-nullable field: {field}")
                    return False
                
                if getattr(self, field) is None and not field_nullable.is_nullable:
                    print(f"Command {type(self)} failed validation due to None value in non-nullable field {field}")
                    return False
        
        return True

@dataclass
class Response(Command):
    STATUS: Annotated["APIStatus.APIStatus", Nullable(False)] = None

###########################################################
# CLIENT API DATA
###########################################################

@dataclass
class ClientConnect(Command):
    user_uuid: Annotated[uuid.UUID, Nullable(False)] = None

@dataclass
class ClientConnectResponse(Response):
    ACTIVE_PIPELINE_UUID: Annotated[uuid.UUID, Nullable(True)] = None

@dataclass
class GetPipeline(Command):
    user_uuid: Annotated[uuid.UUID, Nullable(False)] = None
    pipeline_id: Annotated[uuid.UUID, Nullable(True)] = None

@dataclass
class GetPipelineResponse(Response):
    GRAPH: Annotated["graph.Graph", Nullable(True)] = None

@dataclass
class NewPipeline(Command):
    user_uuid: Annotated[uuid.UUID, Nullable(False)] = None
    input_uri: Annotated[str, Nullable(False)] = None
    graph: Annotated["graph.Graph", Nullable(False)] = None

@dataclass
class NewPipelineResponse(Response):
    PIPELINE_ID: Annotated[uuid.UUID, Nullable(False)] = None
    ERROR_INFO: Annotated["APIStatus.APIStatus", Nullable(True)] = None

@dataclass
class OverwritePipeline(NewPipeline):
    pass
    # Difference is in semantics, not syntax

@dataclass
class OverwritePipelineResponse(NewPipelineResponse):
    pass
    # Difference is in semantics, not syntax

@dataclass
class ModifyPipelineParams(Command):
    user_uuid: Annotated[uuid.UUID, Nullable(False)] = None
    pipeline_id: Annotated[uuid.UUID, Nullable(False)] = None
    node_num: Annotated[int, Nullable(False)] = None
    new_args: Annotated[dict, Nullable(False)] = None

@dataclass
class ModifyPipelineParamsResponse(Response):
    pass
    # Difference is in semantics, not syntax

@dataclass
class RunPipeline(Command):
    user_uuid: Annotated[uuid.UUID, Nullable(False)] = None
    pipeline_id: Annotated[uuid.UUID, Nullable(False)] = None

@dataclass
class RunPipelineResponse(Response):
    ERROR_INFO: Annotated["APIStatus.APIStatus", Nullable(True)] = None

@dataclass
class StopPipeline(Command):
    user_uuid: Annotated[uuid.UUID, Nullable(False)] = None
    pipeline_id: Annotated[uuid.UUID, Nullable(False)] = None

@dataclass
class StopPipelineResponse(Response):
    pass
    # Difference is in semantics, not syntax

@dataclass
class RerunStage(Command):
    user_uuid: Annotated[uuid.UUID, Nullable(False)] = None
    pipeline_id: Annotated[uuid.UUID, Nullable(False)] = None
    node_num: Annotated[int, Nullable(False)] = None

@dataclass
class RerunStageResponse(Response):
    pass
    # Difference is in semantics, not syntax

@dataclass
class GetArtifactDownload(Command):
    user_uuid: Annotated[uuid.UUID, Nullable(False)] = None
    pipeline_id: Annotated[uuid.UUID, Nullable(False)] = None
    node_num: Annotated[int, Nullable(False)] = None

@dataclass
class GetArtifactDownloadResponse(Response):
    URI: Annotated[str, Nullable(True)] = None


###########################################################
# ASYNC SOCKET DATA
###########################################################

@dataclass
class WebsocketConnectResponse(Response):
    pass
    # Difference is in semantics, not syntax

@dataclass
class GraphUIUpdate(Command):
    PIPELINE_ID: Annotated[uuid.UUID, Nullable(False)] = None
    UPDATES: Annotated[dict[int, "graph.StageState"], Nullable(False)] = None


###########################################################
# CONTAINER DATA
###########################################################

@dataclass
class OnStageComplete(Command):
    pipeline_id: Annotated[uuid.UUID, Nullable(False)] = None
    stage_num: Annotated[int, Nullable(False)] = None

@dataclass
class OnPipelineError(Command):
    pipeline_id: Annotated[uuid.UUID, Nullable(False)] = None
    stage_num: Annotated[int, Nullable(False)] = None
    error: Annotated["APIStatus.APIStatus", Nullable(False)] = None
    
###########################################################
# DEBUG COMMANDS
###########################################################

@dataclass
class SendDummyWebsocketUpdate(Response):
    pipeline_id: Annotated[uuid.UUID, Nullable(False)] = None