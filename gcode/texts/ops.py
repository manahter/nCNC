import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


class NCNC_OT_TextsOpen(Operator, ImportHelper):
    bl_idname = "ncnc.textsopen"
    bl_label = "Open GCode Text"
    bl_description = "Import a GCode file"
    bl_options = {'REGISTER'}

    # References:
    # https://docs.blender.org/api/current/bpy_extras.io_utils.html
    # https://sinestesia.co/blog/tutorials/using-blenders-filebrowser-with-python/
    # https://blender.stackexchange.com/questions/177742/how-do-i-create-a-text-datablock-and-populate-it-with-text-with-python

    filter_glob: StringProperty(
        default='*.text;*.txt;*.cnc;*.nc;*.tap;*.ngc;*.gc;*.gcode;*.ncnc;*.ncc',
        options={'HIDDEN'}
    )

    def execute(self, context):
        with open(self.filepath, 'r') as f:
            txt = bpy.data.texts.new(os.path.basename(self.filepath))
            txt.write(f.read())
            if context.scene.ncnc_pr_texts.texts_items:
                context.scene.ncnc_pr_texts.texts = txt.name

        return {'FINISHED'}


class NCNC_OT_TextsSave(Operator, ExportHelper):
    bl_idname = "ncnc.textssave"
    bl_label = "Export to GCode"
    bl_description = "Export a GCode file"
    bl_options = {'REGISTER'}

    # References:
    # https://docs.blender.org/api/current/bpy_extras.io_utils.html
    # https://blender.stackexchange.com/questions/150932/export-file-dialog-in-blender-2-80

    filter_glob: StringProperty(
        default='*.text;*.txt;*.cnc;*.nc;*.tap;*.ngc;*.gc;*.gcode;*.ncnc;*.ncc',
        options={'HIDDEN'}
    )
    filename_ext = ".cnc"

    def execute(self, context):
        active = context.scene.ncnc_pr_texts.active_text

        if active:
            text = active.as_string()
            with open(self.filepath, "wb") as f:
                f.write(text.encode("ASCII"))

            self.report({"INFO"}, "Exported")

        return {'FINISHED'}


class NCNC_OT_TextsRemove(Operator):
    bl_idname = "ncnc.textsremove"
    bl_label = "Remove Text File"
    bl_description = "Remove selected Text File"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        txt = context.scene.ncnc_pr_texts.active_text
        if txt:
            bpy.data.texts.remove(txt)
        return {"FINISHED"}
