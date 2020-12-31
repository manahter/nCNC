import bpy
from bpy.props import EnumProperty, BoolProperty, PointerProperty, CollectionProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup, Scene


class NCNC_PR_MessageItem(PropertyGroup):
    ingoing: BoolProperty(
        name="Ingoing?",
        description="Message is Ingoing / Outgoing"
    )
    message: StringProperty(
        name="Messsage?",
        description="Message"
    )

    # time = time.time()
    # incoming = StringProperty(name="Incoming", default="")

    @classmethod
    def register(cls):
        Scene.ncnc_pr_messageitem = PointerProperty(
            name="NCNC_PR_MessageItem Name",
            description="NCNC_PR_MessageItem Description",
            type=cls)

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_messageitem


class NCNC_PR_Communication(PropertyGroup):
    def get_active(self):
        return bpy.context.scene.ncnc_pr_machine.status in ("IDLE", "RUN", "JOG", "CHECK", "HOME", "")

    def run_mode_update(self, context):
        self.isrun = self.run_mode != "stop"

    items: CollectionProperty(
        type=NCNC_PR_MessageItem,
        name="Messages",
        description="All Message Items Collection"
    )
    active_item_index: IntProperty(
        name="Active Item",
        default=-1,
        description="Selected message index in Collection"
    )
    isactive: BoolProperty(
        name='Communication is Active?',
        description='İletişimi durdur veya sürdür',
        default=True,
        get=get_active
    )

    isrun: BoolProperty(default=False)

    run_mode: EnumProperty(
        items=[
            ("stop", "Stop", "Stop and end"),
            ("start", "Run", "Send to GCodes"),
            ("pause", "Pause", "Pause to Send"),
            ("resume", "Resume", "Pause to Sending"),
        ],
        name="Gcode",
        default="stop",
        update=run_mode_update
    )

    ############################################################
    # #################################################### QUEUE
    # Mesaj Kuyruğu
    queue_list = []

    ######################################
    # ############################# Hidden
    # Mesaj Kuyruğu Gizli
    queue_list_hidden = []

    # Cevap Kuyruğu Gizli
    answers = []

    def set_hidden(self, message):
        self.queue_list_hidden.append(message)
        # if len(self.queue_list_hidden) > 10:
        #    _volatile = self.queue_list_hidden[:10]
        #    self.queue_list_hidden.clear()
        #    self.queue_list_hidden.extend(_volatile)

        # print("queue_list_hidden", self.queue_list_hidden)

    def get_answer(self):
        if self.isrun and not len(self.queue_list):
            self.run_mode = "stop"

        return self.answers.pop(0) if len(self.answers) else ""

    ######################################
    # ############################# Hardly
    # Mesaj Kuyruğu zorla
    queue_list_hardly = []

    def set_hardly(self, message):
        self.queue_list_hardly.append(message)

    def clear_queue(self):
        self.queue_list.clear()
        self.queue_list_hidden.clear()

    ############################################################
    # ################################################ MESSAGING
    def update_messaging(self, context):
        if not self.messaging:
            return
        self.send_in_order(self.messaging)
        self.messaging = ""

    messaging: StringProperty(name="Outgoing Message",
                              update=update_messaging)

    ############################################################
    # ################################################## METHODS
    def send_in_order(self, msg=None):
        if not msg:
            return

        if "=" in msg and "$J" not in msg:
            self.set_hidden("$$")

        self.queue_list.append(msg)

    @classmethod
    def register(cls):
        Scene.ncnc_pr_communication = PointerProperty(
            name="NCNC_PR_Communication Name",
            description="NCNC_PR_Communication Description",
            type=cls)

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_communication