from bpy.props import (
    IntProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    StringProperty,
    PointerProperty,
    FloatVectorProperty,
    BoolVectorProperty
)
from bpy.types import PropertyGroup, Scene


class NCNC_PR_Machine(PropertyGroup):
    # ################################################ ?
    status: StringProperty(name="Status")
    """IDLE, JOG, RUN, ALARM:0.., HOLD:0.., DOOR:0..,"""

    wco: FloatVectorProperty(
        name="WCO",
        subtype='XYZ',
        default=[0.0, 0.0, 0.0]
    )

    def wpos_update(self, context):
        if self.pos_type == "mpos":
            for i in range(3):
                self.mpos[i] = self.wpos[i] + self.wco[i]

    # Workspace Position
    wpos: FloatVectorProperty(
        name="WPos",
        subtype='XYZ',
        update=wpos_update,
        default=[0.0, 0.0, 0.0]
    )

    def mpos_update(self, context):
        if self.pos_type == "wpos":
            for i in range(3):
                self.wpos[i] = self.mpos[i] - self.wco[i]

    # Machine Position
    mpos: FloatVectorProperty(
        name="MPos",
        subtype='XYZ',
        update=mpos_update,
        default=[0.0, 0.0, 0.0],
    )
    feed: FloatProperty(
        name="Feed",
        default=0,
        precision=1,
        description="Feed Rate (Current)"
    )
    spindle: FloatProperty(
        name="Spindle",
        default=0,
        precision=1,
        description="Spindle (Current)"
    )
    saved_feed: FloatProperty(
        name="&Feed",
        default=0,
        precision=1,
        description="Feed Rate (Saved) - Only read"
    )
    saved_spindle: FloatProperty(
        name="Saved Spindle",
        default=0,
        precision=1,
        description="Spindle (Saved) - Only read"
    )

    buffer: IntProperty(
        name="Buffer",
        default=15,
        description="""Buffer State:

    Bf:15,128. The first value is the number of available blocks in the planner buffer and the second is number of available bytes in the serial RX buffer.

    The usage of this data is generally for debugging an interface, but is known to be used to control some GUI-specific tasks. While this is disabled by default, GUIs should expect this data field to appear, but they may ignore it, if desired.

    NOTE: The buffer state values changed from showing "in-use" blocks or bytes to "available". This change does not require the GUI knowing how many block/bytes Grbl has been compiled with.

    This data field appears:
        In every status report when enabled. It is disabled in the settings mask by default.

    This data field will not appear if:
        It is disabled by the $ status report mask setting or disabled in the config.h file.

""")

    bufwer: IntProperty(
        name="Buffer Answer on Machine",
        default=15,
        description="""Buffer State:

    Bf:15,128. The first value is the number of available blocks in the planner buffer and the second is number of available bytes in the serial RX buffer.

    The usage of this data is generally for debugging an interface, but is known to be used to control some GUI-specific tasks. While this is disabled by default, GUIs should expect this data field to appear, but they may ignore it, if desired.

    NOTE: The buffer state values changed from showing "in-use" blocks or bytes to "available". This change does not require the GUI knowing how many block/bytes Grbl has been compiled with.

    This data field appears:
        In every status report when enabled. It is disabled in the settings mask by default.

    This data field will not appear if:
        It is disabled by the $ status report mask setting or disabled in the config.h file.

""")

    # ########################################################################## $0
    def s0_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$0={self.s0}")

    s0: IntProperty(
        name="Step pulse (µs)",
        default=10,
        min=1,
        max=255,
        subtype='TIME',
        update=s0_update,
        description="""$0 – Step pulse, microseconds
Stepper drivers are rated for a certain minimum step pulse length. 
Check the data sheet or just try some numbers. You want the shortest 
pulses the stepper drivers can reliably recognize. If the pulses are 
too long, you might run into trouble when running the system at very 
high feed and pulse rates, because the step pulses can begin to 
overlap each other. We recommend something around 10 microseconds, 
which is the default value.""")

    # ########################################################################## $1
    def s1_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$1={self.s1}")

    s1: IntProperty(
        name="Step idle delay (ms)",
        default=25,
        min=0,
        max=255,
        update=s1_update,
        description="""$1 - Step idle delay, milliseconds

Every time your steppers complete a motion and come to a stop, Grbl will delay disabling the steppers by this value. OR, you can always keep your axes enabled (powered so as to hold position) by setting this value to the maximum 255 milliseconds. Again, just to repeat, you can keep all axes always enabled by setting $1=255.

The stepper idle lock time is the time length Grbl will keep the steppers locked before disabling. Depending on the system, you can set this to zero and disable it. On others, you may need 25-50 milliseconds to make sure your axes come to a complete stop before disabling. This is to help account for machine motors that do not like to be left on for long periods of time without doing something. Also, keep in mind that some stepper drivers don't remember which micro step they stopped on, so when you re-enable, you may witness some 'lost' steps due to this. In this case, just keep your steppers enabled via $1=255.""")

    # ########################################################################## $2
    def s2_update(self, context):
        a = 0
        if self.s2[0]:
            a += 1
        if self.s2[1]:
            a += 2
        if self.s2[2]:
            a += 4
        context.scene.ncnc_pr_communication.send_in_order(f"$2={a}")

    s2: BoolVectorProperty(
        name="Step Port",  # Invert
        default=[False, False, False],
        subtype='XYZ',
        update=s2_update,
        description="""$2 – Step port invert, mask
This setting inverts the step pulse signal. By default, a step signal starts at normal-low and goes high upon a step pulse event. After a step pulse time set by $0, the pin resets to low, until the next step pulse event. When inverted, the step pulse behavior switches from normal-high, to low during the pulse, and back to high. Most users will not need to use this setting, but this can be useful for certain CNC-stepper drivers that have peculiar requirements. For example, an artificial delay between the direction pin and step pulse can be created by inverting the step pin.

This invert mask setting is a value which stores the axes to invert as bit flags. You really don't need to completely understand how it works. You simply need to enter the settings value for the axes you want to invert. For example, if you want to invert the X and Z axes, you'd send $2=5 to Grbl and the setting should now read $2=5 (step port invert mask:00000101)""")
    """
    Setting Value 	Mask 	Invert X 	Invert Y 	Invert Z
        0 	      00000000 	    N 	        N 	        N
        1 	      00000001 	    Y 	        N 	        N
        2 	      00000010 	    N 	        Y 	        N
        3 	      00000011 	    Y 	        Y 	        N
        4 	      00000100 	    N 	        N 	        Y
        5 	      00000101 	    Y 	        N 	        Y
        6 	      00000110 	    N 	        Y 	        Y
        7 	      00000111 	    Y 	        Y 	        Y
    """

    # ########################################################################## $3
    def s3_update(self, context):
        a = 0
        if self.s3[0]:
            a += 1
        if self.s3[1]:
            a += 2
        if self.s3[2]:
            a += 4
        context.scene.ncnc_pr_communication.send_in_order(f"$3={a}")

    s3: BoolVectorProperty(
        name="Direction Port",  # Invert
        default=[True, False, True],
        subtype='XYZ',
        update=s3_update,
        description="""$3 – Direction port invert, mask

This setting inverts the direction signal for each axis. By default, Grbl assumes that the axes move in a positive direction when the direction pin signal is low, and a negative direction when the pin is high. Often, axes don't move this way with some machines. This setting will invert the direction pin signal for those axes that move the opposite way.

This invert mask setting works exactly like the step port invert mask and stores which axes to invert as bit flags. To configure this setting, you simply need to send the value for the axes you want to invert. Use the table above. For example, if want to invert the Y axis direction only, you'd send $3=2 to Grbl and the setting should now read $3=2 (dir port invert mask:00000010)""")
    """
    Setting Value 	Mask 	Invert X 	Invert Y 	Invert Z
        0 	      00000000 	    N 	        N 	        N
        1 	      00000001 	    Y 	        N 	        N
        2 	      00000010 	    N 	        Y 	        N
        3 	      00000011 	    Y 	        Y 	        N
        4 	      00000100 	    N 	        N 	        Y
        5 	      00000101 	    Y 	        N 	        Y
        6 	      00000110 	    N 	        Y 	        Y
        7 	      00000111 	    Y 	        Y 	        Y
    """

    # ########################################################################## $4
    def s4_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$4={1 if self.s4 else 0}")

    s4: BoolProperty(
        name="$4 - Step enable invert",
        default=False,
        update=s4_update,
        description="""$4 - Step enable invert, boolean

By default, the stepper enable pin is high to disable and low to enable. If your setup needs the opposite, just invert the stepper enable pin by typing $4=1. Disable with $4=0. (May need a power cycle to load the change.)""")

    # ########################################################################## $5
    def s5_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$5={1 if self.s5 else 0}")

    s5: BoolProperty(
        name="$5 - Limit pins invert",
        default=False,
        update=s5_update,
        description="""$5 - Limit pins invert, boolean

By default, the limit pins are held normally-high with the Arduino's internal pull-up resistor. When a limit pin is low, Grbl interprets this as triggered. For the opposite behavior, just invert the limit pins by typing $5=1. Disable with $5=0. You may need a power cycle to load the change.

NOTE: For more advanced usage, the internal pull-up resistor on the limit pins may be disabled in config.h.""")

    # ########################################################################## $6
    def s6_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$6={1 if self.s6 else 0}")

    s6: BoolProperty(
        name="$6 - Probe pin invert",
        default=False,
        update=s6_update,
        description="""$6 - Probe pin invert, boolean

By default, the probe pin is held normally-high with the Arduino's internal pull-up resistor. When the probe pin is low, Grbl interprets this as triggered. For the opposite behavior, just invert the probe pin by typing $6=1. Disable with $6=0. You may need a power cycle to load the change.""")

    # ########################################################################## $10
    def s10_update(self, context):
        if self.s10 != 2:
            context.scene.ncnc_pr_communication.send_in_order(f"$10=2")

    s10: IntProperty(
        name="$10 - Status report, mask",
        default=2,
        min=0,
        max=255,
        description="$10 - Status report, mask\n0:WPos, 1:MPos, 2:Buf",
        update=s10_update
    )

    # Not CNC Configuration, only select for UI
    pos_type: EnumProperty(
        name="Select Position Mode for Display",
        description="$10 - Status report",  # 0:WPos, 1:MPos, 2:Buf
        default="wpos",
        update=s10_update,
        items=[("wpos", "WPos", "Working Position"),  # "MATPLANE", "SNAP_GRID"
               ("mpos", "MPos", "Machine Position"),  # "ORIENTATION_LOCAL"
               ])
    """
    $10   --> '?' query. Get Position Info

    Position Type 	0 	Enable WPos:    Disable MPos:.
    Position Type 	1 	Enable MPos:.   Disable WPos:.
    Buffer Data 	2 	Enabled Buf: field appears with planner and serial RX available buffer.
    """

    # ########################################################################## $11
    def s11_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$11={round(self.s11, 4)}")

    s11: FloatProperty(
        name="Junction deviation (mm)",
        default=0.010,
        precision=3,
        update=s11_update,
        description="""$11 - Junction deviation, mm

Junction deviation is used by the acceleration manager to determine how fast it can move through line segment junctions of a G-code program path. For example, if the G-code path has a sharp 10 degree turn coming up and the machine is moving at full speed, this setting helps determine how much the machine needs to slow down to safely go through the corner without losing steps.

How we calculate it is a bit complicated, but, in general, higher values gives faster motion through corners, while increasing the risk of losing steps and positioning. Lower values makes the acceleration manager more careful and will lead to careful and slower cornering. So if you run into problems where your machine tries to take a corner too fast, decrease this value to make it slow down when entering corners. If you want your machine to move faster through junctions, increase this value to speed it up. For curious people, hit this link to read about Grbl's cornering algorithm, which accounts for both velocity and junction angle with a very simple, efficient, and robust method.""")

    # ########################################################################## $12
    def s12_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$12={round(self.s12, 4)}")

    s12: FloatProperty(
        name="Arc tolerance (mm)",
        default=0.002,
        precision=3,
        update=s12_update,
        description="""$12 – Arc tolerance, mm

Grbl renders G2/G3 circles, arcs, and helices by subdividing them into teeny tiny lines, such that the arc tracing accuracy is never below this value. You will probably never need to adjust this setting, since 0.002mm is well below the accuracy of most all CNC machines. But if you find that your circles are too crude or arc tracing is performing slowly, adjust this setting. Lower values give higher precision but may lead to performance issues by overloading Grbl with too many tiny lines. Alternately, higher values traces to a lower precision, but can speed up arc performance since Grbl has fewer lines to deal with.

For the curious, arc tolerance is defined as the maximum perpendicular distance from a line segment with its end points lying on the arc, aka a chord. With some basic geometry, we solve for the length of the line segments to trace the arc that satisfies this setting. Modeling arcs in this way is great, because the arc line segments automatically adjust and scale with length to ensure optimum arc tracing performance, while never losing accuracy.""")

    # ########################################################################## $13
    def s13_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$13={self.s13}")

    s13: EnumProperty(
        items=[("0", "0: mm", ""),
               ("1", "1: inch", ""),
               ],
        name="Unit Mode",
        default="0",
        update=s13_update,
        description="""$13 - Report inches, boolean

Grbl has a real-time positioning reporting feature to provide a user feedback on where the machine is exactly at that time, as well as, parameters for coordinate offsets and probing. By default, it is set to report in mm, but by sending a $13=1 command, you send this boolean flag to true and these reporting features will now report in inches. $13=0 to set back to mm.""")

    # ########################################################################## $20
    def s20_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$20={1 if self.s20 else 0}")

    s20: BoolProperty(
        name="$20 - Soft limits",
        default=False,
        update=s20_update,
        description="""$20 - Soft limits, boolean

Soft limits is a safety feature to help prevent your machine from traveling too far and beyond the limits of travel, crashing or breaking something expensive. It works by knowing the maximum travel limits for each axis and where Grbl is in machine coordinates. Whenever a new G-code motion is sent to Grbl, it checks whether or not you accidentally have exceeded your machine space. If you do, Grbl will issue an immediate feed hold wherever it is, shutdown the spindle and coolant, and then set the system alarm indicating the problem. Machine position will be retained afterwards, since it's not due to an immediate forced stop like hard limits.

NOTE: Soft limits requires homing to be enabled and accurate axis maximum travel settings, because Grbl needs to know where it is. $20=1 to enable, and $20=0 to disable.""")

    # ########################################################################## $21
    def s21_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$21={1 if self.s21 else 0}")

    s21: BoolProperty(
        name="$21 - Hard limits",
        default=False,
        update=s21_update,
        description="""$21 - Hard limits, boolean

Hard limit work basically the same as soft limits, but use physical switches instead. Basically you wire up some switches (mechanical, magnetic, or optical) near the end of travel of each axes, or where ever you feel that there might be trouble if your program moves too far to where it shouldn't. When the switch triggers, it will immediately halt all motion, shutdown the coolant and spindle (if connected), and go into alarm mode, which forces you to check your machine and reset everything.

To use hard limits with Grbl, the limit pins are held high with an internal pull-up resistor, so all you have to do is wire in a normally-open switch with the pin and ground and enable hard limits with $21=1. (Disable with $21=0.) We strongly advise taking electric interference prevention measures. If you want a limit for both ends of travel of one axes, just wire in two switches in parallel with the pin and ground, so if either one of them trips, it triggers the hard limit.

Keep in mind, that a hard limit event is considered to be critical event, where steppers immediately stop and will have likely have lost steps. Grbl doesn't have any feedback on position, so it can't guarantee it has any idea where it is. So, if a hard limit is triggered, Grbl will go into an infinite loop ALARM mode, giving you a chance to check your machine and forcing you to reset Grbl. Remember it's a purely a safety feature.""")

    # ########################################################################## $22
    def s22_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$22={1 if self.s22 else 0}")

    s22: BoolProperty(
        name="$22 - Homing cycle",
        default=False,
        update=s22_update,
        description="""$22 - Homing cycle, boolean

Ahh, homing. For those just initiated into CNC, the homing cycle is used to accurately and precisely locate a known and consistent position on a machine every time you start up your Grbl between sessions. In other words, you know exactly where you are at any given time, every time. Say you start machining something or are about to start the next step in a job and the power goes out, you re-start Grbl and Grbl has no idea where it is due to steppers being open-loop control. You're left with the task of figuring out where you are. If you have homing, you always have the machine zero reference point to locate from, so all you have to do is run the homing cycle and resume where you left off.

To set up the homing cycle for Grbl, you need to have limit switches in a fixed position that won't get bumped or moved, or else your reference point gets messed up. Usually they are setup in the farthest point in +x, +y, +z of each axes. Wire your limit switches in with the limit pins, add a recommended RC-filter to help reduce electrical noise, and enable homing. If you're curious, you can use your limit switches for both hard limits AND homing. They play nice with each other.

Prior to trying the homing cycle for the first time, make sure you have setup everything correctly, otherwise homing may behave strangely. First, ensure your machine axes are moving in the correct directions per Cartesian coordinates (right-hand rule). If not, fix it with the $3 direction invert setting. Second, ensure your limit switch pins are not showing as 'triggered' in Grbl's status reports. If are, check your wiring and settings. Finally, ensure your $13x max travel settings are somewhat accurate (within 20%), because Grbl uses these values to determine how far it should search for the homing switches.

By default, Grbl's homing cycle moves the Z-axis positive first to clear the workspace and then moves both the X and Y-axes at the same time in the positive direction. To set up how your homing cycle behaves, there are more Grbl settings down the page describing what they do (and compile-time options as well.)

Also, one more thing to note, when homing is enabled. Grbl will lock out all G-code commands until you perform a homing cycle. Meaning no axes motions, unless the lock is disabled ($X) but more on that later. Most, if not all CNC controllers, do something similar, as it is mostly a safety feature to prevent users from making a positioning mistake, which is very easy to do and be saddened when a mistake ruins a part. If you find this annoying or find any weird bugs, please let us know and we'll try to work on it so everyone is happy. :)

NOTE: Check out config.h for more homing options for advanced users. You can disable the homing lockout at startup, configure which axes move first during a homing cycle and in what order, and more.""")

    # ########################################################################## $23
    def s23_update(self, context):
        a = 0
        if self.s23[0]:
            a += 1
        if self.s23[1]:
            a += 2
        if self.s23[2]:
            a += 4
        context.scene.ncnc_pr_communication.send_in_order(f"$23={a}")

    s23: BoolVectorProperty(
        name="Homing Dir",  # Invert
        default=[False, False, False],
        subtype='XYZ',
        update=s23_update,
        description="""$23 - Homing dir invert, mask

By default, Grbl assumes your homing limit switches are in the positive direction, first moving the z-axis positive, then the x-y axes positive before trying to precisely locate machine zero by going back and forth slowly around the switch. If your machine has a limit switch in the negative direction, the homing direction mask can invert the axes' direction. It works just like the step port invert and direction port invert masks, where all you have to do is send the value in the table to indicate what axes you want to invert and search for in the opposite direction.""")

    # ########################################################################## $24
    def s24_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$24={round(self.s24, 4)}")

    s24: FloatProperty(
        name="Homing feed (mm/min)",
        default=25.000,
        precision=3,
        update=s24_update,
        description="""$24 - Homing feed, mm/min

The homing cycle first searches for the limit switches at a higher seek rate, and after it finds them, it moves at a slower feed rate to home into the precise location of machine zero. Homing feed rate is that slower feed rate. Set this to whatever rate value that provides repeatable and precise machine zero locating.""")

    # ########################################################################## $25
    def s25_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$25={round(self.s25, 4)}")

    s25: FloatProperty(
        name="Homing seek (mm/min)",
        default=500.000,
        precision=3,
        update=s25_update,
        description="""$25 - Homing seek, mm/min

Homing seek rate is the homing cycle search rate, or the rate at which it first tries to find the limit switches. Adjust to whatever rate gets to the limit switches in a short enough time without crashing into your limit switches if they come in too fast.""")

    # ########################################################################## $26
    def s26_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$26={self.s26}")

    s26: IntProperty(
        name="Homing debounce (ms)",
        default=250,
        min=10,
        max=1000,
        subtype='TIME',
        update=s26_update,
        description="""$26 - Homing debounce, milliseconds

Whenever a switch triggers, some of them can have electrical/mechanical noise that actually 'bounce' the signal high and low for a few milliseconds before settling in. To solve this, you need to debounce the signal, either by hardware with some kind of signal conditioner or by software with a short delay to let the signal finish bouncing. Grbl performs a short delay, only homing when locating machine zero. Set this delay value to whatever your switch needs to get repeatable homing. In most cases, 5-25 milliseconds is fine.""")

    # ########################################################################## $27
    def s27_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$27={round(self.s27, 4)}")

    s27: FloatProperty(
        name="Homing pull-off (mm)",
        default=1.000,
        precision=3,
        update=s27_update,
        description="""$27 - Homing pull-off, mm

To play nice with the hard limits feature, where homing can share the same limit switches, the homing cycle will move off all of the limit switches by this pull-off travel after it completes. In other words, it helps to prevent accidental triggering of the hard limit after a homing cycle. Make sure this value is large enough to clear the limit switch. If not, Grbl will throw an alarm error for failing to clear it.""")

    # ########################################################################## $30
    def s30_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$30={self.s30}")

    s30: IntProperty(
        name="Max spindle speed (RPM)",
        default=1000,
        min=0,
        max=25000,
        subtype='ANGLE',
        update=s30_update,
        description="""$30 - Max spindle speed, RPM

This sets the spindle speed for the maximum 5V PWM pin output. For example, if you want to set 10000rpm at 5V, program $30=10000. For 255rpm at 5V, program $30=255. If a program tries to set a higher spindle RPM greater than the $30 max spindle speed, Grbl will just output the max 5V, since it can't go any faster. By default, Grbl linearly relates the max-min RPMs to 5V-0.02V PWM pin output in 255 equally spaced increments. When the PWM pin reads 0V, this indicates spindle disabled. Note that there are additional configuration options are available in config.h to tweak how this operates.""")

    # ########################################################################## $31
    def s31_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$31={self.s31}")

    s31: IntProperty(
        name="Min spindle speed (RPM)",
        default=0,
        min=0,
        max=25000,
        subtype='ANGLE',
        update=s31_update,
        description="""$31 - Min spindle speed, RPM

This sets the spindle speed for the minimum 0.02V PWM pin output (0V is disabled). Lower RPM values are accepted by Grbl but the PWM output will not go below 0.02V, except when RPM is zero. If zero, the spindle is disabled and PWM output is 0V.""")

    # ########################################################################## $32
    def s32_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$32={1 if self.s32 else 0}")

    s32: BoolProperty(
        name="$32 - Laser mode",
        default=False,
        update=s32_update,
        description="""$32 - Laser mode, boolean

When enabled, Grbl will move continuously through consecutive G1, G2, or G3 motion commands when programmed with a S spindle speed (laser power). The spindle PWM pin will be updated instantaneously through each motion without stopping. Please read the GRBL laser documentation and your laser machine documentation prior to using this mode. Lasers are very dangerous. They can instantly damage your vision permanantly and cause fires. Grbl does not assume any responsibility for any issues the firmware may cause, as defined by its GPL license.

When disabled, Grbl will operate as it always has, stopping motion with every S spindle speed command. This is the default operation of a milling machine to allow a pause to let the spindle change speeds.""")

    # ########################################################################## $100
    def s100_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$100={round(self.s100, 3)}")

    s100: FloatProperty(
        name="X",
        default=800.000,
        precision=3,
        update=s100_update,
        description="""X-axis travel resolution, step/mm
$100, $101 and $102 – [X,Y,Z] steps/mm

Grbl needs to know how far each step will take the tool in reality. To calculate steps/mm for an axis of your machine you need to know:

    The mm traveled per revolution of your stepper motor. This is dependent on your belt drive gears or lead screw pitch.
    The full steps per revolution of your steppers (typically 200)
    The microsteps per step of your controller (typically 1, 2, 4, 8, or 16). Tip: Using high microstep values (e.g., 16) can reduce your stepper motor torque, so use the lowest that gives you the desired axis resolution and comfortable running properties.

The steps/mm can then be calculated like this: steps_per_mm = (steps_per_revolution*microsteps)/mm_per_rev

Compute this value for every axis and write these settings to Grbl.""")

    # ########################################################################## $101
    def s101_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$101={round(self.s101, 3)}")

    s101: FloatProperty(
        name="Y",
        default=800.000,
        precision=3,
        update=s101_update,
        description="""Y-axis travel resolution, step/mm
$100, $101 and $102 – [X,Y,Z] steps/mm

Grbl needs to know how far each step will take the tool in reality. To calculate steps/mm for an axis of your machine you need to know:

    The mm traveled per revolution of your stepper motor. This is dependent on your belt drive gears or lead screw pitch.
    The full steps per revolution of your steppers (typically 200)
    The microsteps per step of your controller (typically 1, 2, 4, 8, or 16). Tip: Using high microstep values (e.g., 16) can reduce your stepper motor torque, so use the lowest that gives you the desired axis resolution and comfortable running properties.

The steps/mm can then be calculated like this: steps_per_mm = (steps_per_revolution*microsteps)/mm_per_rev

Compute this value for every axis and write these settings to Grbl.""")

    # ########################################################################## $102
    def s102_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$102={round(self.s102, 3)}")

    s102: FloatProperty(
        name="Y",
        default=800.000,
        precision=3,
        update=s102_update,
        description="""Z-axis travel resolution, step/mm
$100, $101 and $102 – [X,Y,Z] steps/mm

Grbl needs to know how far each step will take the tool in reality. To calculate steps/mm for an axis of your machine you need to know:

    The mm traveled per revolution of your stepper motor. This is dependent on your belt drive gears or lead screw pitch.
    The full steps per revolution of your steppers (typically 200)
    The microsteps per step of your controller (typically 1, 2, 4, 8, or 16). Tip: Using high microstep values (e.g., 16) can reduce your stepper motor torque, so use the lowest that gives you the desired axis resolution and comfortable running properties.

The steps/mm can then be calculated like this: steps_per_mm = (steps_per_revolution*microsteps)/mm_per_rev

Compute this value for every axis and write these settings to Grbl.""")

    # ########################################################################## $110
    def s110_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$110={round(self.s110, 3)}")

    s110: FloatProperty(
        name="X",
        default=500.000,
        precision=3,
        update=s110_update,
        description="""X-axis maximum rate, mm/min
$110, $111 and $112 – [X,Y,Z] Max rate, mm/min

This sets the maximum rate each axis can move. Whenever Grbl plans a move, it checks whether or not the move causes any one of these individual axes to exceed their max rate. If so, it'll slow down the motion to ensure none of the axes exceed their max rate limits. This means that each axis has its own independent speed, which is extremely useful for limiting the typically slower Z-axis.

The simplest way to determine these values is to test each axis one at a time by slowly increasing max rate settings and moving it. For example, to test the X-axis, send Grbl something like G0 X50 with enough travel distance so that the axis accelerates to its max speed. You'll know you've hit the max rate threshold when your steppers stall. It'll make a bit of noise, but shouldn't hurt your motors. Enter a setting a 10-20% below this value, so you can account for wear, friction, and the mass of your workpiece/tool. Then, repeat for your other axes.

NOTE: This max rate setting also sets the G0 seek rates.""")

    # ########################################################################## $111
    def s111_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$111={round(self.s111, 3)}")

    s111: FloatProperty(
        name="Y",
        default=500.000,
        precision=3,
        update=s111_update,
        description="""Y-axis maximum rate, mm/min
$110, $111 and $112 – [X,Y,Z] Max rate, mm/min

This sets the maximum rate each axis can move. Whenever Grbl plans a move, it checks whether or not the move causes any one of these individual axes to exceed their max rate. If so, it'll slow down the motion to ensure none of the axes exceed their max rate limits. This means that each axis has its own independent speed, which is extremely useful for limiting the typically slower Z-axis.

The simplest way to determine these values is to test each axis one at a time by slowly increasing max rate settings and moving it. For example, to test the X-axis, send Grbl something like G0 X50 with enough travel distance so that the axis accelerates to its max speed. You'll know you've hit the max rate threshold when your steppers stall. It'll make a bit of noise, but shouldn't hurt your motors. Enter a setting a 10-20% below this value, so you can account for wear, friction, and the mass of your workpiece/tool. Then, repeat for your other axes.

NOTE: This max rate setting also sets the G0 seek rates.""")

    # ########################################################################## $112
    def s112_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$112={round(self.s112, 3)}")

    s112: FloatProperty(
        name="Z",
        default=500.000,
        precision=3,
        update=s112_update,
        description="""Z-axis maximum rate, mm/min
$110, $111 and $112 – [X,Y,Z] Max rate, mm/min

This sets the maximum rate each axis can move. Whenever Grbl plans a move, it checks whether or not the move causes any one of these individual axes to exceed their max rate. If so, it'll slow down the motion to ensure none of the axes exceed their max rate limits. This means that each axis has its own independent speed, which is extremely useful for limiting the typically slower Z-axis.

The simplest way to determine these values is to test each axis one at a time by slowly increasing max rate settings and moving it. For example, to test the X-axis, send Grbl something like G0 X50 with enough travel distance so that the axis accelerates to its max speed. You'll know you've hit the max rate threshold when your steppers stall. It'll make a bit of noise, but shouldn't hurt your motors. Enter a setting a 10-20% below this value, so you can account for wear, friction, and the mass of your workpiece/tool. Then, repeat for your other axes.

NOTE: This max rate setting also sets the G0 seek rates.""")

    # ########################################################################## $120
    def s120_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$120={round(self.s120, 3)}")

    s120: FloatProperty(
        name="X",
        default=10.000,
        precision=3,
        update=s120_update,
        description="""X-axis acceleration, mm/sec^2
$120, $121, $122 – [X,Y,Z] Acceleration, mm/sec^2

This sets the axes acceleration parameters in mm/second/second. Simplistically, a lower value makes Grbl ease slower into motion, while a higher value yields tighter moves and reaches the desired feed rates much quicker. Much like the max rate setting, each axis has its own acceleration value and are independent of each other. This means that a multi-axis motion will only accelerate as quickly as the lowest contributing axis can.

Again, like the max rate setting, the simplest way to determine the values for this setting is to individually test each axis with slowly increasing values until the motor stalls. Then finalize your acceleration setting with a value 10-20% below this absolute max value. This should account for wear, friction, and mass inertia. We highly recommend that you dry test some G-code programs with your new settings before committing to them. Sometimes the loading on your machine is different when moving in all axes together.
""")

    # ########################################################################## $121
    def s121_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$121={round(self.s121, 3)}")

    s121: FloatProperty(
        name="Y",
        default=10.000,
        precision=3,
        update=s121_update,
        description="""Y-axis acceleration, mm/sec^2
$120, $121, $122 – [X,Y,Z] Acceleration, mm/sec^2

This sets the axes acceleration parameters in mm/second/second. Simplistically, a lower value makes Grbl ease slower into motion, while a higher value yields tighter moves and reaches the desired feed rates much quicker. Much like the max rate setting, each axis has its own acceleration value and are independent of each other. This means that a multi-axis motion will only accelerate as quickly as the lowest contributing axis can.

Again, like the max rate setting, the simplest way to determine the values for this setting is to individually test each axis with slowly increasing values until the motor stalls. Then finalize your acceleration setting with a value 10-20% below this absolute max value. This should account for wear, friction, and mass inertia. We highly recommend that you dry test some G-code programs with your new settings before committing to them. Sometimes the loading on your machine is different when moving in all axes together.
""")

    # ########################################################################## $122
    def s122_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$122={round(self.s122, 3)}")

    s122: FloatProperty(
        name="Z",
        default=10.000,
        precision=3,
        update=s122_update,
        description="""Z-axis acceleration, mm/sec^2
$120, $121, $122 – [X,Y,Z] Acceleration, mm/sec^2

This sets the axes acceleration parameters in mm/second/second. Simplistically, a lower value makes Grbl ease slower into motion, while a higher value yields tighter moves and reaches the desired feed rates much quicker. Much like the max rate setting, each axis has its own acceleration value and are independent of each other. This means that a multi-axis motion will only accelerate as quickly as the lowest contributing axis can.

Again, like the max rate setting, the simplest way to determine the values for this setting is to individually test each axis with slowly increasing values until the motor stalls. Then finalize your acceleration setting with a value 10-20% below this absolute max value. This should account for wear, friction, and mass inertia. We highly recommend that you dry test some G-code programs with your new settings before committing to them. Sometimes the loading on your machine is different when moving in all axes together.
""")

    # ########################################################################## $130
    def s130_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$130={round(self.s130, 3)}")

    s130: FloatProperty(
        name="X",
        default=200.000,
        precision=3,
        update=s130_update,
        description="""X-axis maximum travel, millimeters
$130, $131, $132 – [X,Y,Z] Max travel, mm

This sets the maximum travel from end to end for each axis in mm. This is only useful if you have soft limits (and homing) enabled, as this is only used by Grbl's soft limit feature to check if you have exceeded your machine limits with a motion command.""")

    # ########################################################################## $131
    def s131_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$131={round(self.s131, 3)}")

    s131: FloatProperty(
        name="Y",
        default=200.000,
        precision=3,
        update=s131_update,
        description="""Y-axis maximum travel, millimeters
$130, $131, $132 – [X,Y,Z] Max travel, mm

This sets the maximum travel from end to end for each axis in mm. This is only useful if you have soft limits (and homing) enabled, as this is only used by Grbl's soft limit feature to check if you have exceeded your machine limits with a motion command.""")

    # ########################################################################## $132
    def s132_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"$132={round(self.s132, 3)}")

    s132: FloatProperty(
        name="Z",
        default=200.000,
        precision=3,
        update=s132_update,
        description="""Z-axis maximum travel, millimeters
$130, $131, $132 – [X,Y,Z] Max travel, mm

This sets the maximum travel from end to end for each axis in mm. This is only useful if you have soft limits (and homing) enabled, as this is only used by Grbl's soft limit feature to check if you have exceeded your machine limits with a motion command.""")

    # ##############################################################################
    # def motion_mode_update(self, context):
    #    context.scene.ncnc_pr_communication.send_in_order(f"{self.motion_mode}")

    motion_mode: EnumProperty(
        name="Motion Mode",
        default="G0",
        description="Only Read",
        items=[("G0", "G0 - Rapid Move", "G0 - For rapid motion, program G0 axes, where all the axis words are "
                                         "optional. The G0 is optional if the current motion mode is G0. This will "
                                         "produce coordinated motion to the destination point at the maximum rapid "
                                         "rate (or slower). G0 is typically used as a positioning move."),
               ("G1", "G1 - Linear Move",
                "G1 - For linear (straight line) motion at programed feed "
                "rate (for cutting or not), program G1 'axes', "
                "where all the axis words are optional. The G1 is optional "
                "if the current motion mode is G1. This will produce "
                "coordinated motion to the destination point at the "
                "current feed rate (or slower)."),
               ("G2", "G2 - Clockwise Arc Move", "G2 CW - A circular or helical arc is specified "
                                                 "using either G2 (clockwise arc) or G3 ("
                                                 "counterclockwise arc) at the current feed rate. "
                                                 "The direction (CW, CCW) is as viewed from the "
                                                 "positive end of the axis about which the circular "
                                                 "motion occurs."),
               ("G3", "G3 - CounterClockwise Arc Move", "G3 CCW - A circular or helical arc is "
                                                        "specified using either G2 (clockwise arc) "
                                                        "or G3 (counterclockwise arc) at the current "
                                                        "feed rate. The direction (CW, CCW) is as "
                                                        "viewed from the positive end of the axis "
                                                        "about which the circular motion occurs."),
               ("G38.2", "G38.2 - Straight Probe", "G38.2 - probe toward workpiece, stop on contact, signal error if "
                                                   "failure "),
               ("G38.3", "G38.3 - Straight Probe", "G38.3 - probe toward workpiece, stop on contact "),
               ("G38.4", "G38.4 - Straight Probe", "G38.4 - probe away from workpiece, stop on loss of contact, "
                                                   "signal error if failure"),
               ("G38.5", "G38.5 - Straight Probe", "G38.5 - probe away from workpiece, stop on loss of contact"),
               ("G80", "G80 - Cancel Canned Cycle", "G80 - cancel canned cycle modal motion. G80 is part of modal "
                                                    "group 1, so programming any other G code from modal group 1 will"
                                                    " also cancel the canned cycle. "),
               ],
        # update=motion_mode_update
    )

    # ##############################################################################
    def coordinate_system_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.coordinate_system}")

    coordinate_system: EnumProperty(
        name="Coordinate System",
        default="G54",
        update=coordinate_system_update,
        items=[("G54", "G54 - System 1", "Select coordinate system 1"),
               ("G55", "G55 - System 2", "Select coordinate system 2"),
               ("G56", "G56 - System 3", "Select coordinate system 3"),
               ("G57", "G57 - System 4", "Select coordinate system 4"),
               ("G58", "G58 - System 5", "Select coordinate system 5"),
               ("G59", "G59 - System 6", "Select coordinate system 6"),
               # ("G59.1", "G59.1 - System 7", "Select coordinate system 7"),
               # ("G59.2", "G59.2 - System 8", "Select coordinate system 8"),
               # ("G59.3", "G59.3 - System 9", "Select coordinate system 9"),
               ])

    # ##############################################################################
    def distance_mode_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.distance_mode}")

    distance_mode: EnumProperty(
        name="Distance Mode",
        default="G90",
        update=distance_mode_update,
        items=[("G90", "G90 - Absolute", "G90 - Absolute Distance Mode"),
               ("G91", "G91 - Incremental", "91 - Incremental Distance Mode")
               ])

    # ##############################################################################
    def plane_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.plane}")

    plane: EnumProperty(
        name="Plane Select",
        description="These codes set the current plane",
        default="G17",
        update=plane_update,
        items=[
            ("G17", "G17 - XY", ""),
            ("G18", "G18 - ZX", ""),
            ("G19", "G19 - YZ", "")
        ])

    # ##############################################################################
    def arc_ijk_distance_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.arc_ijk_distance}")

    arc_ijk_distance: EnumProperty(
        name="Arc IJK Distance Mode",
        description="Arc Distance Mode",
        default="G91.1",
        update=arc_ijk_distance_update,
        items=[("G91.1", "G91.1", "G91.1 - incremental distance mode for I, J & K offsets. G91.1 Returns I, J & K to "
                                  "their default behavior. ")
               ])

    # ##############################################################################
    def feed_rate_mode_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.feed_rate_mode}")

    feed_rate_mode: EnumProperty(
        name="Feed Rate Mode",
        description="",
        default="G94",
        update=feed_rate_mode_update,
        items=[
            ("G93", "G93 - Inverse Time", "G93 - is Inverse Time Mode. In inverse time feed "
                                          "rate mode, "
                                          "an F word means the move should be completed in [one divided by "
                                          "the F number] minutes. For example, if the F number is 2.0, "
                                          "the move should be completed in half a minute.\nWhen the inverse "
                                          "time feed rate mode is active, an F word must appear on every "
                                          "line which has a G1, G2, or G3 motion, and an F word on a line "
                                          "that does not have G1, G2, or G3 is ignored. Being in inverse "
                                          "time feed rate mode does not affect G0 (rapid move) motions."),
            ("G94", "G94 - Units per Minute", "G94 - is Units per Minute Mode. In units per "
                                              "minute feed mode, "
                                              "an F word is interpreted to mean the controlled point should "
                                              "move at a certain number of inches per minute, millimeters per "
                                              "minute, or degrees per minute, depending upon what length units "
                                              "are being used and which axis or axes are moving. ")
        ])

    # ##############################################################################
    def units_mode_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.units_mode}")

    units_mode: EnumProperty(
        name="Units Mode",
        description="",
        default="G21",
        update=units_mode_update,
        items=[
            ("G20", "G20 - inc", "G20 - to use inches for length units."),
            ("G21", "G21 - mm", "G21 - to use millimeters for length units.")
        ])

    cutter_radius_compensation: EnumProperty(
        name="Cutter Radius Compensation",
        description="",
        default="G40",
        items=[
            ("G40", "G40", "G40 - turn cutter compensation off. If tool "
                           "compensation was on the next move must be a linear "
                           "move and longer than the tool diameter. It is OK to "
                           "turn compensation off when it is already off. ")
        ])

    # ##############################################################################
    def tool_length_offset_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.tool_length_offset}")

    tool_length_offset: EnumProperty(
        name="Tool Length Offset",
        description="",
        default="G49",
        update=tool_length_offset_update,
        items=[
            ("G43.1", "G43.1 - Dynamic", "G43.1 axes - change subsequent motions by "
                                         "replacing the current offset(s) of axes. G43.1 "
                                         "does not cause any motion. The next time a "
                                         "compensated axis is moved, that axis’s "
                                         "endpoint is the compensated location. "),
            ("G49", "G49 - Cancels", "It is OK to program using the same offset already "
                                     "in use. It is also OK to program using no tool "
                                     "length offset if none is currently being used.")
        ])

    # ##############################################################################
    def program_mode_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.program_mode}")

    program_mode: EnumProperty(
        name="Program Mode",
        description="",
        default="M0",
        update=program_mode_update,
        items=[
            ("M0", "M0 - Pause", "M0 - pause a running program temporarily. CNC remains in the "
                                 "Auto Mode so MDI and other manual actions are not enabled. "
                                 "Pressing the resume button will restart the program at the "
                                 "following line. "),
            ("M1", "M1 - Pause", "M1 - pause a running program temporarily if the optional "
                                 "stop switch is on. LinuxCNC remains in the Auto Mode so MDI "
                                 "and other manual actions are not enabled. Pressing the "
                                 "resume button will restart the program at the following "
                                 "line. "),
            ("M2", "M2 - End", 'M2 - end the program. Pressing Cycle Start ("R" in the Axis '
                               'GUI) will restart the program at the beginning of the file. '),
            ("M30", "M30 - End", "M30 - exchange pallet shuttles and end the program. Pressing "
                                 "Cycle Start will start the program at the beginning of the "
                                 "file. ")
        ])

    # ##############################################################################
    def spindle_state_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.spindle_state}")

    spindle_state: EnumProperty(
        name="Spindle State",
        description="Spindle Control",
        default="M5",
        update=spindle_state_update,
        items=[
            ("M3", "M3 - Start CW", "M3 - start the spindle clockwise at the S speed."),
            ("M4", "M4 - Start CCW", "M4 - start the spindle counterclockwise at the S speed."),
            ("M5", "M5 - Stop", "M5 - stop the spindle. ")
        ])

    # ##############################################################################
    def coolant_state_update(self, context):
        context.scene.ncnc_pr_communication.send_in_order(f"{self.coolant_state}")

    coolant_state: EnumProperty(
        name="Coolant State",
        description="",
        default="M9",
        update=coolant_state_update,
        items=[
            ("M7", "M7 - turn mist coolant on", "M7 - turn mist coolant on. M7 controls "
                                                "iocontrol.0.coolant-mist pin. "),
            ("M8", "M8 - turn flood coolant on", "M8 - turn flood coolant on. M8 controls "
                                                 "iocontrol.0.coolant-flood pin."),
            ("M9", "M9 - turn off", "M9 - turn both M7 and M8 off. ")
        ])

    @classmethod
    def register(cls):
        Scene.ncnc_pr_machine = PointerProperty(
            name="NCNC_PR_Machine Name",
            description="NCNC_PR_Machine Description",
            type=cls)

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_machine
