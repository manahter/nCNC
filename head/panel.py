from datetime import timedelta
from bpy.types import Panel


class NCNC_PT_Head(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = ""
    bl_idname = "NCNC_PT_head"

    def draw(self, context):
        pr_txs = context.scene.ncnc_pr_texts
        pr_con = context.scene.ncnc_pr_connection
        pr_com = context.scene.ncnc_pr_communication

        layout = self.layout
        layout.template_running_jobs()
        pr_txs.template_texts(layout, context=context)

        if pr_con.isconnected:
            row = layout.row()
            if pr_com.run_mode == "stop":
                row.operator("ncnc.communicationrun", icon="PLAY", text="Start").action = "start"
            elif pr_com.run_mode == "pause":
                row.operator("ncnc.communicationrun", icon="PLAY", text="Resume").action = "resume"
                row.operator("ncnc.communicationrun", icon="SNAP_FACE", text="Stop").action = "stop"
            else:
                row.operator("ncnc.communicationrun", icon="PAUSE", text="Pause").action = "pause"
                row.operator("ncnc.communicationrun", icon="SNAP_FACE", text="Stop").action = "stop"

    def draw_header(self, context):
        prop = context.scene.ncnc_pr_head

        row = self.layout.row(align=True)
        row.prop(prop, "tool_scene", text="", expand=True, icon="TOOL_SETTINGS")

        row.separator(factor=1)

        row.prop(prop, "tool_gcode", text="", expand=True, icon="COLOR_GREEN")
        row.prop(prop, "tool_machine", text="", expand=True, icon="PLUGIN")

    def draw_header_preset(self, context):
        self.layout.prop(context.scene.ncnc_pr_head, "tool_vision", text="", expand=True, icon="CAMERA_STEREO")


class NCNC_PT_HeadTextDetails(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "GCode Details"
    bl_idname = "NCNC_PT_filedetails"
    bl_parent_id = "NCNC_PT_head"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_texts.active_text

    def draw(self, context):
        pr_txs = context.scene.ncnc_pr_texts
        if not pr_txs.active_text:
            return
        pr_txt = pr_txs.active_text.ncnc_pr_text

        layout = self.layout

        row = layout.row(align=True)
        col1 = row.column()
        col1.alignment = "RIGHT"
        col1.label(text="Distance to Travel")
        col1.label(text="Estimated Time")
        col1.label(text="Total Line")
        for i in range(3):
            col1.label(text=f"{round(pr_txt.minimum[i], 1)} || {round(pr_txt.maximum[i], 1)}")

        col2 = row.column(align=False)
        col2.label(text=f"{int(pr_txt.distance_to_travel)} mm")
        col2.label(text=f"{timedelta(seconds=int(pr_txt.estimated_time))}")
        col2.label(text=f"{pr_txt.count}")
        for i in "XYZ":
            col2.label(text=i)

        row = layout.row()
        row.operator("ncnc.textssave", icon="EXPORT", text="Export")
