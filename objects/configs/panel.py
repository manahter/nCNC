from bpy.types import Panel

from ...assets.icons import icons


class NCNC_PT_ObjectConfigs(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "Object Configs"
    bl_idname = "NCNC_PT_objectconfigs"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_gcode

    def draw(self, context):

        obj = context.active_object

        layout = self.layout

        if not obj:
            col = layout.column()
            col.label(text="No object selected", icon="MATCUBE")
            for i in range(7):
                col.label()
            return

        props = obj.ncnc_pr_objectconfigs

        row = layout.row(align=True)
        row.prop(props, "included", text="", icon="CHECKBOX_HLT" if props.included else "CHECKBOX_DEHLT")
        row.enabled = props.check_for_include(obj)
        row.prop(obj, "name", text="")

        isok = props.check_for_include(obj)
        tip_egri = obj.type in ("CURVE", "FONT")
        if isok:
            # if tip_egri:
            a = row.split()
            a.prop(props, "as_line",
                   icon="IPO_CONSTANT" if props.as_line else "IPO_EASE_IN_OUT",
                   icon_only=True,
                   emboss=False
                   )
            row.prop(props, "milling_strategy", icon_only=True)

        # if not props.check_for_include(obj):
        #    row.operator("ncnc.toolpathconfigs", text="", icon="CURVE_DATA")

        row = layout.row(align=True)
        if not isok:
            row.operator("ncnc.toolpathconfigs", text="Convert to Curve", icon="CURVE_DATA")
        else:
            row.enabled = props.included  # Tip uygun değilse buraları pasif yapar
            row.prop(props, "plane", expand=True)
            row.enabled = False

        col = layout.column(align=True)
        col.enabled = props.included  # Tip uygun değilse buraları pasif yapar
        col.prop(props, "safe_z")
        col.prop(props, "step")
        if tip_egri:
            col.prop(props, "depth")
        else:
            col.label()

        col = layout.column(align=True)
        col.enabled = props.included  # Tip uygun değilse buraları pasif yapar
        col.prop(props, "feed")
        col.prop(props, "plunge")
        col.prop(props, "spindle")


class NCNC_PT_ToolpathConfigsDetailConverting(Panel):
    # bl_idname = "NCNC_PT_tconfigsdetailconverting"
    bl_label = "Detail: Converting"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_objectconfigs"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        obj = context.active_object
        if not obj:
            return

        props = obj.ncnc_pr_objectconfigs

        if not props.check_for_include(obj):
            return

        layout = self.layout
        col = layout.column(align=True)
        col.enabled = props.included  # Tip uygun değilse buraları pasif yapar
        col.prop(props, "round_circ", slider=True)
        col.prop(props, "round_loca", slider=True)

        col = layout.column(align=True)
        col.enabled = props.included  # Tip uygun değilse buraları pasif yapar
        if obj.type == "CURVE":

            col.prop(props, "resolution_general", slider=True, text="Resolution Curve (General)")
            if obj.data.splines.active:
                col.prop(props, "resolution_spline", slider=True, text="Resolution Spline (in Curve)")


class NCNC_PT_ToolpathConfigsDetailClearance(Panel):
    bl_label = "Detail: Clearance"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_objectconfigs"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        obj = context.active_object
        if not obj:
            return

        props = obj.ncnc_pr_objectconfigs

        if not props.check_for_include(obj):
            return

        layout = self.layout
        col = layout.column(align=True)
        col.enabled = props.included  # Tip uygun değilse buraları pasif yapar

        col = layout.column(align=True)
        col.enabled = props.included  # Tip uygun değilse buraları pasif yapar
        col.prop(props, "carving_range")
        col.prop(props, "carving_angle")
