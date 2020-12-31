from bpy.types import Panel


class NCNC_PT_Scene(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "Scene"
    bl_idname = "NCNC_PT_scene"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_scene

    def draw(self, context):
        pr_scn = context.scene.ncnc_pr_scene

        row = self.layout.row(align=True)
        col1 = row.column()
        col1.alignment = "RIGHT"
        col1.label(text="Scene")
        col1.label(text="")
        col1.label(text="Units")

        col1.scale_x = 1

        col2 = row.column(align=False)
        col2.operator("ncnc.scene", text="New", icon="FILE_NEW").newscene = True
        col2.operator("ncnc.scene", text="Apply", icon="SETTINGS").settings = True  # "OPTIONS"
        col2.prop(pr_scn, "mm", text="Milimeters")
        col2.prop(pr_scn, "inc", text="Inches")

