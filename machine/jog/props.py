from bpy.props import IntProperty, BoolProperty, FloatProperty, PointerProperty
from bpy.types import PropertyGroup, Scene


class NCNC_PR_JogController(PropertyGroup):
    def update_spindle_speed(self, context):
        pr_com = context.scene.ncnc_pr_communication
        pr_com.send_in_order(f"S{self.spindle_speed}")

    def update_spindle_state(self, context):
        pr_com = context.scene.ncnc_pr_communication
        pr_mac = context.scene.ncnc_pr_machine
        if pr_mac.spindle_state not in ("M3", "M4"):
            pr_com.send_in_order(f"M3 S{self.spindle_speed}")

        else:
            pr_com.send_in_order(f"M5")

    # Auto Update On/Off BUTTON
    step_size_xy: FloatProperty(
        name="Step Size XY",
        step=200,
        default=10.000
    )
    step_size_z: FloatProperty(
        name="Step Size Z",
        step=100,
        default=1.0
    )
    feed_rate: IntProperty(
        name="Feed",
        step=50,
        default=500,
        description="Feed Rate"
    )
    spindle_speed: IntProperty(
        name="Spindle",
        default=1000,
        step=200,
        min=0,
        max=75000,
        description="Current Speed",
        update=update_spindle_speed
    )
    spindle_state: BoolProperty(
        name="Spindle On/Off",
        default=False,
        description="Start / Stop",
        update=update_spindle_state
    )

    @classmethod
    def register(cls):
        Scene.ncnc_pr_jogcontroller = PointerProperty(
            name="NCNC_PR_JogController Name",
            description="NCNC_PR_JogController Description",
            type=cls)

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_jogcontroller
