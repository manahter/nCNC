import bpy
from bpy.types import Operator


class NCNC_OT_ObjectConfigs(Operator):
    bl_idname = "ncnc.toolpathconfigs"
    bl_label = "Convert to Curve"
    bl_description = "Convert to curve for CNC machining"
    bl_options = {'REGISTER'}

    def execute(self, context):
        return self.invoke(context)

    def invoke(self, context, event=None):
        obj = context.active_object
        obj.select_set(True)
        objAyar = obj.ncnc_pr_objectconfigs

        if not obj:
            self.report({'WARNING'}, "No Object Selected")
            return {"FINISHED"}

        # Convert if not suitable
        if obj.type not in ('CURVE', 'FONT'):
            bpy.ops.object.convert(target='CURVE')

        # Cancel if still not suitable
        if obj.type not in ('CURVE', 'FONT'):
            self.report({'WARNING'}, f"Cannot convert to curve : {obj.name}")
            return {"CANCELLED"}

        # TODO: NURBS için de geliştir.
        # Curve ok, if not Bezier or Poly
        if not objAyar.check_for_include(obj):
            self.report({'INFO'}, f"Not the desired type : {obj.name}")
            return {"FINISHED"}

        # Include in the mill.
        objAyar.included = True

        # if "nCurve" not in obj.name:
        #     obj.name = "nCurve." + obj.name

        self.report({'INFO'}, f"Included in the mill: {obj.name}")

        return {"FINISHED"}

