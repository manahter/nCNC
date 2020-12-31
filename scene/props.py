from bpy.props import BoolProperty, PointerProperty
from bpy.types import PropertyGroup, Scene
import bpy


class NCNC_PR_Scene(PropertyGroup):
    def set_mm(self, val):
        unit = bpy.context.scene.unit_settings
        if unit.system != 'METRIC':
            unit.system = 'METRIC'

        if unit.length_unit != 'MILLIMETERS':
            unit.length_unit = 'MILLIMETERS'

    def get_mm(self):
        return bpy.context.scene.unit_settings.length_unit == 'MILLIMETERS'

    mm: BoolProperty(
        name="Milimeters",
        set=set_mm,
        get=get_mm
    )

    def set_inc(self, val):
        unit = bpy.context.scene.unit_settings
        if unit.system != 'IMPERIAL':
            unit.system = 'IMPERIAL'

        if unit.length_unit != 'INCHES':
            unit.length_unit = 'INCHES'

    def get_inc(self):
        return bpy.context.scene.unit_settings.length_unit == 'INCHES'

    inc: BoolProperty(
        name="Inches",
        set=set_inc,
        get=get_inc
    )

    @classmethod
    def register(cls):
        Scene.ncnc_pr_scene = PointerProperty(
            name="NCNC_PR_Head Name",
            description="NCNC_PR_Head Description",
            type=cls
        )

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_scene
