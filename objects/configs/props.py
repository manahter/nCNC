import bpy
import math
from bpy.props import (
    IntProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    StringProperty,
    PointerProperty,
    FloatVectorProperty,
)
from mathutils import Vector
from bpy.types import PropertyGroup, Object
from nCNC.assets.icons import icons


class S:
    """S: Shorts"""
    PROFILE = "PROFILE"
    INNER = "INNER"
    OUTER = "OUTER"
    ONLY_INNER = "ONLY_INNER"
    ONLY_OUTER = "ONLY_OUTER"


class NCNC_PR_ObjectConfigs(PropertyGroup):
    """Configs of the object. Located on the object itself"""
    obj: PointerProperty(type=Object, name="Object")

    # runs: CollectionProperty(type=NCNC_Runs_Collection)
    runs = {}

    def im_running(self):
        if not self.runs.get(self.id_data):
            self.runs[self.id_data] = []

        self_runs = self.runs[self.id_data]

        index = len(self_runs)
        if index:
            self_runs[-1] = False
        self_runs.append(True)

        # Reset values
        self.gcode = ""
        self.loading = 1
        self.is_updated = False
        self.min_point = (0, 0, 0)
        self.max_point = (0, 0, 0)

        return index

    def am_i_running(self, index):
        return self.runs[self.id_data][index]

    def reload_gcode(self, context=None):
        self.is_updated = True
        bpy.ops.ncnc.gcode_create(auto_call=True)

    def update_included(self, context):
        if self.included:
            if self.check_for_include(self.id_data):
                context.scene.ncnc_pr_objects.add_item(self.id_data)

                tip = self.id_data.type

                if tip == "CURVE":
                    self.milling_strategy = S.PROFILE
                elif tip == "FONT":
                    self.milling_strategy = S.INNER
                elif tip == "MESH":
                    self.milling_strategy = S.OUTER

                self.reload_gcode(context)
            else:
                self.included = False
        else:
            context.scene.ncnc_pr_objects.remove_item(self.id_data)

    included: BoolProperty(
        name="Included",
        default=False,
        description="Include in CNC machining?",
        update=update_included
    )
    plane: EnumProperty(
        name="Working Plane Selector",
        description="Select Plane (Under development. Doesn't work yet)",
        update=reload_gcode,
        items=[("G17", "XY", "G17: Work in XY Plane"),
               ("G18", "XZ", "G18: Work in XZ Plane"),
               ("G19", "YZ", "G19: Work in YZ Plane"),
               ("G17", "XYZ", "Under development (Doesn't work with GRBL v1.1)"),
               ]
    )
    ##############################################################################
    # ########################################################## create self gcode
    gcode: StringProperty(
        name="G-code",
        description="G-code as string",
        # update=
    )
    loading: IntProperty(
        name="Loading...",
        subtype="PERCENTAGE",
        default=0,
        min=0,
        max=100
    )

    min_point: FloatVectorProperty(name="Minimum Point", default=[0, 0, 0], subtype="XYZ")
    max_point: FloatVectorProperty(name="Maximum Point", default=[0, 0, 0], subtype="XYZ")

    last_loc: FloatVectorProperty(default=[0, 0, 0], subtype="XYZ")
    last_rot: FloatVectorProperty(default=[0, 0, 0], subtype="XYZ")
    last_sca: FloatVectorProperty(default=[0, 0, 0], subtype="XYZ")
    is_updated: BoolProperty()

    ##############################################################################
    ##############################################################################
    safe_z: FloatProperty(
        name="Safe Z",
        default=5,
        # unit="LENGTH",
        description="Safe Z position (default:5)",
        update=reload_gcode
    )
    step: FloatProperty(
        name="Step Z",
        min=.1,
        default=0.5,
        # unit="LENGTH",
        description="Z Machining depth in one step",
        update=reload_gcode
    )
    depth: FloatProperty(
        name="Total Depth",
        default=1,
        min=0,
        # unit="LENGTH",
        description="Son işleme derinliği",
        update=reload_gcode
    )

    ##############################################################################
    ##############################################################################
    feed: IntProperty(
        name="Feed Rate (mm/min)",
        default=60,
        min=30,
        description="Feed rate is the velocity at which the cutter is fed, that is, advanced against "
                    "the workpiece. It is expressed in units of distance per revolution for turning and "
                    "boring (typically inches per revolution [ipr] or millimeters per "
                    "revolution).\nDefault:200",
        update=reload_gcode
    )
    plunge: IntProperty(
        name="Plunge Rate (mm/min)",
        default=50,
        min=10,
        update=reload_gcode,
        description="Plunge rate is the speed at which the router bit is driven down into the "
                    "material when starting a cut and will vary depending on the bit used and the "
                    "material being processed. It is important not to plunge too fast as it is easy "
                    "to damage the tip of the cutter during this operation\ndefault: 100",
    )
    spindle: IntProperty(
        name="Spindle (rpm/min)",  # "Spindle Speed (rpm/min)"
        default=1000,
        min=600,
        update=reload_gcode,
        description="The spindle speed is the rotational frequency of the spindle of the machine, "
                    "measured in revolutions per minute (RPM). The preferred speed is determined by "
                    "working backward from the desired surface speed (sfm or m/min) and "
                    "incorporating the diameter (of workpiece or cutter).\nDefault:1200",
    )
    # #############################################################################
    # #############################################################################
    round_loca: IntProperty(
        name="Round (Location)",
        default=3,
        min=0,
        max=6,
        update=reload_gcode,
        description="Floating point resolution of location analysis? (default=3)\n"
                    "[0-6] = Rough analysis - Detailed analysis"
    )
    round_circ: IntProperty(
        name="Round (Circle)",
        default=1,
        min=0,
        max=6,
        update=reload_gcode,
        description="Floating point resolution of circular analysis? (default=1)\n"
                    "[0-6] = Rough analysis - Detailed analysis"
    )

    def resolution_general_set(self, value):
        if not self.id_data:
            return
        self.id_data.data.resolution_u = value
        self.is_updated = True
        # self.reload_gcode()

    def resolution_general_get(self):
        if not self.id_data:
            return
        return self.id_data.data.resolution_u

    resolution_general: IntProperty(
        name="Resolution General for Object",
        default=12,
        min=1,
        max=64,
        description="Surface Resolution in U direction",
        set=resolution_general_set,
        get=resolution_general_get
    )

    def resolution_spline_set(self, value):
        if not self.id_data:
            return
        self.id_data.data.splines.active.resolution_u = value
        self.is_updated = True
        # self.reload_gcode()

    def resolution_spline_get(self):
        if not self.id_data:
            return
        return self.id_data.data.splines.active.resolution_u

    resolution_spline: IntProperty(
        name="Resolution Spline in Object",
        default=12,
        min=1,
        max=64,
        description="Curve or Surface subdivisions per segment",
        set=resolution_spline_set,
        get=resolution_spline_get
    )

    as_line: BoolProperty(
        name="As a Line or Curve",
        update=reload_gcode,
        description="as Line: Let it consist of lines only. Don't use G2-G3 code.\n"
                    "as Curve: Use curves and lines. Use all, including G2-G3."
    )

    milling_strategy: EnumProperty(
        name="Milling Strategy",
        description="",
        update=reload_gcode,
        items=[(S.PROFILE, "Only Profile", "", icons[S.PROFILE].icon_id, 0),
               (S.INNER, "Profile and Inner Clearance", "", icons[S.INNER].icon_id, 1),
               (S.ONLY_INNER, "Only Inner Clearance", "", icons[S.ONLY_INNER].icon_id, 2),
               (S.OUTER, "Profile and Outer Clearance", "", icons[S.OUTER].icon_id, 3),
               (S.ONLY_OUTER, "Only Outer Clearance", "", icons[S.ONLY_OUTER].icon_id, 4),
               ],
    )

    # veya
    # scraping_range   -> Kazıma Aralığı
    # carving_range    -> Oyma Aralığı          -> Burayı değiştirip "Stepover"
    carving_range: FloatProperty(
        name="Carving Range (mm)",
        description="The tool diameter in mm is entered",
        min=0.2,
        default=2,
        step=50,
        update=reload_gcode
    )

    carving_angle: FloatProperty(
        name="Carving Angle",
        description="Carving Angle",
        min=0,
        max=math.radians(90),
        step=500,
        default=math.radians(45),
        subtype="ANGLE",
        unit="ROTATION",
        update=reload_gcode
    )

    @property
    def carving_normal(self):
        t = math.tan(math.radians(90) - self.carving_angle)
        v = Vector((-1, t, 0))
        v.normalize()
        return v

    def check_for_include(self, obj):
        """ Checks if the object type is Curve (Bezier or Poly)"""
        if obj.type == "CURVE":
            o = []
            for i in obj.data.splines:
                o.append(i.type == "POLY" or i.type == "BEZIER")
            return False not in o
        elif obj.type in ("FONT", "MESH"):
            return True
        else:
            return False

    @classmethod
    def register(cls):
        Object.ncnc_pr_objectconfigs = PointerProperty(
            name="NCNC_PR_ObjectConfigs Name",
            description="NCNC_PR_ObjectConfigs Description",
            type=cls)

    @classmethod
    def unregister(cls):
        del Object.ncnc_pr_objectconfigs
