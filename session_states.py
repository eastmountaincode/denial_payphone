# session_states.py
from enum import Enum, auto

class S(Enum):
    INTRO                         = auto()
    POCKETS_Q                     = auto()
    CONFESSION_INQUIRY            = auto()
    CONFESSION_RECORD             = auto()
    CONFESSION_RECORD_AND_TRANSCRIBE = auto()
    POST_CONFESSION_INFO_REQUEST  = auto()
    POST_CONFESSION_INFO_RECORD   = auto()
    READY_TO_GO_INQUIRY           = auto()
    END                           = auto() 