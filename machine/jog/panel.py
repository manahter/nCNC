from bpy.types import Panel


class NCNC_PT_JogController(Panel):
    bl_idname = "NCNC_PT_jogcontroller"
    bl_label = "Jog"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_machine

    def draw(self, context):
        if not context.scene.ncnc_pr_connection.isconnected:
            self.layout.enabled = False

        pr_jog = context.scene.ncnc_pr_jogcontroller
        layout = self.layout

        row_jog = layout.row(align=True)
        row_jog.scale_y = 1.8
        col = row_jog.column(align=True)
        col.operator("ncnc.jogcontroller", text="", icon="DOT").action = "x-y+"
        col.operator("ncnc.jogcontroller", text="", icon="TRIA_LEFT").action = "x-"
        col.operator("ncnc.jogcontroller", text="", icon="DOT").action = "x-y-"
        zero = col.split()
        zero.operator("ncnc.jogcontroller", text="X:0").action = "0x"
        zero.scale_y = 0.5

        col = row_jog.column(align=True)
        col.operator("ncnc.jogcontroller", text="", icon="TRIA_UP").action = "y+"
        col.operator("ncnc.jogcontroller", text="", icon="RADIOBUT_ON").action = "x0y0"  # SNAP_FACE_CENTER
        col.operator("ncnc.jogcontroller", text="", icon="TRIA_DOWN").action = "y-"
        zero = col.split()
        zero.operator("ncnc.jogcontroller", text="Y:0").action = "0y"
        zero.scale_y = 0.5

        col = row_jog.column(align=True)
        col.operator("ncnc.jogcontroller", text="", icon="DOT").action = "x+y+"
        col.operator("ncnc.jogcontroller", text="", icon="TRIA_RIGHT").action = "x+"
        col.operator("ncnc.jogcontroller", text="", icon="DOT").action = "x+y-"
        zero = col.split()
        zero.operator("ncnc.jogcontroller", text="XY:0").action = "0xy"
        zero.scale_y = 0.5

        col = row_jog.column(align=True)
        col.label(icon="BLANK1")
        col.operator("ncnc.jogcontroller", text="", icon="CON_OBJECTSOLVER").action = "mousepos"

        col = row_jog.column(align=True)
        col.operator("ncnc.jogcontroller", text="", icon="TRIA_UP").action = "z+"
        col.operator("ncnc.jogcontroller", text="", icon="RADIOBUT_ON").action = "z0"
        col.operator("ncnc.jogcontroller", text="", icon="TRIA_DOWN").action = "z-"
        zero = col.split()
        zero.operator("ncnc.jogcontroller", text="Z:0").action = "0z"
        zero.scale_y = 0.5

        row_conf = layout.row(align=True)

        col = row_conf.column(align=True)
        col.prop(pr_jog, "step_size_xy", icon="AXIS_TOP")
        col.prop(pr_jog, "step_size_z", icon="EMPTY_SINGLE_ARROW", )
        col.prop(pr_jog, "feed_rate", icon="CON_TRACKTO")
        col.prop(pr_jog, "spindle_speed", icon="CON_TRACKTO")

        col = row_conf.column(align=True)
        col.operator("ncnc.jogcontroller", text="", icon="HOME").action = "home"
        col.operator("ncnc.jogcontroller", text="", icon="EMPTY_SINGLE_ARROW").action = "safez"
        if context.scene.ncnc_pr_machine.status == "JOG":
            col.operator("ncnc.jogcontroller", text="", icon="CANCEL").action = "cancel"
        else:
            col.label(icon="BLANK1")

        pr_mac = context.scene.ncnc_pr_machine
        col.alert = pr_mac.spindle_state != "M5"
        col.prop(pr_jog, "spindle_state", icon="DISC", icon_only=True,
                 invert_checkbox=pr_jog.spindle_state or col.alert)

    def draw_header(self, context):
        context.scene.ncnc_pr_vision.prop_bool(self.layout, "mill")

        if context.scene.ncnc_pr_machine.status == "JOG":
            self.layout.operator("ncnc.jogcontroller", text="", icon="CANCEL").action = "cancel"
