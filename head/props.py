import bpy
from bpy.types import Scene, PropertyGroup
from bpy.props import BoolProperty, PointerProperty


class NCNC_PR_Head(PropertyGroup):
    def update_common(self, context, key):
        keys = ["scene", "gcode", "machine", "vision"]
        keys.remove(key)
        for key in keys:
            exec(f"self.tool_{key} = False")

        # Apply Scene Settings
        bpy.ops.ncnc.scene()

        pr_vis = context.scene.ncnc_pr_vision

        # Load recent settings for pr_vis
        pref = bpy.context.preferences.addons.get(__name__)
        if pref and pref.preferences.last_preset:
            pr_vis.presets = pref.preferences.last_preset

        pr_vis.gcode = pr_vis.gcode
        pr_vis.dash = pr_vis.dash
        pr_vis.mill = pr_vis.mill

    def update_tool_scene(self, context):
        if self.tool_scene:
            self.update_common(context, "scene")

    def update_tool_machine(self, context):
        if self.tool_machine:
            self.update_common(context, "machine")

    def update_tool_vision(self, context):
        if self.tool_vision:
            self.update_common(context, "vision")

    def update_tool_gcode(self, context):
        if self.tool_gcode:
            self.update_common(context, "gcode")

            # Track Included Objects
            bpy.ops.ncnc.objects(start=True)
        # else:
        #    # Cancel Track
        #    bpy.ops.ncnc.objects(start=False)

    tool_scene: BoolProperty(
        name="Scene Tools",
        description="Show/Hide regions",
        default=True,
        update=update_tool_scene
    )
    tool_machine: BoolProperty(
        name="Machine Tools",
        description="Show/Hide regions",
        default=False,
        update=update_tool_machine
    )
    tool_gcode: BoolProperty(
        name="G-code Generation Tools",
        description="Show/Hide regions",
        default=False,
        update=update_tool_gcode
    )
    tool_vision: BoolProperty(
        name="Vision Tools",
        description="Show/Hide regions",
        default=False,
        update=update_tool_vision
    )

    @classmethod
    def register(cls):
        Scene.ncnc_pr_head = PointerProperty(
            name="NCNC_PR_Head Name",
            description="NCNC_PR_Head Description",
            type=cls
        )

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_head
