# from nCNC.registerer import register_in_dir
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

from nCNC.registerer import classes
from .props import NCNC_PR_Lines, NCNC_PR_TextLine, NCNC_PR_Text
from .ops import NCNC_OT_Text

classes.extend([
    NCNC_PR_Lines,
    NCNC_PR_TextLine,
    NCNC_PR_Text,
    NCNC_OT_Text,
])