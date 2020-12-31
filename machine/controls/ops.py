import bpy
from bpy.types import Operator
from bpy.props import EnumProperty


class NCNC_OT_Machine(Operator):
    bl_idname = "ncnc.machine"
    bl_label = "Machine Controls"
    bl_description = "Machine Controllers"
    bl_options = {'REGISTER'}

    action: EnumProperty(items=[
        ("bos", "", ""),
        ("reset", "Soft Reset", "Immediately halts and safely resets Grbl without a power-cycle."
                                "Accepts and executes this command at any time."),
        ("resume", "Cycle Start / Resume", "Resumes a feed hold, a safety door/parking state when the door is closed, "
                                           "and the M0 program pause states."),
        ("hold", "Feed Hold", "Places Grbl into a suspend or HOLD state. If in motion, the machine will decelerate to "
                              "a stop and then be suspended.Command executes when Grbl is in an IDLE, RUN, "
                              "or JOG state. It is otherwise ignored."),
        ("door", "Safety Door", "Although typically connected to an input pin to detect the opening of a safety door, "
                                "this command allows a GUI to enact the safety door behavior with this command."),
        ("cancel", "Jog Cancel", "Immediately cancels the current jog state by a feed hold and automatically flushing "
                                 "any remaining jog commands in the buffer. Command is ignored, if not in a JOG state "
                                 "or if jog cancel is already invoked and in-process. Grbl will return to the IDLE "
                                 "state or the DOOR state, if the safety door was detected as ajar during the "
                                 "cancel."),
        ("unlock", "Kill alarm lock", "Grbl's alarm mode is a state when something has gone critically wrong, "
                                      "such as a hard limit or an abort during a cycle, or if Grbl doesn't know its "
                                      "position. By default, if you have homing enabled and power-up the Arduino, "
                                      "Grbl enters the alarm state, because it does not know its position. The alarm "
                                      "mode will lock all G-code commands until the '$H' homing cycle has been "
                                      "performed. Or if a user needs to override the alarm lock to move their axes "
                                      "off their limit switches, for example, '$X' kill alarm lock will override the "
                                      "locks and allow G-code functions to work again."),

        ("sleep", "Sleep", "This command will place Grbl into a de-powered sleep state, shutting down the spindle, "
                           "coolant, and stepper enable pins and block any commands. It may only be exited by a "
                           "soft-reset or power-cycle. Once re-initialized, Grbl will automatically enter an ALARM "
                           "state, because it's not sure where it is due to the steppers being disabled."),
        ("run", "Run", ""),
    ])

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        pr_com = context.scene.ncnc_pr_communication
        pr_vis = context.scene.ncnc_pr_vision

        if self.action == "run":
            if not pr_vis.texts:
                self.report({'INFO'}, "No Selected Text")
                return {"CANCELLED"}
            txt = bpy.data.texts[pr_vis.texts]

            for i in txt.as_string().splitlines():
                x = i.strip()
                if not x or (x.startswith("(") and x.endswith(")")):
                    continue
                pr_com.send_in_order(x)

        elif self.action == "reset":
            pr_com.set_hardly("0x18")
            pr_com.set_hardly("$X")
            pr_com.clear_queue()

        elif self.action == "resume":
            pr_com.set_hardly("~")

        elif self.action == "hold":
            pr_com.set_hardly("!")

        elif self.action == "door":
            pr_com.set_hardly("0x84")

        elif self.action == "cancel":
            pr_com.set_hardly("0x85")

        elif self.action == "unlock":
            pr_com.set_hardly("$X")

        elif self.action == "sleep":
            pr_com.set_hardly("$SLP")

        return {'FINISHED'}
