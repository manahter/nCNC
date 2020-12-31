# Serial Connecting Machine
_dev = []

def dev_set(value):
    global _dev
    _dev.append(value)


def dev_get():
    if _dev:
        return _dev[-1]
    return None
# ##########################

from .connection import *
from .communication import *
from .controls import *
from .jog import *






