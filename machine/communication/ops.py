import re
import time
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, EnumProperty

from .. import dev_get
from ...utils.modal import register_modal, unregister_modal

tr_translate = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")


rex_conf = '\$ *(\d*?) *\= *(\d+\.*\d*?)(?:$|\D+.*$)'


def mask(my_int, min_len=3):
    """
    my_int:
        1       -> 001
        15      -> 1111
        ...
    min_len:    minimum_len -> List Count
        1 ->    [ True ]
        2 ->    [ True, True ]
        3 ->    [ True, True, True ]
        ...
    """
    return [b == '1' for b in bin(my_int)[2:].rjust(min_len)[::-1]]


def mask_s10(my_int):
    return str(my_int % 3)


dev_list = {
    "0": int,  # $0=10
    "1": int,  # $1=25
    "2": mask,  # $2=0      # BoolVectorProperty
    "3": mask,  # $3=5      # BoolVectorProperty
    "4": bool,  # $4=0
    "5": bool,  # $5=0
    "6": bool,  # $6=0
    "10": int,  # $10=1
    "11": float,  # $11=0.010
    "12": float,  # $12=0.002
    "13": str,  # $13=0
    "20": bool,  # $20=0
    "21": bool,  # $21=0
    "22": bool,  # $22=0
    "23": mask,  # $23=0    # BoolVectorProperty
    "24": float,  # $24=25.000
    "25": float,  # $25=500.000
    "26": int,  # $26=250
    "27": float,  # $27=1.000
    "30": int,  # $30=1000
    "31": int,  # $31=0
    "100": float,  # $100=800.000
    "101": float,  # $101=800.000
    "102": float,  # $102=800.000
    "110": float,  # $110=500.000
    "111": float,  # $111=500.000
    "112": float,  # $112=500.000
    "120": float,  # $120=10.000
    "121": float,  # $121=10.000
    "122": float,  # $122=10.000
    "130": float,  # $130=200.000
    "131": float,  # $131=200.000
    "132": float,  # $132=200.000
}


"""
>>> $$
$0 = 10    (Step pulse time, microseconds)
$1 = 25    (Step idle delay, milliseconds)
$2 = 0    (Step pulse invert, mask)
$3 = 5    (Step direction invert, mask)
$4 = 0    (Invert step enable pin, boolean)
$5 = 0    (Invert limit pins, boolean)
$6 = 0    (Invert probe pin, boolean)
$10 = 0    (Status report options, mask)
$11 = 0.010    (Junction deviation, millimeters)
$12 = 0.002    (Arc tolerance, millimeters)
$13 = 0    (Report in inches, boolean)
$20 = 0    (Soft limits enable, boolean)
$21 = 0    (Hard limits enable, boolean)
$22 = 0    (Homing cycle enable, boolean)
$23 = 0    (Homing direction invert, mask)
$24 = 25.000    (Homing locate feed rate, mm/min)
$25 = 500.000    (Homing search seek rate, mm/min)
$26 = 250    (Homing switch debounce delay, milliseconds)
$27 = 1.000    (Homing switch pull-off distance, millimeters)
$30 = 1000    (Maximum spindle speed, RPM)
$31 = 0    (Minimum spindle speed, RPM)
$32 = 0    (Laser-mode enable, boolean)
$100 = 800.000    (X-axis travel resolution, step/mm)
$101 = 800.000    (Y-axis travel resolution, step/mm)
$102 = 800.000    (Z-axis travel resolution, step/mm)
$110 = 500.000    (X-axis maximum rate, mm/min)
$111 = 500.000    (Y-axis maximum rate, mm/min)
$112 = 500.000    (Z-axis maximum rate, mm/min)
$120 = 10.000    (X-axis acceleration, mm/sec^2)
$121 = 10.000    (Y-axis acceleration, mm/sec^2)
$122 = 10.000    (Z-axis acceleration, mm/sec^2)
$130 = 200.000    (X-axis maximum travel, millimeters)
$131 = 200.000    (Y-axis maximum travel, millimeters)
$132 = 200.000    (Z-axis maximum travel, millimeters)

>>> $G
[GC:G0 G54 G17 G21 G90 G94 M5 M9 T0 F0 S0]
"""


class NCNC_OT_Decoder(Operator):
    bl_idname = "ncnc.decoder"
    bl_label = "NCNC Decoder"
    bl_description = "Resolve Receive Codes"
    # bl_options = {'REGISTER'}

    q_count = 0

    ct_reg = None  # Context, Regions
    pr_con = None
    pr_com = None
    pr_dev = None

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

        self.report({'INFO'}, "NCNC Decoder Started")

        return self.timer_add(context)

    def timer_add(self, context):
        # add to timer
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

        # !!! Bug: 3D ViewPort kısmını, sol üstten, TextEditor vs 'ye çevirince, bu kısımda hata çıkıyor.
        # Bug fixed in v0.6.4
        if not context.area:
            self.report({'WARNING'}, "Main Area Closed")
            self.report({'Info'}, "You need to re-establish the connection.")
            unregister_modal(self)
            context.scene.ncnc_pr_connection.isconnected = False
            return self.timer_remove(context)

        self.ct_reg = context.area.regions
        self.pr_dev = context.scene.ncnc_pr_machine
        self.pr_con = context.scene.ncnc_pr_connection
        self.pr_com = context.scene.ncnc_pr_communication

        if not self.pr_con.isconnected:
            return self.timer_remove(context)

        if not self.pr_com.isactive or self.pr_com.isrun or self.q_count < 5:
            self.decode("?")
            self.q_count += 1
        else:
            self.decode("$G")
            self.q_count = 0

        # self.decode("?")

        return {'PASS_THROUGH'}

    def decode(self, msg="?"):
        if msg:
            if not (len(self.pr_com.queue_list_hidden) and self.pr_com.queue_list_hidden[-1] == msg):
                self.pr_com.set_hidden(msg)
        while 1:
            c = self.pr_com.get_answer()
            if not c:
                break
            c = c.lower()

            # print("get_answer   ->", c)

            if c == "ok":
                """ok : Indicates the command line received was parsed and executed (or set to be executed)."""
                continue
            elif c.startswith("error:"):
                """error:x : Indicated the command line received contained an error, with an error code x, and was 
                purged. See error code section below for definitions."""
                continue
            elif c.startswith("alarm"):
                self.pr_dev.status = c.upper()
                continue
            elif c.startswith("<") and c.endswith(">"):
                """< > : Enclosed chevrons contains status report data.Examples;
                    <Idle|WPos:120.000,50.000,0.000|FS:0,0>
                    <Jog|WPos:94.853,50.000,0.000|FS:500,0>
                """
                self.status_report(c.strip("<>"))
                continue
            elif re.findall("\[gc\:(.*)\]", c):  # c.startswith("[gc") and c.endswith("]"):
                """[gc:g0 g54 g17 g21 g90 g94 m5 m9 t0 f0 s0]"""
                self.modes(re.findall("\[gc\:(.*)\]", c)[0])

            # ############################################### RESOLVE
            # ################################################ $x=val
            # r = [('12', '0.002')]
            for i in re.findall(rex_conf, c):

                # i = ('12', '0.002')
                if i[0] in dev_list.keys():

                    # '12', "0.002"     before -> "$12=0.002"
                    x, val = i

                    # float/int/set/mask
                    conv = dev_list[x]

                    # prop = cls.pr_dev.s1/2/3...
                    local_vars = {}

                    exec(f"p = self.pr_dev.s{x}", {"self": self}, local_vars)
                    prop = local_vars["p"] if conv is not float else round(local_vars["p"], 4)

                    # float("0.002")
                    var = conv(int(val)) if conv in [bool, mask, mask_s10] else conv(val)

                    # [True, False, True]
                    if conv is mask:
                        for k in range(len(var)):
                            if var[k] != prop[k]:
                                exec(f"self.pr_dev.s{x}[{k}] = {var[k]}")
                                # cls.pr_dev[f"s"][k] = var[k]
                    else:
                        if var != prop:
                            if conv in [str, mask_s10]:
                                exec(f'self.pr_dev.s{x} = "{var}"')
                            else:
                                exec(f'self.pr_dev.s{x} = {var}')
                            # cls.pr_dev[f"s{x}"] = var

        if self.ct_reg:
            for region in self.ct_reg:
                if region.type == "UI":
                    region.tag_redraw()

    def status_report(self, code):
        """ >> ?
        Idle|MPos:0.000,0.000,0.000|FS:0,0|WCO:-80.000,-50.000,0.000
        Idle|MPos:0.000,0.000,0.000|FS:0,0|Ov:100,100,100
        Idle|MPos:0.000,0.000,0.000|FS:0,0

        Idle|WPos:0.000,0.000,0.000|FS:0,0

        jog|wpos:90.003,50.000,0.000|bf:15,127|fs:0,0

        Status; Idle, Run, Hold, Jog, Alarm, Door, Check, Home, Sleep
        """

        codes = code.split("|")

        if len(codes):
            self.pr_dev.status = codes.pop(0).upper()

        for i in codes:
            a = i.split(":")[1].split(",")
            for key, var in (("mpos", self.pr_dev.mpos),
                             ("wpos", self.pr_dev.wpos),
                             ("wco", self.pr_dev.wco)):
                if key in i:
                    for j in range(len(a)):
                        var[j] = float(a[j])

            if "fs" in i:
                self.pr_dev.feed = float(a[0])
                self.pr_dev.spindle = float(a[1])
            elif "bf" in i:
                self.pr_dev.buffer = int(a[0])
                self.pr_dev.bufwer = int(a[1])

    def modes(self, code):
        """Mode Group"""
        for c in code.upper().split():
            for key, var in (("motion_mode", ("G0", "G1", "G2", "G3", "G38.2", "G38.3", "G38.4", "G38.5", "G80")),
                             ("coordinate_system", ("G54", "G55", "G56", "G57", "G58", "G59")),
                             ("plane", ("G17", "G18", "G19")),
                             ("distance_mode", ("G90", "G91")),
                             ("arc_ijk_distance", ["G91.1"]),
                             ("feed_rate_mode", ("G93", "G94")),
                             ("units_mode", ("G20", "G21")),
                             ("cutter_radius_compensation", ["G40"]),
                             ("tool_length_offset", ("G43.1", "G49")),
                             ("program_mode", ("M0", "M1", "M2", "M30")),
                             ("spindle_state", ("M3", "M4", "M5")),
                             ("coolant_state", ("M7", "M8", "M9")),
                             ):
                vars = {}

                exec(f"eq = self.pr_dev.{key} == c", {"self": self, "c": c}, vars)

                if c in var and not vars["eq"]:
                    exec(f"self.pr_dev.{key} = c", {"self": self, "c": c}, {})

            if c.startswith("S"):
                self.pr_dev.saved_spindle = float(c[1:])

            elif c.startswith("F"):
                self.pr_dev.saved_feed = float(c[1:])


class NCNC_OT_Communication(Operator):
    bl_idname = "ncnc.communication"
    bl_label = "Communication"
    bl_description = "Communication Description"
    bl_options = {'REGISTER'}

    # Sent Mode (only_read)
    #   0.0: Hardly -> Read
    #   0.1: Hardly -> Write
    #   1.0: Public -> Read
    #   1.1: Public -> Write
    #   2.0: Hidden -> Read
    #   2.1: Hidden -> Write
    sent = 0

    pr_con = None
    pr_com = None
    pr_dev = None

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
        # ####################################
        # ####################################

        # bpy.app.driver_namespace[self.bl_idname] = self

        self.pr_dev = context.scene.ncnc_pr_machine
        self.pr_con = context.scene.ncnc_pr_connection
        self.pr_com = context.scene.ncnc_pr_communication

        context.window_manager.modal_handler_add(self)

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

        if not self.pr_con.isconnected:
            unregister_modal(self)
            return self.timer_remove(context)
        # ####################################
        # ####################################

        self.delay = self.contact()

        return {'PASS_THROUGH'}

    def contact(self):
        """return: delay ms -> float"""
        pr_com = self.pr_com
        pr_dev = self.pr_dev

        # READ HARDLY
        if self.sent == 0.0:
            for i in self.read().strip().split("\n"):
                c = i.strip()
                if not c:
                    continue
                item = pr_com.items.add()
                item.ingoing = True
                item.message = c
                pr_com.active_item_index = len(pr_com.items) - 1
                pr_com.answers.append(c)

            self.sent = 3.1
            # print("READ HARDLY", c)

        # READ PUBLIC
        elif self.sent == 1.0:
            for i in self.read().strip().split("\n"):
                c = i.strip()
                if not c:
                    continue
                item = pr_com.items.add()
                item.ingoing = True
                item.message = c
                pr_com.active_item_index = len(pr_com.items) - 1
                pr_com.answers.append(c)

            # One visible code has been sent and read. The queue is in one hidden code.
            self.sent = 2.1

        # READ HIDDEN
        elif self.sent == 2.0:
            c = [i.strip() for i in self.read().strip().split("\n")]
            pr_com.answers.extend(c)

            self.sent = 1.1
            # print("READ HIDDEN", c)

        #############
        # SEND HARDLY
        if len(pr_com.queue_list_hardly):
            code = pr_com.queue_list_hardly.pop(0)
            gi = self.send(code)

            item = pr_com.items.add()
            item.ingoing = False
            item.message = gi
            pr_com.active_item_index = len(pr_com.items) - 1

            self.sent = 0.0
            # print("SEND HARDLY", code, "\n"*5)
            return .1

        if self.sent == 3.1:
            self.sent = 2.1
        elif not pr_com.isactive:
            # print("Communication Passive")
            return 0

        # SEND PUBLIC
        if self.sent == 1.1:
            if len(pr_com.queue_list) and pr_dev.buffer > 10:  # and pr_dev.bufwer > 100
                # If the buffer's remainder is greater than 10, new code can be sent.
                code = pr_com.queue_list.pop(0)
                gi = self.send(code)
                item = pr_com.items.add()
                item.ingoing = False
                item.message = gi
                pr_com.active_item_index = len(pr_com.items) - 1
                self.sent = 1.0

                # "G4 P3" -> 3 sn bekle gibi komutunu bize de uygula
                wait = re.findall('(?<!\()[Gg]0*4 *[pP](\d+\.*\d*)', code)
                if wait:
                    return float(wait[0])
                # print("SEND PUBLIC", code)
                return .2
            else:
                self.sent = 2.1

        # SEND HIDDEN
        if self.sent == 2.1:
            if len(pr_com.queue_list_hidden):
                code = pr_com.queue_list_hidden.pop(0)
                self.send(code)
                self.sent = 2.0
                # print("SEND HIDDEN", code)
                return .1  # if (pr_dev.buffer > 0) and (pr_dev.bufwer > 100) else 1
            else:
                self.sent = 1.1

        return 0

    @classmethod
    def send(cls, msg=None):
        if not dev_get():
            return
        if not msg:
            msg = "$$"  # Texinput here

        if msg.startswith("0x") or msg.startswith("0X"):
            code = bytearray.fromhex(msg[2:])  # int(msg[2:], 16)
            dev_get().write(code)
            return msg

        msg = msg.translate(tr_translate).upper()
        dev_get().write(f"{msg}\n".encode("ascii"))
        return msg

    @classmethod
    def read(cls):
        if not dev_get():
            return
        a = dev_get().read_all().decode("utf-8")
        return a


class NCNC_OT_CommunicationRun(Operator):
    bl_idname = "ncnc.communicationrun"
    bl_label = "Communication Run"
    bl_description = "Communication Description"
    bl_options = {'REGISTER'}

    action: EnumProperty(
        items=[
            ("start", "Start", ""),
            ("pause", "Pause", ""),
            ("resume", "Resume", ""),
            ("stop", "Stop", "")]
    )

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        pr_com = context.scene.ncnc_pr_communication
        pr_txt = context.scene.ncnc_pr_texts.active_text

        if self.action == "start":
            if not pr_txt:
                self.report({'INFO'}, "No Selected Text")
                return {"CANCELLED"}

            for i in pr_txt.as_string().splitlines():
                x = i.strip()
                if not x:  # or (x.startswith("(") and x.endswith(")")):
                    continue
                pr_com.send_in_order(x)

            pr_com.run_mode = "start"

        elif self.action == "pause":
            bpy.ops.ncnc.machine(action="hold")
            pr_com.run_mode = "pause"

        elif self.action == "resume":
            bpy.ops.ncnc.machine(action="resume")
            pr_com.run_mode = "start"

        elif self.action == "stop":
            pr_com.run_mode = "stop"
            bpy.ops.ncnc.machine(action="reset")

        return {'FINISHED'}


class NCNC_OP_Messages(Operator):
    bl_idname = "ncnc.messages"
    bl_label = "Messages Operator"
    bl_description = "Clear Messages in the ListBox"
    bl_options = {'REGISTER'}

    action: EnumProperty(
        items=[
            ("add", "Add to message", ""),
            ("remove", "Remove to message", ""),
            ("clear", "Clear all messages", ""),
            ("clearqueu", "Clear Queu", "")]
    )

    def execute(self, context):

        pr_com = context.scene.ncnc_pr_communication

        if self.action == "add":
            print("Developing ...")

        elif self.action == "remove":
            print("Developing ...")
            pr_com.items.remove(pr_com.active_item_index)

        elif self.action == "clear":
            pr_com.items.clear()
            pr_com.active_item_index = 0

        elif self.action == "clearqueu":
            pr_com.clear_queue()

        return {'FINISHED'}

