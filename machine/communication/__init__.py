from nCNC.registerer import classes
from .ops import NCNC_OT_Communication, NCNC_OT_CommunicationRun, NCNC_OP_Messages, NCNC_OT_Decoder
from .props import NCNC_PR_MessageItem, NCNC_PR_Communication
from .panel import NCNC_UL_Messages, NCNC_PT_Communication

classes.extend([
    NCNC_OT_Decoder,
    NCNC_PR_MessageItem,
    NCNC_PR_Communication,
    NCNC_OT_CommunicationRun,
    NCNC_OT_Communication,
    NCNC_UL_Messages,
    NCNC_OP_Messages,
    NCNC_PT_Communication]
)
