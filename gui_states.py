from enum import Enum
class GuiStates(Enum):
    INIT        = 0
    READY       = 1
    CONNECTING  = 2
    CONNECTED   = 3
    ERROR       = 4
