# session_states.py
from enum import Enum, auto

class S(Enum):
    INTRO                = auto()
    POCKETS_Q            = auto()
    CONFESSION_PROMPT    = auto()
    CONFESS              = auto()
    POST_CONF_PROMPT     = auto()
    INFO_RECORD          = auto()
    READY_PROMPT         = auto()
    END                  = auto() 