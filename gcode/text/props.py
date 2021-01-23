import re
import bpy
import math
import bmesh
from mathutils import Vector
from mathutils.geometry import intersect_sphere_sphere_2d
from bpy.props import (
    IntProperty,
    BoolProperty,
    FloatProperty,
    StringProperty,
    PointerProperty,
    CollectionProperty,
    FloatVectorProperty
)
from bpy.types import PropertyGroup, Text


class NCNC_PR_Lines(PropertyGroup):
    co: FloatVectorProperty()


class NCNC_PR_TextLine(PropertyGroup):
    lines: CollectionProperty(type=NCNC_PR_Lines)
    index: IntProperty()
    ismove: BoolProperty(default=False)

    code_full: StringProperty()
    code: StringProperty()
    comment: StringProperty()

    mode_distance: IntProperty(default=90)
    mode_plane: IntProperty(default=17)
    mode_units: IntProperty(default=21)
    mode_move: IntProperty(default=0)

    xyz_in_code: FloatVectorProperty()
    ijk_in_code: FloatVectorProperty()

    xyz: FloatVectorProperty()
    ijk: FloatVectorProperty()

    r: FloatProperty()
    f: FloatProperty()

    length: FloatProperty(default=0)
    pause: FloatProperty(default=0)
    error: BoolProperty(default=False)

    def get_estimated_time(self):
        f = 500 if self.mode_move == 0 else self.f
        return (self.length / (f * (1 if self.mode_units == 21 else 25.4))) * 60

    estimated_time: FloatProperty(get=get_estimated_time)

    def load(self, value: str):
        ismove_xyz = False
        ismove_ijk = False
        ismove_r = False

        self.code_full = value
        self.prev_line = self.id_data.ncnc_pr_text.lines[self.index - 1]

        # ###############################################
        # ####################################### Comment
        for i in re.findall(r'\([^()]*\)', value):
            self.comment += i
            value = value.replace(i, "")

        # ###############################################
        # ########################################  G0-3
        value = value.upper()
        self.code = value

        for rex, key in [(r'G *(9[01])(?:\D|$)', "mode_distance"),
                         (r'G *(1[7-9])(?:\D|$)', "mode_plane"),
                         (r'G *(2[01])(?:\D|$)', "mode_units"),
                         (r'G *(0?[0-3])(?:\D|$)', "mode_move"),
                         ]:
            fn = re.findall(rex, value)
            exec(f"self.{key} = int(fn[0]) if {len(fn) == 1} else self.prev_line.{key}")

        if self.prev_line:
            self.xyz = self.prev_line.xyz

        # ###############################################
        # ################################ X0.0 Y0.0 Z0.0
        for j, v in enumerate("XYZ"):
            ps = re.findall(f'{v} *([+-]?\d*\.?\d*)', value)
            if len(ps) == 1 and re.sub("[+-.]", "", ps[0]).isdigit():
                ismove_xyz = True
                self.xyz_in_code[j] = float(ps[0])
                self.xyz[j] = float(ps[0]) + (self.xyz[j] if self.mode_distance == 91 else 0)
                self.xyz[j] *= (1 if self.mode_units == 21 else 25.4)

        # ###############################################
        # ################################ I0.0 J0.0 K0.0
        for j, v in enumerate("IJK"):
            ps = re.findall(f'{v} *([+-]?\d*\.?\d*)', value)
            if len(ps) == 1 and re.sub("[+-.]", "", ps[0]).isdigit():
                ismove_ijk = True
                self.ijk_in_code[j] = float(ps[0])
                self.ijk[j] = float(ps[0]) * (1 if self.mode_units == 21 else 25.4)

        # ###############################################
        # ############################################# F

        ps = re.findall('F *([+]?\d*\.?\d*)', value)
        if len(ps) == 1 and re.sub("[+.]", "", ps[0]).isdigit():
            self.f = float(ps[0])
        else:
            self.f = self.prev_line.f

        ps = re.findall('R *([+-]?\d*\.?\d*)', value)
        if len(ps) == 1 and re.sub("[+-.]", "", ps[0]).isdigit():
            ismove_r = True
            self.r = float(ps[0]) * (1 if self.mode_units == 21 else 25.4)
            if ismove_ijk:
                self.error = True

        # ###############################################
        # ######################################## PAUSE
        ps = re.findall('G4 *P([+]?\d*\.?\d*)', value)
        if len(ps) == 1 and re.sub("[+.]", "", ps[0]).isdigit():
            self.pause = float(ps[0])

        if (ismove_xyz and self.mode_move in (0, 1)) or (ismove_xyz and ismove_ijk) or (ismove_xyz and ismove_r):
            self.ismove = True

        if self.ismove and not self.error:
            for i in self.calc_lines():
                a = self.lines.add()
                a.co = i

        if self.error:
            self.mode_distance = self.prev_line.mode_distance
            self.mode_plane = self.prev_line.mode_plane
            self.mode_units = self.prev_line.mode_units
            self.mode_move = self.prev_line.mode_move
            self.xyz = self.prev_line.xyz
            self.ismove = False
            self.f = self.prev_line.f
        return

    def calc_lines(self, step: int = 0):
        """For this item"""
        mv = self.mode_move
        prev_xyz = Vector(self.prev_line.xyz)
        xyz = Vector(self.xyz)

        # G0 - G1 için;
        if mv in (0, 1):
            self.length = (prev_xyz - xyz).length
            return prev_xyz, xyz

        # Buradan sonrası, G2 - G3 - I J K R için
        # If the R code is used, we must convert the R code to IJK
        # +R: Short angle way
        # -R: Long angle way
        if self.r:
            # Reference:
            # https://docs.blender.org/api/current/mathutils.geometry.html?highlight=intersect_sphere_sphere_2d#mathutils.geometry.intersect_sphere_sphere_2d

            r = abs(self.r)
            distance = round((xyz - prev_xyz).length / 2, 3)

            # Distance greater than diameter
            if distance > round(r, 3):
                self.error = True
                return []

            # Distance equal to diameter
            elif distance == round(r, 3):
                ijk = (xyz + prev_xyz) / 2

            # Distance smaller than diameter
            else:
                intersects = intersect_sphere_sphere_2d(prev_xyz[:2], r, xyz[:2], r)

                if mv == 3:
                    ijk = intersects[self.r > 0]
                else:
                    ijk = intersects[self.r < 0]

                ijk = Vector((*ijk[:], 0))

            ijk = ijk - prev_xyz
        else:
            ijk = Vector(self.ijk)

        center = prev_xyz + ijk

        bm = bmesh.new()

        # Uyarı Buradan sonrası G17 düzlemi için hesaplanmıştır.
        # Diğer düzlemler için düzenlemek kolay.
        # Farkettiysen, Vektörlerin Z'lerinin yerine 0 yazdık.
        # Oraları düzenleyerek diğer düzlemler için uygulayabilirsin.

        # From the CENTER to the CURRENT POINT
        v1 = prev_xyz - center
        v1.z = 0

        # From the CENTER to the POINT of DESTINATION
        v2 = xyz - center
        v2.z = 0

        try:
            if abs(v1.length - v2.length) > 0.01:
                raise Exception

            # Angle between V1 and V2 (RADIANS)
            angle = v1.angle(v2)
        except:
            self.error = True
            return []

        cross = v1.cross(v2).z
        if cross > 0 and mv == 2:
            angle = math.radians(360) - angle
        elif cross < 0 and mv == 3:
            angle = math.radians(360) - angle
        elif cross == 0:
            if self.r or v1.x == v2.x or v1.y == v2.y:
                angle = math.radians(180)
            else:
                angle = math.radians(360)
        self.length = angle * v1.length

        # Angle between V1 and V2 (DEGREES)
        angle_degrees = math.degrees(angle)

        if step:
            pass
        elif v1.length < 10:
            step = math.ceil(angle_degrees / 10)
        elif v1.length < 50:
            step = math.ceil(angle_degrees / 5)
        else:
            step = math.ceil(angle_degrees / 2)

        # ####### !!!
        # Bu kısımda axis'i güncelle ileride
        # Çünkü, G17, G18 vs düzlemine göre axis değişir
        bmesh.ops.spin(bm,
                       geom=[bm.verts.new(prev_xyz)],
                       axis=(0, 0, (1 if mv == 2 else -1)),
                       # axis=(.7, 0, (1 if mv == 2 else -1)),
                       steps=step,
                       angle=-angle,
                       cent=center
                       )
        # print("\n"*2)
        # print("Prev :", prev_xyz)
        # print("XYZ :", xyz)
        # print("IJK :", ijk)
        # print("Center :", center)
        # print("Vector1 :", v1)
        # print("Vector2 :", v2)
        # print("Angle :", angle)
        # print("Degrees", angle_degrees)
        # print("Cross :", v1.cross(v2))
        # print("Dot :", round(v1.dot(v2), 3))

        lines = []

        z_step = (xyz.z - prev_xyz.z) / step if step else 0

        for n, t in enumerate(bm.verts):
            x = round(t.co.x, 3)
            y = round(t.co.y, 3)
            z = round(t.co.z + n * z_step, 3)

            lines.append((prev_xyz.x, prev_xyz.y, prev_xyz.z))
            prev_xyz.x = x
            prev_xyz.y = y
            prev_xyz.z = z
            lines.append((prev_xyz.x, prev_xyz.y, prev_xyz.z))

        return lines


class NCNC_PR_Text(PropertyGroup):
    # Modals, stop, run ...
    isrun = []

    event: BoolProperty(default=False)
    event_selected: BoolProperty(default=False)

    last_cur_index: IntProperty()
    last_end_index: IntProperty()

    lines: CollectionProperty(
        type=NCNC_PR_TextLine,
        name="Objects",
        description="All Object Items Collection",
    )

    # Total Line
    count: IntProperty()

    # Milimeters
    distance_to_travel: FloatProperty()

    # Seconds
    estimated_time: FloatProperty()

    minimum: FloatVectorProperty()
    maximum: FloatVectorProperty()

    def event_control(self):
        cur_ind = self.id_data.current_line_index + 1
        end_ind = self.id_data.select_end_line_index + 1

        cur_ind, end_ind = min(cur_ind, end_ind), max(cur_ind, end_ind) + 1
        if cur_ind != self.last_cur_index or end_ind != self.last_end_index:
            self.last_cur_index = cur_ind
            self.last_end_index = end_ind
            self.event_selected = True

        self.load()

    def get_points(self):
        return [c.xyz for c in self.lines if c.ismove]

    def get_lines(self, move_mode=0):
        self.event = False
        lines = []
        for c in self.lines:
            if c.ismove and (c.mode_move == move_mode):
                lines.extend([i.co[:] for i in c.lines])

        return lines

    def get_selected(self):
        self.event_selected = False
        if self.isrun and self.isrun[-1]:
            return []

        count = len(self.lines)

        if count >= self.last_end_index > self.last_cur_index:
            lines = []
            for i in range(self.last_cur_index, self.last_end_index):
                line = self.lines[i]
                if line.ismove:
                    lines.extend([i.co[:] for i in line.lines])
            return lines

        return [(0, 0, 0), (0, 0, 0)]

    def load(self):
        if not self.ismodified:
            return

        count = len(self.isrun)
        if count:
            self.isrun[-1] = False

        self.isrun.append(True)

        # ####################
        # Before Reset to vars
        self.lines.clear()
        self.count = 0
        self.distance_to_travel = 0
        self.estimated_time = 0
        self.minimum = (0, 0, 0)
        self.maximum = (0, 0, 0)

        bpy.ops.ncnc.gcode(text_name=self.id_data.name, run_index=count)
        self.prev_str = self.id_data.as_string()

    prev_str: StringProperty()

    def get_ismodified(self):
        return self.id_data.as_string() != self.prev_str

    ismodified: BoolProperty(get=get_ismodified)

    @classmethod
    def register(cls):
        Text.ncnc_pr_text = PointerProperty(
            name="NCNC_PR_Text Name",
            description="NCNC_PR_Text Description",
            type=cls)

    @classmethod
    def unregister(cls):
        del Text.ncnc_pr_text
