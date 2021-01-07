from bpy.props import EnumProperty, BoolProperty, PointerProperty
from bpy.types import PropertyGroup, Scene
import bpy
import time

from ...modules.serial import Serial

# USB portlarını bulur...
from ...modules.serial.tools.list_ports import comports

from .. import dev_get, dev_set


class NCNC_PR_Connection(PropertyGroup):
    """
    Only CNC Connection Panel Properties
    """

    def get_isconnected(self):
        if dev_get():
            try:
                dev_get().inWaiting()
            except:
                return False
        return True if dev_get() else False

    def set_isconnected(self, value):
        """Value : True->Connect,  False->Disconnect"""
        if dev_get():
            try:
                dev_get().close()
            except:
                ...
            dev_set(None)

        if value:
            try:
                s = Serial(self.ports, self.bauds)
                s.write("\r\n\r\n".encode("ascii"))
                time.sleep(.1)
                s.flushInput()
                dev_set(s)
            except:
                ...

            bpy.ops.ncnc.communication(start=True)
        else:
            bpy.ops.ncnc.communication(start=False)

    def get_ports(self, context):
        return [(i.device, str(i), i.name) for i in comports()]

    isconnected: BoolProperty(
        name="IsConnected",
        description="Is Connected ?",
        default=False,
        get=get_isconnected,
        set=set_isconnected
    )
    ports: EnumProperty(
        name="Select Machine",
        description="Select the machine you want to connect",
        items=get_ports
    )
    bauds: EnumProperty(
        items=[("2400", "2400", ""),
               ("4800", "4800", ""),
               ("9600", "9600", ""),
               ("19200", "19200", ""),
               ("38400", "38400", ""),
               ("57600", "57600", ""),
               ("115200", "115200", ""),
               ("230400", "230400", "")
               ],
        name="Select Baud",
        description="Select the machine you want to connect",
        default="115200"
    )
    controller: EnumProperty(
        items=[("GRBL", "GRBL v1.1 (Tested)", "")],
        name="Controller",
        description="Under development...",
        default="GRBL"
    )

    @classmethod
    def register(cls):
        Scene.ncnc_pr_connection = PointerProperty(
            name="NCNC_PR_Connection Name",
            description="NCNC_PR_Connection Description",
            type=cls
        )

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_connection
