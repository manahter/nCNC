from bpy.types import Panel


class NCNC_PT_Connection(Panel):
    bl_idname = "NCNC_PT_connection"
    bl_label = "Connection"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_machine

    def draw(self, context):
        pr_con = context.scene.ncnc_pr_connection

        layout = self.layout
        col = layout.column()
        col.prop(pr_con, "ports", text="Port")
        col.prop(pr_con, "bauds", text="Baud")
        col.prop(pr_con, "controller")

        conn = pr_con.isconnected

        col.operator("ncnc.connection",
                     text=("Connected" if conn else "Connect"),
                     icon=("LINKED" if conn else "UNLINKED"),
                     depress=conn
                     )