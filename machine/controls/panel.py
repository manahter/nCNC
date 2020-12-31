from bpy.types import Panel


class NCNC_PT_Machine(Panel):
    bl_idname = "NCNC_PT_machine"
    bl_label = "Machine"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_machine

    def draw(self, context):
        layout = self.layout

        if not context.scene.ncnc_pr_connection.isconnected:
            layout.enabled = False

        status = context.scene.ncnc_pr_machine.status

        row = layout.row()
        row.alert = status.startswith("ALARM") or status in ("HOLD:0", "SLEEP", "DOOR:0")
        row.operator("ncnc.machine", text="Reset", icon="FILE_REFRESH", ).action = "reset"
        row.alert = status in ("ALARM:3")
        row.operator("ncnc.machine", text="Unlock", icon="UNLOCKED", ).action = "unlock"
        row = layout.row()
        row.operator("ncnc.machine", text="Hold!", icon="PAUSE", ).action = "hold"

        row.alert = status in ("HOLD:0", "HOLD:1", "DOOR:0")
        row.operator("ncnc.machine", text="Resume", icon="PLAY", ).action = "resume"

        row = layout.row()
        row.operator("ncnc.machine", text="Sleep", icon="SORTTIME", ).action = "sleep"
        row.operator("ncnc.machine", text="Door", icon="ARMATURE_DATA", ).action = "door"

    def draw_header(self, context):
        status = context.scene.ncnc_pr_machine.status
        if status.startswith("ALARM") or status in ("HOLD:0", "SLEEP", "DOOR:0"):
            self.layout.operator("ncnc.machine", text="", icon="FILE_REFRESH", ).action = "reset"


class NCNC_PT_MachineDash(Panel):
    bl_idname = "NCNC_PT_machinedash"
    bl_label = "Dashboard"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_machine"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        props = context.scene.ncnc_pr_machine

        layout = self.layout

        if not context.scene.ncnc_pr_connection.isconnected:
            layout.enabled = False

        # STATUS
        row = layout.row()
        row.alert = True
        row.operator("ncnc.empty", text=f"{props.status}")

        col = layout.column(align=True)

        # POS MODE
        row = col.row(align=True)
        row.prop(props, "pos_type", expand=True, )
        row.scale_y = 0.8

        pos = props.mpos if props.pos_type == "mpos" else props.wpos

        # POS LABEL
        row = col.row(align=True)
        row.alert = True
        row.operator("ncnc.empty", text="X", depress=True)  # emboss=True,
        row.operator("ncnc.empty", text="Y", depress=True)  # emboss=True,
        row.operator("ncnc.empty", text="Z", depress=True)  # emboss=True,

        # POS
        row = layout.row(align=True)
        row.operator("ncnc.empty", text=f"{round(pos[0], 2)}", emboss=False)  # , depress=True
        row.operator("ncnc.empty", text=f"{round(pos[1], 2)}", emboss=False)  # , depress=True
        row.operator("ncnc.empty", text=f"{round(pos[2], 2)}", emboss=False)  # , depress=True

        # SPLIT
        row = layout.split()

        # LABELS
        row = layout.row(align=True)
        row.alert = True
        row.operator("ncnc.empty", text="Feed", depress=True)  # emboss=False,
        row.operator("ncnc.empty", text="Spindle", depress=True)  # emboss=False,
        row.operator("ncnc.empty", text="Buffer", depress=True)  # emboss=False,
        row.enabled = True

        # VALS
        row = layout.row(align=True)
        row.operator("ncnc.empty", text=f"{props.feed}", emboss=False)
        row.operator("ncnc.empty", text=f"{props.spindle}", emboss=False)
        row.operator("ncnc.empty", text=f"{props.buffer},{props.bufwer}", emboss=False)

    def draw_header(self, context):
        context.scene.ncnc_pr_vision.prop_bool(self.layout, "dash")


class NCNC_PT_MachineModes(Panel):
    bl_idname = "NCNC_PT_machinemodes"
    bl_label = "Modes"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_machine"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        props = context.scene.ncnc_pr_machine

        layout = self.layout

        if not context.scene.ncnc_pr_connection.isconnected:
            layout.enabled = False

        row = layout.row(heading="Motion Mode")
        row.prop(props, "motion_mode", text="")

        row = layout.row(heading="Coordinate System")
        row.prop(props, "coordinate_system", text="")

        row = layout.row(heading="Distance Mode")
        row.prop(props, "distance_mode", text="")

        row = layout.row(heading="Plane")
        row.prop(props, "plane", text="")

        row = layout.row(heading="Feed Rate Mode")
        row.prop(props, "feed_rate_mode", text="")

        row = layout.row(heading="Units Mode")
        row.prop(props, "units_mode", text="")

        row = layout.row(heading="Spindle State")
        row.prop(props, "spindle_state", text="")

        row = layout.row(heading="Coolant State")
        row.prop(props, "coolant_state", text="")

        row = layout.row(heading="Saved Feed")
        row.prop(props, "saved_feed", text="")
        # row.enabled = False

        row = layout.row(heading="Saved Spindle")
        row.prop(props, "saved_spindle", text="")
        # row.enabled = False

        # row = layout.row(heading="Cutter Radius Compensation")
        # row.prop(props, "cutter_radius_compensation", text="")

        # row = layout.row(heading="Arc Distance")
        # row.prop(props, "arc_ijk_distance", text="")

        # row = layout.row(heading="Tool Length Offset")
        # row.prop(props, "tool_length_offset", text="")

        # row = layout.row(heading="Program Mode")
        # row.prop(props, "program_mode", text="")


class NCNC_PT_MachineDetails(Panel):
    bl_idname = "NCNC_PT_machinedetails"
    bl_label = "Configs"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_machine"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass


class NCNC_PT_MachineDetail(Panel):
    bl_label = "Detail"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_machinedetails"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        props = context.scene.ncnc_pr_machine

        layout = self.layout

        if not context.scene.ncnc_pr_connection.isconnected:
            layout.enabled = False

        row = layout.row(heading="Motion Mode")
        row.prop(props, "motion_mode", text="")

        # ### Numeric
        col = layout.column(align=True)
        col.prop(props, "s0")
        col.prop(props, "s1")
        col.prop(props, "s11")
        col.prop(props, "s12")
        col.prop(props, "s24")
        col.prop(props, "s25")
        col.prop(props, "s26")
        col.prop(props, "s27")
        col.prop(props, "s30")
        col.prop(props, "s31")


class NCNC_PT_MachineDetailInvert(Panel):
    bl_label = "Detail: Invert"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_machinedetails"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        props = context.scene.ncnc_pr_machine

        layout = self.layout
        if not context.scene.ncnc_pr_connection.isconnected:
            layout.enabled = False

        col = layout.column(align=False)
        col.alignment = "RIGHT"
        col.prop(props, "s4")
        col.prop(props, "s5")
        col.prop(props, "s6")
        col.prop(props, "s20")
        col.prop(props, "s21")
        col.prop(props, "s22")
        col.prop(props, "s32")


class NCNC_PT_MachineDetailAxis(Panel):
    bl_label = "Detail: Invert Axis"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_machinedetails"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        props = context.scene.ncnc_pr_machine

        layout = self.layout

        if not context.scene.ncnc_pr_connection.isconnected:
            layout.enabled = False

        # row = layout.column(align=False)
        """
        row = layout.row(align=False)
        col = row.column()
        col.prop(props, "s2")
        col = row.column()
        col.prop(props, "s3")
        col = row.column()
        col.prop(props, "s23")"""

        col = layout.column(align=False)

        col.label(text="Step Port Invert:")
        row = col.row()
        row.prop(props, "s2", text="")

        col.label(text="Direction Port Invert:")
        row = col.row()
        row.prop(props, "s3", text="")

        col.label(text="Homing Dir Invert:")
        row = col.row()
        row.prop(props, "s23", text="")


class NCNC_PT_MachineDetailAxisInvert(Panel):
    bl_label = "Detail: Axis"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_machinedetails"
    bl_options = {'DEFAULT_CLOSED'}  # DEFAULT_CLOSED

    def draw(self, context):
        props = context.scene.ncnc_pr_machine

        layout = self.layout
        if not context.scene.ncnc_pr_connection.isconnected:
            layout.enabled = False
            # return

        col = layout.column(align=True, heading="Axis Travel Resolution (step/mm)")
        col.prop(props, "s100")
        col.prop(props, "s101")
        col.prop(props, "s102")

        col = layout.column(align=True, heading="Axis Maximum Rate (mm/min)")
        col.prop(props, "s110")
        col.prop(props, "s111")
        col.prop(props, "s112")

        col = layout.column(align=True, heading="Axis Acceleration (mm/sec^2)")
        col.prop(props, "s120")
        col.prop(props, "s121")
        col.prop(props, "s122")

        col = layout.column(align=True, heading="Axis Maximum Travel (mm)")
        col.prop(props, "s130")
        col.prop(props, "s131")
        col.prop(props, "s132")
