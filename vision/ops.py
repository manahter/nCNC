import time
from bpy.types import Operator
from bpy.props import BoolProperty
from ..utils.modal import register_modal, unregister_modal


class NCNC_OT_Vision(Operator):
    bl_idname = "ncnc.vision"
    bl_label = "Update View"
    bl_description = "Update View"
    bl_options = {'REGISTER'}

    inloop = True
    delay = 0.1
    _last_time = 0

    start: BoolProperty(default=True)

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        # ########################### STANDARD
        if not self.start:
            unregister_modal(self)
            return {'CANCELLED'}
        register_modal(self)
        context.window_manager.modal_handler_add(self)
        # ####################################
        # ####################################

        return self.timer_add(context)

    def timer_add(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(self.delay, window=context.window)
        return {"RUNNING_MODAL"}

    def timer_remove(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {'CANCELLED'}

    def modal(self, context, event):
        # ########################### STANDARD
        if not self.inloop:
            if context.area:
                context.area.tag_redraw()
            return self.timer_remove(context)

        if time.time() - self._last_time < self.delay:
            return {'PASS_THROUGH'}

        self._last_time = time.time()
        # ####################################
        # ####################################

        pr_act = context.scene.ncnc_pr_texts.active_text
        if not pr_act:
            return {'PASS_THROUGH'}

        pr_txt = pr_act.ncnc_pr_text

        pr_txt.event_control()
        if pr_txt.event or pr_txt.event_selected:
            for area in context.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()

        return {'PASS_THROUGH'}
