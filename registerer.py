from bpy.types import Panel, PropertyGroup, Operator, UIList, AddonPreferences
from bpy_extras.io_utils import ImportHelper, ExportHelper
import inspect
import nCNC
import sys

register_types = (Panel, PropertyGroup, Operator, UIList, AddonPreferences, ImportHelper, ExportHelper)

classes = []


def register_in_dir(module_name):
    """module_name: __name__"""
    for name, obj in inspect.getmembers(sys.modules[module_name]):
        if name.startswith("NCNC") and \
                inspect.isclass(obj) and issubclass(obj, register_types) and not isinstance(obj, register_types):
            classes.append(obj)


def register_class(class_obj):
    classes.append(class_obj)