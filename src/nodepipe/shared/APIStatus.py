from enum import Enum

class APIStatus(Enum):
    SUCCESS                     = 0
    ERR_DATAGRAM_REJECTED       = 2**22
    ERR_INVALID_GRAPH           = 2**23
    ERR_INVALID_TOOL            = 2**24
    ERR_INVALID_ARTIFACT        = 2**25
    ERR_IMMUTABLE_ATTRIBUTE     = 2**26
    ERR_OVERWRITE_REJECTED      = 2**27
    ERR_BAD_PIPELINE_ID         = 2**28
    ERR_BAD_TIMESTAMP           = 2**29
    ERR_BAD_JSON                = 2**30
    ERR_UNKNOWN                 = 2**31