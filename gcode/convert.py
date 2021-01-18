import time
import bpy
import math
import bmesh

from bpy.types import Operator
from mathutils import Matrix, Vector
from mathutils.geometry import intersect_line_line_2d, interpolate_bezier
from bpy.props import StringProperty, FloatProperty, IntProperty, FloatVectorProperty

from ..utils.nVector import nVector
from ..utils import nCompute
from ..objects.configs.props import S

# TODO !!!
#   Mil için ofseti ekleyelim
#   Poly obje çizilirken, G2-G3 uyumluluk modu isteği ekleyelim
#   Offset uygulanıp uygulanmayacağı Property

# Faydalan:
#   İki çizginin kesişen noktası:
#       2D -> mathutils.geometry.intersect_line_line_2d(lineA_p1, lineA_p2, lineB_p1, lineB_p2)
#       3D -> mathutils.geometry.intersect_line_line(v1, v2, v3, v4)


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

    # Birleşendeki son Vertexi alıyoruz ve datadan o vertex bağlı diğerlerini bulup alıyoruz.
    _verts = data[bilesen[-1].index].copy()

    # Vertexleri aldık içini temizleyelim.
    data[bilesen[-1].index].clear()

    # Bitir, 3 taneden az vertex varsa, bilesen 2 taneden az ise, vertexlerin ilki ve sonuncusu aynıysa dön
    if (len(_verts) < 3) or (len(bilesen) < 2) or bilesen[0] == bilesen[-1]:  # len(set(_verts) - set(bilesen)) < 1 or
        return bilesen

    # Vertexlerdeki son
    if bilesen[-2] != _verts[0]:
        _verts.reverse()

    bilesen = biless(data, bilesen[:-2] + _verts)
    bilesen.reverse()
    return biless(data, bilesen)


def bmesh_independent_parts(bm):
    """BMesh'i bağımsız parçalarına ayırır.
    return:
    [
        {"verts": {Vert1, Vert2...}, "edges": {Edge1, Edge2...}}    -> Part1
        {"verts": {Vert1, Vert2...}, "edges": {Edge1, Edge2...}}    -> Part2...
    ]
    """
    bm.edges.ensure_lookup_table()

    edges = bm.edges[:]
    parts = []
    while edges:
        is_append = False
        for e in edges[::-1]:
            v0, v1 = e.verts[:]
            for p in parts:
                if v0 in p["verts"] or v1 in p["verts"]:
                    p["edges"].add(e)
                    p["verts"].add(v0)
                    p["verts"].add(v1)
                    edges.remove(e)
                    is_append = True
                    break

            if is_append:
                break

        if not is_append:
            e = edges[-1]
            v0, v1 = e.verts[:]
            parts.append({"verts": {v0, v1}, "edges": {e}})

    return parts


def is_planar(edges):
    """BMEdge'lerin düzlemsel olup olmadığını döndürür"""
    for e in edges:
        # İki kenarın birbirine bitişik olduğunda, arada kalan görünmeyen yüzeyleri telafi edebilmek için, alanları
        # kontrol edilerek işleme devam edilir.
        if e.is_contiguous and e.calc_face_angle(None) and \
                e.link_faces[0].calc_area() > 0.01 and e.link_faces[1].calc_area() > 0.01:
            return False
    return True


def bmesh_planar_parts(bm):
    """Düzlemsel parçaları döndürür. Edgeleri parçalarına ayırır ve düzlemsel olup olmadıklarını sorgular.
    return:
    [
        { Edge1, Edge2..}   -> Part1
        { Edge1, Edge2..}   -> Part2
    ]
    """
    return [list(p["edges"]) for p in bmesh_independent_parts(bm) if is_planar(p["edges"])]


def bmedges_to_curve(edges):
    """BMEdge'leri birleştirerek curve oluşturur.
    return:
    [ curve ] or [ ]
    """
    # Vertexleri indexlere ayır
    # {ind: [Edge1, Edge2], ind: [Edge1, Edge2]}
    inds = {}
    for e in edges:
        for ind in [e.verts[0].index, e.verts[1].index]:
            if ind in inds:
                # Önceki eklenen edge ile şimdi eklenen edge vertexlerini birleştir.
                verts = (*inds[ind], *e.verts[:])

                # Ortanca Vertex bulunur
                mid = max(verts, key=verts.count)

                # Vertexler kümelenir ve ortanca çıkartılır
                vts = list(set(verts))
                vts.remove(mid)

                # Vertexler, sırasına göre gruplanır.
                inds[ind] = [vts[0], mid, vts[1]]
            else:
                inds[ind] = e.verts[:]

    # print("indexes", *inds.values(), sep="\n")
    polys = []

    for ind, verts in inds.items():
        if len(verts) < 3:
            # polys.append(verts)
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

            # Burada Kapalı Curve olup olmadığına karar vermek için, ilk ve son noktaları arasındaki mesafeye bakıyoruz
            if (poly[0].co.xyz - poly[-1].co.xyz).length < .01:
                spline.use_cyclic_u = True

                # Fazlalık yapmasın diye siliyoruz. Çünkü ilk ve son vertex aynı.
                poly.remove(poly[-1])

                # Kapalı Curve ise Başlangıç noktasını değiştir. X ve Y de en küçük noktayı başlangıç noktası yap
                ind = poly.index(min(poly, key=lambda k: [k.co.x, k.co.y]))
                bas = poly[:ind]
                poly = poly[ind:]
                poly.extend(bas)

            spline.points[0].co.xyz = poly[0].co.xyz
            for v in poly[1:]:
                spline.points.add(1)
                spline.points[-1].co.xyz = v.co.xyz

        return [curve]
    return []


def faces_in_z_range(bm, min_z, max_z):
    """Z ekseninde min_z ile max_z arasındaki yüzeyleri döndürür."""
    # bm.faces.ensure_lookup_table()
    return [f for f in bm.faces[:] if all([min_z <= v.co.z <= max_z for v in f.verts[:]])]


def bmesh_slice(data, step_z):
    # TODO !!!
    #   Yüzey katmanlarını da taramayı ekleyelim

    curves = []
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.weld_verts(bm)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.7), verts=bm.verts, edges=bm.edges)

    for planar_edges in bmesh_planar_parts(bm):
        # Düzlemsel parçada yüzey içindeki gereksiz BMEdge'leri siliyoruz.
        for e in planar_edges[::-1]:
            # Bu kenar 2 tane yüzeyi mi birleştiriyor. O zaman sil
            if e.is_contiguous:
                planar_edges.remove(e)

        # Curve oluşturuyoruz
        curves.extend(bmedges_to_curve(planar_edges))

        # BMesh'den düzlemsel parçayı siliyoruz.
        bmesh.ops.delete(bm, geom=planar_edges, context="EDGES")

    verts_z = [v.co.z for v in bm.verts]
    min_z = min(verts_z, default=0)
    max_z = max(verts_z, default=0)
    step = max_z - step_z

    if step < min_z != max_z:
        step = min_z

    while step >= min_z:
        # BMesh'ten Z ekseninde bir kesit alınır
        cut = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                                     plane_co=Vector((0, 0, (step + .001 if step == min_z else step))),
                                     plane_no=Vector((0, 0, -1)),
                                     dist=0
                                     )["geom_cut"]

        # TODO !!Çok yavaş bir yöntem olduğu için şimdilik iptal
        #   Arada yüzey kaldıysa, yüzeyide traşla
        # for f in faces_in_z_range(bm, step, step+step_z):
        #     curves.extend(bmedges_to_curve(f.edges))

        step -= step_z
        if step < min_z and step + step_z != min_z:
            # En alt katman dilimlenebilsin diye..
            step = min_z

        curves.extend(
            bmedges_to_curve(
                # Edge'lerden Curve yap
                [e for e in cut if isinstance(e, bmesh.types.BMEdge)]
            )
        )

    return curves


def get_circular_points_indexes(point_list, round_circ=1, min_point=5, calc_line_len=False):
    """Noktalara sırayla bakar, peş peşe olan min_point sayısı kadar noktadan bir çember geçiyorsa,
    çemberin geçtiği noktaların indexini döndürür

    :param point_list: Vector -> Nokta listesi
    :param round_circ: int -> 3 noktadan geçen çemberin merkezi bulunduğunda, kaç basamaktan yuvarlansın
    :param min_point: int -> En az kaç noktanın birleşimi çembersel kabul edilsin. Bunun 5'ten küçük olması önerilmez.
                             Çünkü dörtgenleri de çembersel olarak algılar ve bu bir hata olur
    :param calc_line_len: bool -> Hesaplama yaparken, yan yana olan çizgilerin uzunlukları eşit mi kontrol edilsin mi?

    return: [(4, 8), (9, 13), (14, 18), (20, 27)]  -> 4 ile 8. indexler arasındaki noktalardan çember geçiyor...
    """
    # Ovallik sorgulamak için minimum 5 nokta ele alınır
    ask_points = []

    # 3'lü noktaların, merkezleri belirlenir.
    ask_center_circls = []

    # Noktadan sonraki noktaya olan mesafe, uzunluk
    ask_length = []

    len_points = len(point_list)

    for i, p in enumerate(point_list):

        loc = p # p.co.to_3d() - self.step_vector

        ask_points.append(loc)

        if i + 1 < len_points:
            ask_length.append(round((p - point_list[i + 1]).length, 1))

        if len(ask_points) == 3:
            ask_center_circls.append(nVector.yuvarla_vector(round_circ, nCompute.circle_center(*ask_points)))
            ask_points.remove(ask_points[0])

    paket = []
    indexler = []
    paketleme_sayisi = min_point-2
    son_index = len(ask_center_circls) - 1
    # print("Centers:\n", *ask_center_circls, sep="\n", end="\n\n")

    for i, p in enumerate(ask_center_circls):
        paket.append((i, p, ask_length[i]))
        if not i:
            continue

        if len(paket) > 1 or i == son_index:
            # Son iki yayın merkezi eşit değilse  ya da
            # Sonuncu indexteysek ya da
            # Uzunluklar eşit değilse
            if len(paket) > 1 and (paket[-1][1] != paket[-2][1] or (calc_line_len and paket[-1][2] != paket[-2][2])):

                # Paket sayısı, istenen sayıdaysa veya daha büyükse, birikenleri paketle
                if len(paket) > paketleme_sayisi:
                    indexler.append((paket[0][0], i + 1))
                    paket = []
                # Az paket var ve sonuncu yayın merkezi uymadıysa, ilk yayı paketten çıkart
                else:
                    silincekler = []
                    len_paket = len(paket)
                    for no, j in enumerate(paket):
                        ind = no + 1
                        if (ind < len_paket) and (j != paket[ind]):
                            silincekler.append(j)
                    for s in silincekler:
                        paket.remove(s)
                    # paket.remove(paket[0])

            elif i == son_index:
                if len(paket) >= paketleme_sayisi:
                    # indexler.append((paket[0][0], paket[-2][0] + 2))
                    indexler.append((paket[0][0], i + 2))
                    paket = []
    # print(*indexler, sep="\n")
    return indexler


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
        if obj_orj.type == "FONT" and not len(obj_orj.modifiers) and not obj_orj.data.extrude and \
           not obj_orj.data.bevel_object and not obj_orj.data.bevel_depth and not obj_orj.data.follow_curve:
            obj = obj_orj.copy()
            obj.data = get_data_text_object(context, obj_orj)
            if not obj.data:
                return {'CANCELLED'}
            obj.data.transform(obj_orj.matrix_world)
            obj.matrix_world = Matrix()

        # Curve ise veya kütük yok ise direkt kopyala
        elif obj_orj.type == "CURVE" and not len(obj_orj.modifiers) and not obj_orj.data.extrude and \
           not obj_orj.data.bevel_object and not obj_orj.data.bevel_depth:
            obj = obj_orj.copy()
            obj.data = obj.data.copy()
            obj.data.transform(obj_orj.matrix_world)
            obj.matrix_world = Matrix()

        # Eğer Mesh ise ve kütük yok ise mesh'i al
        elif not stock: # or obj_orj.type in ("FONT", "CURVE"):
            # Grafiklerden modifiye edilmiş objeyi alıyoruz.
            depsgraph = bpy.context.evaluated_depsgraph_get()
            object_eval = obj_orj.evaluated_get(depsgraph)

            # Yeni obje oluşturuyoruz
            obj = bpy.data.objects.new("Sil", bpy.data.meshes.new_from_object(object_eval))
            obj.data.transform(obj_orj.matrix_world)
            obj.matrix_world = Matrix()

        # Eğer 3D Obje ise ve kütük var ise kütükten çıkart
        else:
            # Kütüğün kopyasını oluşturuyoruz
            obj = stock.copy()

            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_dif = bpy.data.objects.new("Sil", bpy.data.meshes.new_from_object(obj_orj.evaluated_get(depsgraph)))
            obj_dif.data.transform(obj_orj.matrix_world)
            obj_dif.matrix_world = Matrix()

            # Hedef objeyi modifier uygulayarak kütükten çıkartıyoruz.
            mod_bool = stock.modifiers.new('my_bool_mod', 'BOOLEAN')
            mod_bool.operation = 'DIFFERENCE'
            # mod_bool.object = obj_orj
            mod_bool.object = obj_dif

            # Grafiklerden modifiye edilmiş objeyi alıyoruz.
            depsgraph = bpy.context.evaluated_depsgraph_get()
            object_eval = stock.evaluated_get(depsgraph)

            # Oluşan objenin datasını kopyalıyoruz
            obj.data = bpy.data.meshes.new_from_object(object_eval)
            obj.data.transform(obj.matrix_world)
            obj.matrix_world = Matrix()

            # Bool iiçin kullandığımız objeyi silebiliriz
            deep_remove_to_object(obj_dif)

            # Orjinal Kütüğe şimdi eklediğimiz modifierleri temizliyoruz ki sonradan sorun çıkmasın
            stock.modifiers.remove(mod_bool)

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
        self.obj = obj

        # Mesh'e dönüştürüp, Z'de uç noktaları buluyoruz
        verts = [v.co.z for v in obj.to_mesh().vertices]
        self.max_z = max(verts)
        self.min_z = min(verts)

        # Oluşan mesh'i temizliyoruz
        obj.to_mesh_clear()

        # #########################################
        # ######################################### DiLiMLE
        depth = conf.depth
        step = conf.step
        if obj.type == "MESH":
            # Mesh dilimlenip, Curvelere dönüştürülür ve listede tutulur.
            self.curve_list = bmesh_slice(obj.data.copy(), step)
            # TODO !!! Dilimlemeden sonra bir de yüzeyi gez seçeneği ekleyelim. Bu seçenek de, Z'de değil de, yüzeyi
            #  Y'de dilimlesin. Sonra üstteki diğer dilimleme seçeneğinde son katmanı gezmesini iptal edelim

            depth = step

        # Z adımı, derinlikten büyükse veya spline yoksa işlemi bitir
        elif step > depth or not len(self.obj.data.splines):
            return self.timer_remove(context, only_object=True)

        # Steps in the Z axis -> 0.5, 1.0, 1.5, 2.0 ...
        self.dongu.extend([i * step for i in range(1, int(depth / step + 1), )])

        ##########################################
        ##########################################
        # Calculate last Z step
        if depth % step > 0.01 and len(self.dongu):
            if len(self.dongu):
                self.dongu.append(round(self.dongu[-1] + depth % step, conf.round_loca))
            else:
                self.dongu.append(round(self.dongu[-1], conf.round_loca))

        # Create initial configs of the shape -> Block x
        self.add_block(expand="1", enable="1")
        self.code = f"{conf.plane} ( Plane Axis )"
        self.code = f"S{conf.spindle} ( Spindle )"
        self.code = f"( Safe Z : {conf.safe_z} )"
        self.code = f"( Step Z : {step} )"
        self.code = f"( Total depth : {round(depth, 3) if obj.type != 'MESH' else self.min_z} )"
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

        if self.conf.milling_strategy in (S.INNER, S.ONLY_INNER):
            self.clearance_zigzag(len_curves and self.curve_list[self.index_curve])

        if len_curves:
            self.index_curve += 1
            if len_curves > self.index_curve:
                self.index_spline = 0
                self.index_dongu = 0
                return {'PASS_THROUGH'}

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

    # Faydalanıldı:
    #   https://behreajj.medium.com/scripting-curves-in-blender-with-python-c487097efd13
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

            # Eğri üzerinden aldığımız noktaları sorguluyoruz
            for ps in interpolate_bezier(m1, hr, hl, m2, 5)[1:-1]:
                ask_center.append(nVector.yuvarla_vector(conf.round_circ, nCompute.circle_center(m1, ps, m2)))
                ask_line.append(nVector.bul_dogru_uzerindemi_3p(m1, m2, ps))

            # Noktalar düz çizgi veya  Çember dilimi oluşturuyorsa
            if all(ask_line) or (not conf.as_line and ask_center[0] == ask_center[1] == ask_center[2]):
                point_list.extend(interpolate_bezier(m1, hr, hl, m2, 3)[j != 0:])

            # Bezier veya Poly isteniyorsa
            else:
                point_list.extend(interpolate_bezier(m1, hr, hl, m2, (subcurve.resolution_u * 2 + 1))[j != 0:])

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
        as_line = conf.as_line
        r = self.roll

        point_list = [i.co.to_3d() - self.step_vector for i in subcurve.points]

        if not point_list:
            return

        # ####################### Dairesel hesap kısmı
        # Poly üzerindeki Dairesel Noktaların indexlerini alıyoruz, sonra bu aralıktaki noktaları G2-3 koduna çeviriyoz
        if not as_line:
            circ_p_inds = get_circular_points_indexes(point_list,
                                                      conf.round_circ,
                                                      conf.min_verts_for_calc_curve,
                                                      conf.control_line_len_for_calc_curve,
                                                      )
            ind_len = len(circ_p_inds)
            ind_bas = circ_p_inds[0][0] if ind_len else None
            ind_son = circ_p_inds[0][1] if ind_len else None
            # #######################

        for i, p in enumerate(point_list):

            loc = p  # p.co.to_3d() - self.step_vector

            # #######################
            # ####################### Dairesel hesap kısmı
            if not as_line and ind_len:

                # İndex, Dairesel aralıktaysa, atlayalım
                if ind_bas < i < ind_son:
                    continue

                # İndex, dairesel aralığın son noktasındaysa, G2-G3 kodunu ekle ve varsa sonraki dairesel aralığı tanıla
                if i == ind_son:
                    # TODO !!! Daireselleştirirken, parça boylarının aynı olması kuralını ekleyelim. Diğer türlü,
                    #   daireye denk gelen başka bir nokta da daireden sanılabiliyor
                    p1 = point_list[ind_bas]
                    p2 = point_list[i - 1]
                    p3 = point_list[i]
                    m = nVector.bul_cember_merkezi_3p(p1, p2, p3, duzlem=conf.plane)

                    I = m.x - p1.x if conf.plane != "G19" else 0
                    J = m.y - p1.y if conf.plane != "G18" else 0
                    K = m.z - p1.z if conf.plane != "G17" else 0

                    # !!! For very large CNC machines, this value should be increased. ( limit: 800 )
                    # G1: as line / G1: as line / Calculate G2 or G3
                    b = int(max(abs(I), abs(J), abs(K)) > 800) or nVector.bul_yonu_1m3p(m, p1, p2, p3)

                    self.code = f"G{b} X{r(x=p3.x)} Y{r(y=p3.y)} Z{r(z=p3.z)}" + \
                                ("", f" I{r(i=I)} J{r(j=J)} K{r(k=K)}")[b > 1] + \
                                ("", f" F{conf.feed}")[i == 0]

                    # point_list[i-3:i]
                    # self.code =
                    circ_p_inds.remove(circ_p_inds[0])

                    ind_len = len(circ_p_inds)
                    ind_bas = circ_p_inds[0][0] if ind_len else None
                    ind_son = circ_p_inds[0][1] if ind_len else None
                    continue
            # #######################
            # #######################

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
            # self.code = f"G0 Z{r(z=first_z or self.max_z)}"
            self.code = f"G0 Z{r(z=self.safe_z or first_z or self.max_z)}"  # Bu satır ile
            self.code = f"G0 X{r(x=vert0.x)} Y{r(y=vert0.y)}"
            self.code = f"G0 Z{r(z=first_z or self.max_z)}"     # Bu satırı, sadece clearence ile mi kullansak
            self.code = f"G1 Z{r(z=vert0.z)}"
        # else:
        #    self.code = f"G0 X{r(x=vert0.x)} Y{r(y=vert0.y)} Z{r(z=vert0.z)}"
        self.code = f"G1 X{r(x=vert1.x)} Y{r(y=vert1.y)} Z{r(z=vert1.z)}"

    # Ref: https://b3d.interplanety.org/en/how-to-create-mesh-through-the-blender-python-api/
    def clearance_zigzag(self, curve=None):
        """Obj type must [Curve or Text] and shape 3D and fill"""
        if curve:
            obj = bpy.data.objects.new("object_name", curve.copy())
        else:
            obj = self.obj.copy()
            obj.data = self.obj.data.copy()

            if obj.type == "CURVE" and obj.data.dimensions == '2D':
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
                # TODO !!! Burada hesaplama şu şekilde yapılmalı;
                #     En yakın kenardan, distance çıkartılır. Bu kadar. Böylece döngülere gerek kalmaz

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
                    v_prv = g[0][0]
                else:
                    line_list.append((g[0][0], g[0][1], True))
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
            if not curve:
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
