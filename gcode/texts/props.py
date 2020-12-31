import bpy
from bpy.props import EnumProperty, PointerProperty, IntProperty
from bpy.types import PropertyGroup, Scene, Text


text_editor_files = []


class NCNC_PR_Texts(PropertyGroup):
    loading: IntProperty(
        name="Loading...",
        subtype="PERCENTAGE",
        default=0,
        min=0,
        max=100
    )

    def template_texts(self, layout, context=None):
        row = layout.row(align=True)

        # Show / Hide
        if context:
            context.scene.ncnc_pr_vision.prop_bool(row, "gcode")

        row.prop(self, "texts", text="", icon="TEXT", icon_only=True)

        if self.loading > 0:
            # row = layout.row(align=True)
            row.prop(self, "loading", slider=True)
        else:
            if self.active_text:
                row.prop(self.active_text, "name", text="")
            row.operator("ncnc.textsopen", icon="FILEBROWSER", text=("" if self.active_text else "Open"))
            if self.active_text:
                row.operator("ncnc.textsremove", icon="X", text="")
                # row.operator("ncnc.textssave", icon="EXPORT", text="")

        return row

    def texts_items(self, context):
        # The reason we used different variables in between was that we got an error when the unicode character was
        # in the file name.
        # Reference:
        # https://devtalk.blender.org/t/enumproperty-and-string-encoding/7835
        text_editor_files.clear()
        text_editor_files.extend([(i.name, i.name, "") for i in bpy.data.texts])
        return text_editor_files

    def update_texts(self, context):
        self.active_text = bpy.data.texts[self.texts]

    last_texts = []
    texts: EnumProperty(
        items=texts_items,
        name="Texts",
        description="Select CNC code text",
        update=update_texts
    )

    def update_active_text(self, context):
        if not self.active_text:
            return

        if bpy.ops.ncnc.vision.poll():
            bpy.ops.ncnc.vision()

        self.active_text.ncnc_pr_text.load()

        for area in context.screen.areas:
            if area.type == "TEXT_EDITOR":
                area.spaces[0].text = self.active_text

        context.scene.ncnc_pr_vision.gcode = context.scene.ncnc_pr_vision.gcode

    active_text: PointerProperty(
        type=Text,
        update=update_active_text
    )

    @property
    def code(self):
        return bpy.data.texts[self.texts].as_string() if self.texts else ""

    @classmethod
    def register(cls):
        Scene.ncnc_pr_texts = PointerProperty(
            name="NCNC_PR_Texts Name",
            description="NCNC_PR_Texts Description",
            type=cls)

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_texts
