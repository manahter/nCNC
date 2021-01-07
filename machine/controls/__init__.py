from ...registerer import classes
from .props import NCNC_PR_Machine
from .ops import NCNC_OT_Machine
from .panel import (
    NCNC_PT_Machine,
    NCNC_PT_MachineDash,
    NCNC_PT_MachineModes,
    NCNC_PT_MachineDetails,
    NCNC_PT_MachineDetail,
    NCNC_PT_MachineDetailInvert,
    NCNC_PT_MachineDetailAxis,
    NCNC_PT_MachineDetailAxisInvert,
)

classes.extend([
    NCNC_PR_Machine,
    NCNC_OT_Machine,
    NCNC_PT_Machine,

    NCNC_PT_MachineDash,
    NCNC_PT_MachineModes,
    NCNC_PT_MachineDetails,
    NCNC_PT_MachineDetail,
    NCNC_PT_MachineDetailInvert,
    NCNC_PT_MachineDetailAxis,
    NCNC_PT_MachineDetailAxisInvert,
])