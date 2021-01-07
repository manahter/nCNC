import bpy
import time
from bpy.types import Operator
from bpy.props import EnumProperty, BoolProperty

from ..utils.modal import register_modal, unregister_modal


class NCNC_OT_Objects(Operator):
    bl_idname = "ncnc.objects"
    bl_label = "Objects Operator"
    bl_description = "for Selected Object ;\n" \
                     "( + ) : Add the object to the CNC work" \
                     "( - ) : Removing the object from CNC work\n" \
                     "(bin) : Delete object"
    bl_options = {'REGISTER', 'UNDO'}
    action: EnumProperty(name="Select Object",
                         items=[("bos", "Select", ""),
                                ("add", "Addt", ""),
                                ("remove", "Remove", ""),
                                ("delete", "Delete", ""),
                                ("up", "Up", ""),
                                ("down", "Down", "")
                                ])

    inloop = True
    delay = 0.2  # 0.5
    _last_time = 0

    start: BoolProperty(default=True)

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        props = context.scene.ncnc_pr_objects
        items = props.items
        index = props.active_item_index

        if self.action == "add":
            bpy.context.active_object.ncnc_pr_objectconfigs.included = True
            self.report({'INFO'}, "Object Added")

        elif self.action == "remove":
            bpy.context.active_object.ncnc_pr_objectconfigs.included = False
            self.report({'INFO'}, "Object Removed")

        elif self.action == "delete":
            self.report({'INFO'}, "Object Deleted")
            bpy.ops.object.delete(use_global=False, confirm=False)

        elif self.action == 'down' and index < len(items) - 1:
            items.move(index, index + 1)
            props.active_item_index += 1

        elif self.action == 'up' and index >= 1:
            items.move(index, index - 1)
            props.active_item_index -= 1

        # ########################### STANDARD
        else:
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

        props = context.scene.ncnc_pr_objects

        # Add new items
        for obj in context.scene.objects:
            if obj.ncnc_pr_objectconfigs.included:
                props.add_item(obj)

        # Remove items
        for i in props.items:
            if not i.obj or (i.obj.name not in context.scene.objects.keys()) or (
                    not i.obj.ncnc_pr_objectconfigs.included):
                props.remove_item(i.obj)
                if context.area:
                    context.area.tag_redraw()

        return {'PASS_THROUGH'}

