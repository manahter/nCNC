from nCNC.registerer import register_in_dir
import os


for module in [i.rsplit(".")[0] for i in os.listdir(os.path.dirname(__file__)) if not i.startswith("_")]:
    try:
        exec(f"from .{module} import *")
    except:
        pass


register_in_dir(__name__)