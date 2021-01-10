import time
import bpy
import math
import bmesh

from bpy.types import Operator
from mathutils import Matrix, Vector
from mathutils.geometry import intersect_line_line_2d
from bpy.props import StringProperty, FloatProperty, IntProperty, FloatVectorProperty

from ..utils.nVector import nVector
from ..utils import nCompute
from ..objects.configs.props import S

# TODO !!!
#   Text için; Eğer 3D şekil verildiyse, 3D olarak al. Değilse, Eğri olarak al
#


def deep_remove_to_object(obj):
    obj.to_mesh_clear()
    _data = obj.data
    _type = obj.type
    bpy.data.objects.remove(obj)
    if _type in ("FONT", "CURVE"):
        bpy.data.curves.remove(_data)
    elif _type == "MESH":
        bpy.data.meshes.remove(_data)
    else:
        print("Temizleyemedik")


def get_data_text_object(context, obj):
    """Text object convert to curve and return Curve data"""
    last_active_obj = context.active_object

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    context.view_layer.objects.active = obj

    before_all_objects = bpy.data.objects[:]

    bpy.ops.object.convert(target="CURVE", keep_original=True)

    diff = set(bpy.data.objects[:]) - set(before_all_objects)

    if len(diff):
        new_obj = diff.pop()
        data = new_obj.data.copy()
        deep_remove_to_object(new_obj)
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = last_active_obj
        return data


def biless(data, bilesen):
    """Vertexleri birleştirir"""

    # Birleşendeki son Vertexi alıyoruz ve datadan o vertex bağlı diğerlerini alıyoruz.
    _verts = data[bilesen[-1].index].copy()

    # Vertexleri aldık içini temizleyelim.
    data[bilesen[-1].index].clear()

    # Bitir, 3 taneden az vertex varsa, bilesen 2 taneden az ise, vertexlerin hepsi zaten birlesende varsa
    if (len(_verts) < 3) or (len(bilesen) < 2) or len(set(_verts) - set(bilesen)) < 1:
        return bilesen

    # Vertexlerdeki son
    if bilesen[-2] != _verts[0]:
        _verts.reverse()

    bilesen = biless(data, bilesen[:-2] + _verts)
    bilesen.reverse()
    return biless(data, bilesen)


def dilimle(data, min_z, max_z, step_z):
    bm = bmesh.new()
    bm.from_mesh(data)

    step = max_z - step_z

    curves = []
    while step > min_z:
        # BMesh'ten Z ekseninde bir kesit alınır
        cut = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=0,
                                     plane_co=Vector((0, 0, step)),
                                     plane_no=Vector((0, 0, 1)),
                                     # clear_inner=True
                                     )["geom_cut"]

        step -= step_z
        if step < min_z:
            step = min_z

        # Sadece Edge'leri al ve sırala
        # cut = sorted([e for e in cut if isinstance(e, bmesh.types.BMEdge)], key=lambda e: e.index)
        # cut = [e for e in cut if isinstance(e, bmesh.types.BMEdge) and not print(e)]
        cut = [e for e in cut if isinstance(e, bmesh.types.BMEdge)]

        # Vertexleri indexlere ayır
        # {ind: [Edge1, Edge2], ind: [Edge1, Edge2]}
        inds = {}
        for e in cut:
            for ind in [e.verts[0].index, e.verts[1].index]:
                if ind in inds:
                    # Önceki eklenen edge ile şimdi eklenen edge vertexlerini birleştir.
                    verts = (*inds[ind], *e.verts[:])
                    mid = max(verts, key=verts.count)
                    vts = list(set(verts))
                    vts.remove(mid)
                    inds[ind] = [vts[0], mid, vts[1]]
                else:
                    inds[ind] = e.verts[:]

        # print("indexes", *inds.values(), sep="\n")
        polys = []
        for ind, verts in inds.items():
            if len(verts) < 3:
                verts.clear()
                continue

            polys.append(biless(inds, verts))

        # Noktalardan Spline oluştur
        if polys:
            # Eğri oluşturulur
            curve = bpy.data.curves.new("nLink", 'CURVE')
            curve.dimensions = '3D'
            # Spline oluşturulur
            for poly in polys:
                if len(poly) < 2:
                    continue
                spline = curve.splines.new("POLY")
                spline.use_cyclic_u = True
                spline.points[0].co.xyz = poly[0].co.xyz
                for v in poly[1:]:
                    spline.points.add(1)
                    spline.points[-1].co.xyz = v.co.xyz

            curves.append(curve)
    return curves


class NCNC_OT_GCodeConvert(Operator):
    bl_idname = "ncnc.gcode_convert"
    bl_label = "Convert"
    bl_description = "Convert object to Gcode"
    bl_options = {'REGISTER', 'UNDO'}
    # bl_options = {'REGISTER'}

    obj_name: StringProperty()
    obj_orj = None
    obj = None
    conf = None
    run_index = 0

    code_str: StringProperty()

    delay = .1
    _last_time = 0

    safe_z = None
    first_z: FloatProperty()
    block: IntProperty(default=0)
    index_spline: IntProperty(default=0)
    index_dongu: IntProperty(default=0)
    index_curve: IntProperty(default=0)

    # Usually used for the Z value
    step_vector: FloatVectorProperty(default=[0, 0, 0], subtype="XYZ")

    curve_list = []

    # !!! use for 3D references:
    # https://docs.blender.org/api/current/bmesh.ops.html?highlight=bisect#bmesh.ops.bisect_plane

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        if not self.obj_name:
            return {'CANCELLED'}

        # Aktif obje Edit moddaysa, obje moduna çeviriyoruz ki işlem yapabilelim
        if context.active_object and context.active_object.mode == "EDIT":
            bpy.ops.object.editmode_toggle()

        # İşlenecek kütüğü alıyoruz.
        stock = context.scene.ncnc_pr_objects.stock

        # Hedef Obje alınır
        obj_orj = bpy.data.objects[self.obj_name]

        # Eğer Yazı ise, objenin datası Curve'ye çevrilerek alınır
        if obj_orj.type == "FONT":
            obj = obj_orj.copy()
            obj.data = get_data_text_object(context, obj_orj)
            if not obj.data:
                return {'CANCELLED'}

        # Curve ise veya kütük yok ise direkt kopyala
        elif obj_orj.type == "CURVE" or not stock:
            obj = obj_orj.copy()
            obj.data = obj.data.copy()

        # Eğer Mesh ise ve kütük var ise kütükten çıkart
        else:
            # Kütüğün kopyasını oluşturuyoruz
            obj = stock.copy()

            # Hedef objeyi modifier uygulayarak kütükten çıkartıyoruz.
            mod_bool = stock.modifiers.new('my_bool_mod', 'BOOLEAN')
            mod_bool.operation = 'DIFFERENCE'
            mod_bool.object = obj_orj

            # Grafiklerden modifiye edilmiş objeyi alıyoruz.
            depsgraph = bpy.context.evaluated_depsgraph_get()
            object_eval = stock.evaluated_get(depsgraph)

            # Oluşan objenin datasını kopyalıyoruz
            obj.data = bpy.data.meshes.new_from_object(object_eval)

            # Orjinal Kütüğe şimdi eklediğimiz modifierleri temizliyoruz ki sonradan sorun çıkmasın
            stock.modifiers.clear()

        conf = obj_orj.ncnc_pr_objectconfigs
        conf.is_updated = False

        # Şuan bu obje Convert işleminde olduğunu belirtmek için bayrak çekiyoruz
        # Report: self is running
        self.run_index = conf.im_running()

        # Bu aşamada olay takibini durduruyoruz. (Sadece bu kopyalanmış obje için)
        # Copy object confs
        obj.ncnc_pr_objectconfigs.included = False
        obj.ncnc_pr_objectconfigs.is_updated = False

        self.conf = conf

        # self.safe_z = None
        self.codes = ""
        self.block = 0
        self.dongu = []
        self.dongu.clear()
        self.index_spline = 0
        self.index_dongu = 0
        self.index_curve = 0
        ##########################################
        ##########################################

        # Eğrilerde 2D'de hata çıkabildiği için, 3D'ye alıyoruz -> transform_apply( .. ) -> Gerekli mi tekrar kontrol et
        if obj.type in ("CURVE", "FONT"):
            obj.data.dimensions = "3D"

        # Objenin boyutlarını uyguluyoruz.
        obj.data.transform(obj.matrix_world)
        obj.matrix_world = Matrix()
        self.obj = obj

        # Mesh'e dönüştürüp, Z'de uç noktaları buluyoruz
        mesh = obj.to_mesh()
        verts = [v.co.z for v in obj.to_mesh().vertices]
        self.max_z = max(verts)
        self.min_z = min(verts)

        # Oluşan mesh'i temizliyoruz
        # obj.to_mesh_clear()

        ##########################################
        ##########################################

        if obj.type == "MESH":
            # Mesh dilimlenip, Curvelere dönüştürülür ve koleksiyonlanır.
            # for i in dilimle(mesh, self.min_z, self.max_z, conf.step):
            #     curve = self.curve_list.add()
            #     curve.obj = i
            # self.curve_list = dilimle(obj.data, self.min_z, self.max_z, conf.step)
            self.curve_list = dilimle(obj.data.copy(), self.min_z, self.max_z, conf.step)

            # conf.depth = conf.step
        # TODO !!! işte Mesh objeyi tam burada z ekseninde dilimleyeceğiz ve dilimleri poly'ye çevireceğiz.

        # Z adımı, derinlikten büyükse veya spline yoksa işlemi bitir
        elif conf.step > conf.depth or not len(self.obj.data.splines):
            return self.timer_remove(context, only_object=True)

        print("Min / Max", self.min_z, self.max_z)

        # Steps in the Z axis -> 0.5, 1.0, 1.5, 2.0 ...
        self.dongu.extend([i * conf.step for i in range(1, int(conf.depth / conf.step + 1), )])

        ##########################################
        ##########################################
        # Calculate last Z step
        if conf.depth % conf.step > 0.01:
            if len(self.dongu):
                self.dongu.append(round(self.dongu[-1] + conf.depth % conf.step, conf.round_loca))
            else:
                self.dongu.append(round(self.dongu[-1], conf.round_loca))

        # Create initial configs of the shape -> Block x
        self.add_block(expand="1", enable="1")
        self.code = f"{conf.plane} ( Plane Axis )"
        self.code = f"S{conf.spindle} ( Spindle )"
        self.code = f"( Safe Z : {conf.safe_z} )"
        self.code = f"( Step Z : {conf.step} )"
        self.code = f"( Total depth : {round(conf.depth, 3) if obj.type != 'MESH' else self.min_z} )"
        self.code = f"( Feed Rate -mm/min- : {conf.feed} )"
        self.code = f"( Plunge Rate -mm/min- : {conf.plunge} )"

        ##########################################
        ##########################################

        context.window_manager.modal_handler_add(self)
        return self.timer_add(context)

    def timer_add(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(self.delay, window=context.window)
        return {"RUNNING_MODAL"}

    def timer_remove(self, context, only_object=False):
        if not only_object:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)

        self.conf.loading = 0

        return {'CANCELLED'}

    def modal(self, context, event):
        if time.time() - self._last_time < self.delay or event.type != 'TIMER':
            return {'PASS_THROUGH'}

        self._last_time = time.time()

        if not self.conf or not self.conf.am_i_running(self.run_index):
            return self.timer_remove(context)

        ##################################################
        ##################################################
        # Necessary calculations have been made
        # Gcode can now be creating for object

        # TODO !!! Düzelt. Buradan dongu sayısına göre hangi sırada olduğumuz ve hangi Curve'de kaldığımızı alıyoruz
        len_curves = len(self.curve_list)
        if len_curves:
            splines = self.curve_list[self.index_curve].splines
            rate_curve = 1 / len_curves
        else:
            splines = self.obj.data.splines
            rate_curve = 1

        # TODO !!! Düzelt
        rate_spline = (1 / len(splines)) * rate_curve
        self.conf.loading = max(100 * (rate_curve * self.index_curve + rate_spline * self.index_spline), 1)

        # Curve altındaki tüm Spline'ları sırayla al
        for i, subcurve in enumerate(splines[self.index_spline:], start=self.index_spline + 1):

            # Add new block header
            if self.index_dongu == 0:
                self.block += 1
                self.add_block(expand="0", enable="1")

            curvetype = subcurve.type

            # Convert Outline
            for j, k in enumerate(self.dongu[self.index_dongu:], start=self.index_dongu + 1):

                rate_dongu = (1 / len(self.dongu)) * rate_spline
                self.conf.loading += max(rate_dongu * self.index_dongu * 100, 1)
                if not len_curves:
                    self.step_vector.z = k

                if curvetype == 'NURBS':
                    # Yapım aşamasında !!!
                    ...

                # Poly tipindeki Spline'ı convert et
                elif curvetype == 'POLY':
                    self.poly(subcurve)

                # Bezier tipindeki Spline'ı convert et
                elif curvetype == 'BEZIER':
                    self.bezier(subcurve, reverse=j % 2 is 1)

                self.index_dongu += 1

                if context.area:
                    context.area.tag_redraw()

                return {'PASS_THROUGH'}

            self.index_dongu = 0
            self.index_spline += 1
            return {'PASS_THROUGH'}

        if len_curves:
            self.index_curve += 1
            if len_curves > self.index_curve:
                self.index_spline = 0
                self.index_dongu = 0
                return {'PASS_THROUGH'}

        if self.conf.milling_strategy in (S.INNER, S.ONLY_INNER):
            self.clearance_zigzag()

        return self.finished(context)

    def finished(self, context):
        self.conf.loading = 0
        self.conf.gcode = self.codes

        self.report({"INFO"}, f"Converted {self.obj_name}")

        deep_remove_to_object(self.obj)
        return self.timer_remove(context)

    def add_block(self, name=None, expand="0", enable="1", description=""):
        self.code = f"\n(Block-name: {name or self.obj_name}-{self.block})"
        self.code = f"(Block-expand: {expand})"
        self.code = f"(Block-enable: {enable})"

    @property
    def code(self):
        return self.codes

    @code.setter
    def code(self, value):
        self.codes += value + "\n"

    def roll(self, **kwargs):
        """Round Location"""
        key, val = kwargs.popitem()

        val = round(val, self.conf.round_loca)

        if key in "xyz":
            no = "xyz".find(key)
            self.conf.min_point[no] = min(self.conf.min_point[no], val)
            self.conf.max_point[no] = max(self.conf.max_point[no], val)

        return val

    def bezier(self, subcurve, reverse=False):
        conf = self.conf
        point_count = len(subcurve.bezier_points) - (0 if subcurve.use_cyclic_u else 1)
        point_list = []

        #####################################
        # Points on the curve are calculated.
        # Query is made with 3 values taken between M1 and m2 (start and end) points.
        # This m1, m2 and the other 3 values;
        #   * On Circle ?
        #   * On Line ?
        # To create more efficient code, points are optimize.

        for j in range(point_count):
            cycle_point = j == point_count - 1 and subcurve.use_cyclic_u

            # last point
            lp = 0 if cycle_point else j + 1

            # Point Head
            m1 = subcurve.bezier_points[j].co - self.step_vector

            hr = subcurve.bezier_points[j].handle_right - self.step_vector
            hl = subcurve.bezier_points[lp].handle_left - self.step_vector

            # Point End
            m2 = subcurve.bezier_points[lp].co - self.step_vector

            ask_center = []
            ask_line = []

            # Ask these ratios between the two points.
            for i in [0.25, 0.5, 0.75]:
                ps = nVector.bul_bezier_nokta_4p1t(i, m1, hr, hl, m2)
                ask_center.append(nVector.yuvarla_vector(conf.round_circ, nCompute.circle_center(m1, ps, m2)))
                ask_line.append(nVector.bul_dogru_uzerindemi_3p(m1, m2, ps))

            # If Line
            if all(ask_line):
                if j == 0:
                    point_list.append(m1)
                point_list.append(nVector.bul_dogrunun_ortasi_2p(m1, m2))
                point_list.append(m2)

            # If Circle
            elif not conf.as_line and ask_center[0] == ask_center[1] == ask_center[2]:
                if j == 0:
                    point_list.append(m1)
                point_list.append(nVector.bul_bezier_nokta_4p1t(0.5, m1, hr, hl, m2))
                point_list.append(m2)

            # If you want a Line rather than a Curve
            elif conf.as_line:
                resolution = subcurve.resolution_u
                step = 1 / resolution / 2
                for i in range(resolution * 2 + 1):
                    o = nVector.bul_bezier_nokta_4p1t(step * i, m1, hr, hl, m2)
                    if i != 0 or j == 0:
                        point_list.append(o)

            # For Curve
            else:
                # Make the resolution even number
                resolution = math.ceil(subcurve.resolution_u / 2.) * 2

                # Step rate
                step = 1 / resolution

                # TODO: Bizim bezier üzerinde nokta bulma fonksiyonu yerine, var olan şuradaki fonksiyonu dene
                #  -> interpolate_bezier
                # https://behreajj.medium.com/scripting-curves-in-blender-with-python-c487097efd13

                # Find as many points as resolution along the curve
                for i in range(resolution + 1):
                    o = nVector.bul_bezier_nokta_4p1t(step * i, m1, hr, hl, m2)
                    if not j or i:
                        point_list.append(o)

        # Continue the process at the near end of the next path.
        if reverse:
            point_list.reverse()

        ##########################################
        # ############### Convert points to G code
        r = self.roll
        number_of_pieces = len(point_list) - 2

        for i in range(0, number_of_pieces, 2):
            p1 = point_list[i]
            p2 = point_list[i + 1]
            p3 = point_list[i + 2]
            m = nVector.bul_cember_merkezi_3p(p1, p2, p3, duzlem=conf.plane)

            I = m.x - p1.x if conf.plane != "G19" else 0
            J = m.y - p1.y if conf.plane != "G18" else 0
            K = m.z - p1.z if conf.plane != "G17" else 0

            # !!! For very large CNC machines, this value should be increased. ( limit: 800 )
            # G1: as line / G1: as line / Calculate G2 or G3
            b = int(conf.as_line) or int(max(abs(I), abs(J), abs(K)) > 800) or nVector.bul_yonu_1m3p(m, p1, p2, p3)

            if i == 0:
                self.starting_code(point_list)

            self.code = f"G{b} X{r(x=p3.x)} Y{r(y=p3.y)} Z{r(z=p3.z)}" + \
                        ("", f" I{r(i=I)} J{r(j=J)} K{r(k=K)}")[b > 1] + \
                        ("", f" F{conf.feed}")[i == 0]

        # self.scan_surface(subcurve)

    def poly(self, subcurve):
        conf = self.conf
        r = self.roll

        point_list = [i.co.to_3d() - self.step_vector for i in subcurve.points]

        if not point_list:
            return

        for i, p in enumerate(point_list):

            loc = p  # p.co.to_3d() - self.step_vector

            if i == 0:
                self.starting_code(point_list)
                # elf.code = f"G0 Z{r(z=z_safe)}"
                # elf.code = f"G0 X{r(x=loc.x)} Y{r(y=loc.y)}"
                # elf.code = f"G1 Z{r(z=loc.z)} F{conf.plunge}"
            else:
                self.code = f"G1 X{r(x=loc.x)} Y{r(y=loc.y)} Z{r(z=loc.z)}" + ("", f" F{conf.feed}")[i == 1]

        if subcurve.use_cyclic_u:
            loc = subcurve.points[0].co.to_3d() - self.step_vector
            self.code = f"G1 X{r(x=loc.x)} Y{r(y=loc.y)} Z{r(z=loc.z)}"

        self.code = f"G0 Z{r(z=self.safe_z)}"

        # self.scan_surface(subcurve)

    def line(self, vert0, vert1, new_line=False, first_z=None):
        r = self.roll
        # TODO: First Z'yi düzenle. Objenin tüm vertexlerinin genelinden bulsun first Z'yi
        if new_line:
            self.code = f"G0 Z{r(z=first_z or self.max_z)}"
            self.code = f"G0 X{r(x=vert0.x)} Y{r(y=vert0.y)}"
            self.code = f"G1 Z{r(z=vert0.z)}"
        # else:
        #    self.code = f"G0 X{r(x=vert0.x)} Y{r(y=vert0.y)} Z{r(z=vert0.z)}"
        self.code = f"G1 X{r(x=vert1.x)} Y{r(y=vert1.y)} Z{r(z=vert1.z)}"

    # Ref: https://b3d.interplanety.org/en/how-to-create-mesh-through-the-blender-python-api/
    def clearance_zigzag(self):
        """Obj type must [Curve or Text] and shape 3D and fill"""

        obj = self.obj.copy()
        obj.data = self.obj.data.copy()

        if obj.data.dimensions == '2D':
            obj.data.dimensions = '3D'

        # Buraya sınama durumlarını ekle.

        # Clear splines that are not cycles.
        for s in obj.data.splines:
            if not s.use_cyclic_u:
                obj.data.splines.remove(s)

        ms = obj.to_mesh()

        if not ms:
            return

        # Convert to mesh
        bm = bmesh.new()
        bm.from_mesh(ms)

        deep_remove_to_object(obj)

        # Calc first point. MinX and MaxY  -> Top Left Corner
        v_x = [v.co.x for v in bm.verts]
        v_y = [v.co.y for v in bm.verts]

        first_point = Vector((min(v_x), max(v_y), 0))
        max_x = max(v_x)
        min_y = min(v_y)

        ang = self.conf.carving_angle

        # x:0   y:1   z:2
        axis = ang > math.radians(45)

        dist = (self.conf.carving_range / (math.cos(ang - math.radians(45)))) / math.sqrt(2)

        self.block += 1
        self.add_block(name=f"{self.obj_name}, Clearance, ZigZag", expand="0", enable="1")

        # Grups -> Lines -> Line -> (Vert0, Vert1)
        grups = []

        # Çizgi ile meshi tara ve kesişen yerleri grupla
        while first_point.x < max_x or first_point.y > min_y:
            _bm = bm.copy()

            cut = bmesh.ops.bisect_plane(_bm, geom=_bm.edges[:] + _bm.faces[:], dist=0,
                                         plane_co=first_point,
                                         plane_no=self.conf.carving_normal,
                                         )["geom_cut"]

            verts = sorted([v.co for v in cut if isinstance(v, bmesh.types.BMVert)], key=lambda v: v[axis])

            # Grup
            g = []

            for v0, v1 in zip(verts[0::2], verts[1::2]):
                if (v1[axis] - v0[axis]) < dist:
                    continue

                # Distance control step
                step = dist / 2

                cont = False

                while nCompute.closest_dist_point(bm, v0) < dist:
                    v0 = v0.lerp(v1, step / (v1 - v0).length)
                    if v0[axis] > v1[axis]:  # or ((v0 - v1).length < dist):
                        cont = True
                        break

                if cont:
                    continue

                while nCompute.closest_dist_point(bm, v1) < dist:
                    v1 = v1.lerp(v0, step / (v1 - v0).length)
                    if v0[axis] > v1[axis]:  # or ((v0 - v1).length < dist):
                        cont = True
                        break

                if cont:
                    continue

                if nCompute.closest_dist_line(bm, v0, v1) < dist:
                    v0_ort = v0.lerp(v1, step / (v1 - v0).length)
                    while v0_ort[axis] < v1[axis] and (v1 - v0_ort).length > dist:

                        while nCompute.closest_dist_line(bm, v0, v0_ort.lerp(v1, step / (
                                v1 - v0_ort).length)) > dist and v0_ort[axis] < v1[axis]:
                            v0_ort = v0_ort.lerp(v1, step / (v1 - v0_ort).length)

                        if (v0 - v0_ort).length > dist:
                            g.append((v0.copy(), v0_ort.copy()))

                        v0 = v0_ort.xyz

                        while nCompute.closest_dist_line(bm, v0, v0_ort.lerp(v1, step / (
                                v1 - v0_ort).length)) < dist and v0_ort[axis] < v1[axis]:
                            v0_ort = v0_ort.lerp(v1, step / (v1 - v0_ort).length)
                            v0 = v0_ort.xyz

                else:
                    g.append((v0, v1))

            grups.append(g)
            first_point.x += dist
            first_point.y -= dist

        line_list = []

        # Ters Çevir
        revrs = False

        # Önceki Nokta
        v_prv = None

        #
        g_ind = 0

        # Gruplanmış çizgileri uygun olan uçlarından birleştir.
        while any(grups):
            g = grups[g_ind]

            # Grup öğesi boşsa son noktayı temizle.
            if not len(g):
                v_prv = None

            elif v_prv:
                l_min_dist = math.inf

                # Şimdi ele alacağımız çizgi
                l_cur = None

                # Önceki noktaya, şimdi ele aldığımız noktalar arasındaki en yakın olanını bul
                for l in g:

                    v_lnk = l[1] if revrs else l[0]

                    if (v_lnk - v_prv).length < l_min_dist:
                        l_min_dist = (v_lnk - v_prv).length
                        l_cur = l

                ok = True

                v_lnk, v_lst = (l_cur[1], l_cur[0]) if revrs else (l_cur[0], l_cur[1])

                # Yeni çizginin, Objedeki çizgilerle kesişip kesişmediğine bak
                for e_bm in bm.edges[:]:

                    if intersect_line_line_2d(v_prv, v_lnk, e_bm.verts[0].co, e_bm.verts[1].co):
                        ok = False
                        break

                # Kesişme yoksa ve Kenarlara yakın değilse çizgiyi ekle.
                if ok and nCompute.closest_dist_line(bm, v_prv, v_lnk) > dist:  # dist / 2 -> OutLine'a yakınları onayla

                    # Önceki çizginin son noktasını şimdiki çizginin ilk noktasına bağla
                    line_list.append((v_prv, v_lnk))

                    # Şimdiki çizgiyi oluştur.
                    line_list.append((v_lnk, v_lst))

                    # self.line(v_prv, v_lnk)
                    # self.line(v_lnk, v_lst)
                    v_prv = v_lst
                    g.remove(l_cur)
                    revrs = not revrs
                else:
                    v_prv = None

            # Grupta hala çizgi varsa ve önceki nokta yoksa, Yeni çizgiye başlayacağımız anlamına gelir.
            # Bu yüzden yeni çizgi için, Z'de güvenli konuma alınarak hazırlık yapılır.
            if len(g) and not v_prv:
                if revrs:
                    line_list.append((g[0][1], g[0][0], True))
                    # self.line(g[0][1], g[0][0], new_line=True)
                    v_prv = g[0][0]
                else:
                    line_list.append((g[0][0], g[0][1], True))
                    # self.line(g[0][0], g[0][1], new_line=True)
                    v_prv = g[0][1]
                g.remove(g[0])
                revrs = not revrs

            g_ind += 1
            if len(grups) <= g_ind:
                grups.reverse()
                g_ind = 0
                revrs = not revrs
                v_prv = None

        for j, k in enumerate(self.dongu):
            self.step_vector.z = k
            self.add_block(name=f"{self.obj_name}, Clearance, ZigZag, StepZ{j}", expand="0", enable="1")
            for l in line_list:
                self.line(l[0] - self.step_vector, l[1] - self.step_vector, *l[2:])

    def starting_code(self, point_list):
        r = self.roll
        point1 = point_list[0]

        if not self.safe_z:
            self.safe_z = self.max_z + self.conf.safe_z  # max(max_z + self.conf.safe_z, self.conf.safe_z, self.safe_z)

        self.code = f"G0 Z{r(z=self.safe_z)}"

        # First XY Pozition
        self.code = f"G0 X{r(x=point1.x)} Y{r(y=point1.y)}"

        # Rapid Z, Nearest point
        self.code = f"G0 Z{r(z=self.max_z)}"

        # First Plunge in Z
        self.code = f"G1 Z{r(z=point1.z)} F{self.conf.plunge}"
