from bpy.types import Panel


class NCNC_PT_Vision(Panel):
    bl_idname = "NCNC_PT_vision"
    bl_label = "Vision"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_vision

    def draw(self, context):
        # Filtreleme özelliği Ekle
        # Koddaki belli satırlar arası Filtrele
        # X Y Z aralıkları filtrele

        pr_vis = context.scene.ncnc_pr_vision
        layout = self.layout


class NCNC_PT_VisionThemes(Panel):
    bl_idname = "NCNC_PT_visionthemes"
    bl_label = "Themes"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_vision

    def draw(self, context):
        pr_vis = context.scene.ncnc_pr_vision
        layout = self.layout

        layout.prop(pr_vis, "presets", text="Presets")

        overlay = context.space_data.overlay

        split = layout.split(factor=.53)
        split.label(text="Show Axes")

        row = split.row(align=True)
        row.prop(overlay, "show_axis_x", text="X", toggle=True)
        row.prop(overlay, "show_axis_y", text="Y", toggle=True)
        row.prop(overlay, "show_axis_z", text="Z", toggle=True)

        row = layout.row(heading="Show")
        row.prop(pr_vis, "infront")


class NCNC_PT_VisionThemesGcode(Panel):
    bl_label = "G Codes"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_visionthemes"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pr_vis = context.scene.ncnc_pr_vision
        layout = self.layout

        for pr, text in [("gcode", "General"),
                         ("gp", "G Points"),
                         ("g0", "G0 - Rapid"),
                         ("g1", "G1 - Linear"),
                         ("g2", "G2 - Arc (CW)"),
                         ("g3", "G3 - Arc (CCW)"),
                         ("gc", "Current Line"),
                         ]:
            pr_vis.prop_theme(layout, pr, text)

    def draw_header(self, context):
        context.scene.ncnc_pr_vision.prop_bool(self.layout, "gcode")


class NCNC_PT_VisionThemesDash(Panel):
    bl_label = "Dashboard"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_visionthemes"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pr_vis = context.scene.ncnc_pr_vision
        layout = self.layout

        for pr, text in [("dash", "General"),
                         ("status", "Status"),
                         ("feed", "Feed"),
                         ("spindle", "Spindle"),
                         ("buffer", "Buffer"),
                         ("pos", "Position"),
                         ]:
            pr_vis.prop_theme(layout, pr, text)

    def draw_header(self, context):
        context.scene.ncnc_pr_vision.prop_bool(self.layout, "dash")


class NCNC_PT_VisionThemesMill(Panel):
    bl_label = "Mill"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"
    bl_parent_id = "NCNC_PT_visionthemes"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pr_vis = context.scene.ncnc_pr_vision
        layout = self.layout

        for pr, text in [("mill", "Mill")]:
            pr_vis.prop_theme(layout, pr, text)

    def draw_header(self, context):
        context.scene.ncnc_pr_vision.prop_bool(self.layout, "mill")