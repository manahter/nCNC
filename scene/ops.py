from bpy.types import Operator
from bpy.props import BoolProperty
import bpy


class NCNC_OT_Scene(Operator):
    bl_idname = "ncnc.scene"
    bl_label = "NCNC Scene Settings"
    bl_description = "New: Deletes the objects and renewed the workspace\n" \
                     "Mod: Adjust scene settings for nCNC"
    bl_options = {'REGISTER', 'UNDO'}

    newscene: BoolProperty(
        name="New Scene",
        description="Deletes the objects and renewed the workspace",
        default=False
    )

    settings: BoolProperty(
        name="Apply nCNC Scene Settings",
        description="Adjust scene settings",
        default=True
    )

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event=None):

        # Aktif obje Edit moddaysa, obje moduna çeviriyoruz ki işlem yapabilelim
        if context.active_object and context.active_object.mode == "EDIT":
            bpy.ops.object.editmode_toggle()

        if self.newscene:
            for i in bpy.data.objects:
                i.ncnc_pr_objectconfigs.included = False
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False, confirm=False)
            bpy.ops.curve.primitive_bezier_curve_add(radius=20, enter_editmode=False, location=(0, 0, 0))
            bpy.ops.view3d.view_all(center=True)
            context.active_object.ncnc_pr_objectconfigs.included = True
            bpy.ops.ncnc.gcode_create()
            self.report({'INFO'}, "Workspace has been renewed for nCNC")

            bpy.context.space_data.overlay.show_extra_edge_length = True

            bpy.ops.view3d.view_axis(type="TOP")
            self.report({'INFO'}, "Applied to nCNC Settings")

        if self.settings:
            unit = context.scene.unit_settings
            spce = context.space_data
            prop = context.scene.ncnc_pr_scene

            if prop.inc:
                prop.inc = True
            else:
                prop.mm = True

            if unit.scale_length != 0.001:
                unit.scale_length = 0.001

            if spce.overlay.grid_scale != 0.001:
                spce.overlay.grid_scale = 0.001

            if spce.clip_end != 10000:
                spce.clip_end = 10000

        self.newscene = False
        return {"FINISHED"}
