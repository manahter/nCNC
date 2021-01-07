
# from ..registerer import register_in_dir
# import os
#
#
# for module in [i.rsplit(".")[0] for i in os.listdir(os.path.dirname(__file__)) if not i.startswith("_")]:
#     try:
#         exec(f"from .{module} import *")
#     except:
#         pass
#
#
# register_in_dir(__name__)

from ..registerer import classes
from .configs.props import NCNC_PR_ObjectConfigs
from .configs.ops import NCNC_OT_ObjectConfigs
from .configs.panel import (
    NCNC_PT_ObjectConfigs,
    NCNC_PT_ToolpathConfigsDetailConverting,
    NCNC_PT_ToolpathConfigsDetailClearance
)
from .props import NCNC_PR_Objects
from .ops import NCNC_OT_Objects
from .panel import NCNC_UL_Objects, NCNC_PT_Objects

classes.extend([
    NCNC_PR_ObjectConfigs,
    NCNC_OT_ObjectConfigs,
    NCNC_UL_Objects,
    NCNC_PR_Objects,
    NCNC_OT_Objects,
    NCNC_PT_ObjectConfigs,
    NCNC_PT_ToolpathConfigsDetailConverting,
    NCNC_PT_ToolpathConfigsDetailClearance,
    NCNC_PT_Objects,
])