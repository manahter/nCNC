from .texts import *
from .text import *

from .create import NCNC_PR_GCodeCreate, NCNC_OT_GCodeCreate
from .convert import NCNC_OT_GCodeConvert

from nCNC.registerer import classes

classes.extend([
    NCNC_PR_GCodeCreate,
    NCNC_OT_GCodeCreate,
    NCNC_OT_GCodeConvert
])
