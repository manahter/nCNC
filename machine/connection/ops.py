import bpy
from bpy.types import Operator


class NCNC_OT_Connection(Operator):
    bl_idname = "ncnc.connection"
    bl_label = "Connection"
    bl_description = "Connect / Disconnect"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        pr_con = context.scene.ncnc_pr_connection
        pr_con.isconnected = not pr_con.isconnected

        context.scene.ncnc_pr_vision.dash = pr_con.isconnected
        context.scene.ncnc_pr_vision.mill = pr_con.isconnected

        # Start communication when connected
        # bpy.ops.ncnc.communication(start=pr_con.isconnected)

        bpy.ops.ncnc.decoder(start=pr_con.isconnected)

        return {'FINISHED'}
