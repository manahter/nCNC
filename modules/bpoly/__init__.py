import math
import bpy
import bmesh
from mathutils.geometry import area_tri, normal, intersect_line_line_2d, intersect_point_line, intersect_line_line
from mathutils import Vector
from bpy.types import Spline

from .is_ import *
from .convert import spline_to_poly
from .angles import angles_in_verts
from .intersect import (
    new_parts_from_intersect_self,
    new_parts_from_overlaps,
    add_point_to_intersects,
    non_intersecting_poly
)


class bpoly(list):
    def __init__(self, arg, cyclic=None, yon=None, copy_conf=None, fix=True):
        """
        :param arg: bpy.types.Spline | List: spline veya liste olabilir.
        :param yon: int: -1: iç offset, +1: dış offset
        :param cyclic: bool: Kapalı mı?
        :param copy_conf: bpoly: Ayarları başka bpoly'den kopyala
        """
        if type(arg) == Spline:

            # Kapalı olup olmadığı öğrenilir
            self.cyclic = arg.use_cyclic_u

            # Convert edilir
            arg = spline_to_poly(arg)

        super().__init__(arg)

        if copy_conf:
            self.cyclic = copy_conf.cyclic
            self.yon = copy_conf.yon

        if cyclic:
            self.cyclic = cyclic

        if yon:
            self.yon = yon

        # Poly'de uygun olmayan kısımlar onarılır
        if fix:
            self.fix()

    def new_bpoly(self, arg, fix=False):
        """self confs ile yeni boş bir bpoly döndürür"""
        return bpoly(arg, copy_conf=self, fix=fix)

    yon = 1
    '''yon = yön = orientation -> İç mi dış mı?
    -1  -> İç offset
    +1  -> Dış offset
    '''

    _cyclic = False

    @property
    def cyclic(self, tolerance=.001) -> bool:
        """Poly kapalı mı?
        :param tolerance: float: Karşılaştırırken hesaplanan yanılma payı

        return bool
        """

        return self._cyclic or (is_same_point(self[-1], self[0], tolerance) if len(self) > 1 else False)

    @cyclic.setter
    def cyclic(self, val: bool):
        self._cyclic = val

    def weld(self, other_bpoly):
        """Diğer poly'yi self'e ilk kesişim yerinden kaynak yapar. - Kaba birleştirme - Mutlaka kesişiyor olmalılar"""
        # NOT: Sadece 1 noktadan kaynak yapar.

        for i in range(len(self)):

            # 0. index ise ve kapalı poly değilsek atla
            if not i and not self.cyclic:
                continue

            p0 = self[i - 1]
            p1 = self[i]

            # ks = bul_kesis_line_poly(p0, p1, other_bpoly, cyclic=other_bpoly.cyclic)
            ks = other_bpoly.calc_intersect_line(p0, p1)

            if ks:
                pol1_new = other_bpoly[ks[0][0]:] + other_bpoly[:ks[0][0]] + [ks[0][1]]

                new_list = self[:i] + [ks[0][1]] + pol1_new + self[i:]

                self.clear()
                self.extend(new_list)

                return

    # ############################################# Ops
    def fix(self):
        """Poly'de uygun olmayan kısımlar onarılır"""

        # Peş peşe aynı olan noktaları temizle
        self.disolve_doubles()

        # Sıfır derece açı oluşturan noktaları temizle
        self.clear_zero_angle()

        # Aynı Doğru üzerindeki noktaları temizle
        self.clear_linear_points()

        # Poly çizgileri kesişmez hale getirilir
        non_intersecting_poly(self, self.cyclic)

    def disolve_doubles(self, tolerance=0.0001):
        """Peş Peşe 2 tane aynı nokta varsa bir tanesi silinir"""
        # Verts sayısı 0 ise bitir
        if not len(self):
            return

        # Tersten alıyoruz ki, silinince listede kayma olmasın
        for i in range(len(self) - 1, -1, -1):
            if is_same_point(self[i - 1], self[i], tolerance=tolerance):
                self.pop(i)

    def clear_linear_points(self):
        """Aynı doğru üzerindeki noktaları temizle"""
        cyclic = self.cyclic
        len_verts = len(self) - 1
        for i in range(len(self)):
            if i in (0, 1) or (i == 2 and not cyclic):
                continue

            j = len_verts - i
            # p0, p1, p2 -> Aynı doğru üzerinde mi?
            if is_linear_3p(self[j], self[j + 1], self[j + 2]):
                self.pop(j + 1)

    def clear_zero_angle(self, tolerance=.001):
        """Sıfır derecelik açı oluşturan noktayı temizler"""
        if len(self) < 2:
            return

        cyclic = self.cyclic
        len_verts = len(self) - (2 if cyclic else 1)

        for i in range(len(self)):
            if i in (0, 1) or (i == 2 and not cyclic):
                continue

            j = len_verts - i

            if is_same_point(self[j + 2], self[j], tolerance=tolerance):
                self.pop(j + 2)
                self.pop(j + 1)

    # ############################################# Is_
    def is_intersect(self, other_bpoly, in_2d=True):
        """İki poly çizgileri arasında kesişen çizgi var mı?

        :param other_bpoly: VectorList: 2. Poly'nin noktaları
        :param in_2d: bool: Kesişim 2D olarak mı incelensin?

        return bool:
            False-> Kesişmez
        """

        for t in range(len(other_bpoly)):
            if not t and not other_bpoly.cyclic:
                continue
            t0 = other_bpoly[t - 1]
            t1 = other_bpoly[t]
            for m in range(len(self)):
                if not m and not self.cyclic:
                    continue

                m0 = self[m - 1]
                m1 = self[m]

                if in_2d:
                    if intersect_line_line_2d(t0, t1, m0, m1):
                        return True
                else:
                    # TODO Henüz 3D'de kesişim kısmı kodlanmadı
                    intersect_line_line(t0, t1, m0, m1)

        return False

    def is_intersect_line(self, p0, p1, in_2d=True):
        """Line ile kesişip kesişmediğini bulur
        :param p0: Vector: Line'ın 0. noktası
        :param p1: Vector: Line'ın 1. noktası
        :param in_2d: bool: Kesişim 2D olarak mı incelensin?

        return bool
        """
        return self.is_intersect(bpoly((p0, p1), cyclic=False), in_2d=in_2d)

    @staticmethod
    def _ray(verts, p):
        """İçinde mi? Işın yöntemi"""
        # Kaynak
        # https://eray-tr.blogspot.com/2020/11/nokta-poligonun-icinde-mi-point-in.html
        # https://gist.github.com/byciikel/997b53800d21ce7e833f2b14805919a7
        x, y = p.xy

        inside = False

        for i in range(len(verts)):
            x0, y0 = verts[i - 1].xy
            x1, y1 = verts[i].xy

            # Kesişiyorsa, inside'ı ters çevir
            if ((y1 > y) != (y0 > y)) and (x < (x0 - x1) * (y - y1) / (y0 - y1) + x1):
                inside = not inside

        return inside

    def is_inside_point(self, p):
        """Nokta, Şeklin içinde mi
        :param p: Vector: Point

        return bool
        """

        # Önce Boundry bul
        min_x = min(self, key=lambda v: v.x).x
        min_y = min(self, key=lambda v: v.y).y
        max_x = max(self, key=lambda v: v.x).x
        max_y = max(self, key=lambda v: v.y).y

        # Şekil çerçevesi içinde değilse şimdiden dön
        if not (min_x < p.x < max_x and min_y < p.y < max_y):
            return False

        return self._ray(self, p)

    def is_inside_bpoly(self, other_bpoly):
        """poly0, poly1 şeklinin içinde mi?"""

        for p in other_bpoly:

            if not self.is_inside_point(p):
                return False

        return True

    def is_close_distance_to_points(self, other_bpoly, distance):
        """Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
        verts_target'daki noktalar sırayla ele alınıp, verts_main'deki noktalara istenen distance'dan yakın mı kontrol
        edilir.

        :param other_bpoly: VectorList: İncelenen Poly'nin noktaları
        :param distance: float: İncelenecek mesafe, uzaklık

        return bool:
            True -> Evet yakın nokta/lar var.
            False-> Hayır hiçbir nokta yakın değil.
        """
        distance = abs(distance)

        # Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
        for t in other_bpoly:
            for m in range(len(self)):
                if not m and not self.cyclic:
                    continue
                p0 = self[m - 1]
                p1 = self[m]
                c, ratio = intersect_point_line(t, p0, p1)
                mes = (c - t).length
                if 1 >= ratio >= 0 and (mes + .001 < distance):
                    return True

        return False

    def calc_intersect_line(self, p0, p1):
        """Line ile kesişim indexlerini ve yerlerini bulur
        :param p0: Vector: Line'ın 0. noktası
        :param p1: Vector: Line'ın 1. noktası

        return [(index, Vector), ...]
        """
        kesisim = []
        for i in range(len(self)):
            if not i and not self.cyclic:
                continue
            v0 = self[i - 1]
            v1 = self[i]

            o = intersect_line_line_2d(p0, p1, v0, v1)
            if o:
                # TODO !!!
                #   Kesişim yerine eklenen noktanın Z'de yeri belli olsun.

                z0 = v0.lerp(v1, intersect_point_line(o, v0.xy, v1.xy)[1]).z
                z1 = p0.lerp(p1, intersect_point_line(o, p0.xy, p1.xy)[1]).z
                z = (z0 + z1) / 2

                o = Vector((*o, z)).freeze()
                kesisim.append((i, o))
                # print("Kesiişim : -> ", kesisim[-1])

        # v0-v1 aralığında yeni eklenen kesişim noktalarının sırasını düzenliyoruz.
        kesisim.sort(key=lambda x: intersect_point_line(x[1], p0, p1)[1])

        return kesisim


def add_screen_decorator(func):
    """
    :param add_screen: bool:
        True -> Ekrana ekle ve objeyi döndür
        False-> Ekrana ekleme, polyleri döndür
    """
    def inner(*args, **kwargs):
        _add_screen = kwargs.pop("add_screen", False)
        result = func(*args, **kwargs)

        if _add_screen:
            return new_poly_curve(result, add_screen=True)

        return result

    return inner


def new_poly_curve(polys, add_screen=False):
    """Noktalardan yeni bir Poly oluşturulur.

    :param polys: [ [poly_points], [...], ... ] -> Poly pointlerin listesi -> VectorList_Lists
    :param add_screen: bool:
        True -> Ekrana ekle ve objeyi döndür
        False-> Ekrana ekleme, curve'ü döndür

    return: object or curve
    """
    if not any(polys):
        return None

    # Curve Data oluştur
    curve = bpy.data.curves.new("npoly", "CURVE")

    for j, points in enumerate(polys):
        if len(points) < 2:
            continue

        # Poly spline oluştur
        curve.splines.new("POLY")

        # ilk ve son nokta eşitse, son noktayı sil
        if points[0] == points[-1]:
            points.pop(-1)
            print("Nokta ekle")

        # Kapalı yap
        curve.splines[-1].use_cyclic_u = points.cyclic

        # Curve Pointleri al
        curpt = curve.splines[-1].points

        # Gelen point sayısı kadar Curve'da point oluşturulur
        curpt.add(len(points) - 1)

        # Gelen pointler Curve'ye eklenir
        for j, v in enumerate(points):
            if v.xyz != curpt[-1].co.xyz:
                curpt[j].co.xyz = v

    if add_screen:
        # Obje oluşturlup sahneye eklenir
        obje = bpy.data.objects.new("npoly", curve)
        obje.data.dimensions = '3D'
        bpy.context.scene.collection.objects.link(obje)
        return obje
    return curve


@add_screen_decorator
def offset_splines(splines, distance=.2):
    """
    :param splines: obj.data.splines: gibi
    :param distance: float: Mesafe

    return [VectorList, VectorList...] or CurveObje: Spline'ların offset almış hali
    """
    yon = (-1, 1)[distance > 0]
    distance = abs(distance)

    # [ (verts, cyclic, yon), (verts, cyclic), ... ]
    parts_orj = []

    # yönü düzenle

    # Spline'lar düzgün bir şekilde Poly'ye çevrilir
    for s in splines:

        if type(s) in (list, Spline):
            # Spline Poly, bpoly'ye çevrilir veya bpoly ise birşey yapma
            verts = bpoly(s, yon=yon)
        else:
            verts = s
            verts.yon = yon

        if len(verts) < 2:
            continue

        # Poly partlara eklenir.
        parts_orj.append(verts)

    # Kesişen Poly'leri birleştir (2 kesişenin de kapalı olması gerekiyor)
    for verts0 in parts_orj:

        # verts0 kapalı değilse geç
        if not verts0.cyclic:
            continue

        for verts1 in parts_orj:

            # verts0 ve verts1 aynıysa veya verts0 kapalı değilse geç
            if not verts1.cyclic or (verts0 == verts1):
                continue

            # İki Poly kesişiyorsa, kesişim yerinden birleştir
            if verts0.is_intersect(verts1):
                # verts0 ve verts 1'i birleştir
                verts0.weld(verts1)

                # verts1'i temizle
                verts1.clear()

    # Boş olan parçaları temizle.
    for part in parts_orj[::-1]:
        if not len(part):
            parts_orj.remove(part)

    # Yön Sorgula, Herhangi bir şeklin içindeyse, yön ters döner
    for verts0 in parts_orj:
        # verts0 kapalı değilse geç
        if not verts0.cyclic:
            continue

        for verts1 in parts_orj:

            # verts0 ve verts1 aynıysa veya verts0 kapalı değilse geç
            if not verts1.cyclic or (verts0 == verts1):
                continue

            if verts1.is_inside_bpoly(verts0):
                verts0.yon *= -1

    # Offsetler oluşturulur
    parts = []
    for verts in parts_orj:
        for parca in offset_spline(verts, distance):
            parts.append(
                bpoly(parca, copy_conf=verts)
            )

    yeni_parcalar = []
    # Parçaları gez. Kesişen varsa, kesişim kısımlarından birleştir. Dışarda kalan parçaların uygun olanlarını ekle.
    for ind0, part0 in enumerate(parts):

        # Kapalı değilse geç
        if not part0.cyclic:
            continue

        for ind1, part1 in enumerate(parts):

            # Kapalı değilse geç
            if ind1 <= ind0 or not part1.cyclic:
                continue

            # İki Poly kesişiyorsa, kesişim yerinden birleştir
            if part0.is_intersect(part1):
                add_point_to_intersects(part0, part1)

                """"""
                # Çakışan noktalardan yeni poly'ler
                # Tüm yeni parçaları gez. Eğer Orjinalle kesişmiyorsa yenilere ekle
                for party in new_parts_from_overlaps(part0, part1):
                    onay = True

                    # Bu parçanın, Orjinal çizgilere yakınlığı veya onlarla kesişip kesişmediği kontrol edilir.
                    for part in parts_orj:
                        if part.is_intersect(party) or party.is_close_distance_to_points(part, distance=distance):
                            onay = False
                            break

                    # Bu parça orjinal çizgilere yakın değilse ve onlarla kesişmiyorsa, uygun kabul edilir.
                    if onay:
                        yeni_parcalar.append(party)

    parts.extend(yeni_parcalar)

    return parts


@add_screen_decorator
def offset_spline(spline, distance=.2):
    """Spline'a offset uygular.

    :param spline: obj.data.splines[0] | bpoly
    :param distance: float: Mesafe

    return [VectorList, VectorList...] or CurveObje: Spline'ın offset almış hali
    """
    yon = (-1, 1)[distance > 0]
    distance = abs(distance)

    # bpy.types.Spline ise, bpoly'ye çevrilerek değilse, bpoly alınır
    verts = bpoly(spline, yon=yon) if type(spline) == Spline else spline

    parts = offset_2d(verts, distance)

    return parts


@add_screen_decorator
def clearance_offset_splines(splines, distance=.2):
    """Bu metod biraz tehlikelidir. Çünkü bir hata çıkması durumunda sonsuz döngüye girebilir"""

    distance = -abs(distance)

    # Açık olan splinelar alınmaz
    _splines = [s for s in splines if s.use_cyclic_u]

    # İlk kez offset uygulanır
    parts = []
    last_parts = offset_splines(_splines, distance=distance)

    # Son uygulanan offset'ten parça geldiği sürece, yenilere offset uygulanır
    while last_parts:
        parts.extend(last_parts)
        last_parts = offset_splines(last_parts, distance=distance)

    return parts


# ############################################### Poly içini Zigzagla doldur
@add_screen_decorator
def clearance_zigzag(splines, angle=45, distance=1.0):
    """
    Poly vertslerinin içte kalan kısmına zigzag oluşturur.

    :param splines: VectorList: Dilimlenecek Poly'nin noktaları. Orjinal listeyi verme. Copy List olsun.
    :param angle: int: Dilimleyici hangi açıda olsun
    :param distance: float: Dilimler arası mesafe ne kadar olsun

    return [(p0, p1, p2, p3), (p0, p1), ...]    -> Poly Parçalar
    """

    parts_orj = []
    # Spline'lar düzgün bir şekilde Poly'ye çevrilir
    for s in splines:
        # Spline Poly, bpoly'ye çevrilir veya bpoly ise birşey yapma
        verts = bpoly(s) if type(s) in (list, Spline) else s

        if len(verts) < 2:
            continue

        # Poly partlara eklenir.
        parts_orj.append(verts)

    # Zigzag çizgilerini hesapla
    zigzag_lines = _zigzag_vektorlerini_olustur(parts_orj, angle, distance)

    # Zigzag çizgilerinin Ana Poly'yi kestiği noktalara yeni nokta ekle
    kesimli_hali = _zigzagda_kesisimlere_nokta_ekle(parts_orj, zigzag_lines)

    print(len(kesimli_hali))
    # Ana Poly'ye minik bir offset uygula ve zigzag çigilerini uygun şekilde birleştir.
    # Offsetin sebebi, zigzag çizgilerine çok yakın olanları kesiyor saymasın diyedir..
    full = []
    # for i in _zigzag_cizgilerini_birlestir(offset_splines(parts_orj, -.01), kesimli_hali):
    for i in _zigzag_cizgilerini_birlestir(offset_splines(parts_orj, .01), kesimli_hali):
        full.append(bpoly(i, cyclic=False))

    return full


def _zigzag_vektorlerini_olustur(verts_list, angle=45, distance=1.0):
    """
    Zigzag için çizgilerini oluşturur.

    :param verts_list: VectorList: Dilimlenecek Poly'nin noktaları
    :param angle: int: Dilimleyici hangi açıda olsun
    :param distance: float: Dilimler arası mesafe ne kadar olsun

    return [(p0, p1), (p0, p1), ...]    -> Lines
    """
    all_verts = []
    for verts in verts_list:
        all_verts.extend(verts)

    min_x = min(all_verts, key=lambda v: v.x).x - .1
    min_y = min(all_verts, key=lambda v: v.y).y - .1
    max_x = max(all_verts, key=lambda v: v.x).x + .1
    max_y = max(all_verts, key=lambda v: v.y).y + .1

    ang = angle % 360
    rad = math.radians(ang)
    # normal = Vector((math.cos(rad), math.sin(rad), 0))

    mod_ang = ang % 180

    slice_lines = []

    if mod_ang < 45:
        # MaxY'den MinY'ye
        first_point = Vector((min_x, max_y, 0))
        last_point = Vector((max_x, max_y + math.tan(rad) * (max_x - min_x), 0))
        step_vector = Vector((0, -distance / math.sin(math.radians(90) - rad), 0))

        while last_point.y >= min_y:
            # slice_lines.append(first_point.copy())
            # slice_lines.append(last_point.copy())
            slice_lines.append((first_point.copy(), last_point.copy()))

            first_point += step_vector
            last_point += step_vector

    elif mod_ang < 90:
        # MinX'den MaxX'e
        first_point = Vector((min_x, max_y, 0))
        last_point = Vector((min_x - (max_y - min_y) / math.tan(rad), min_y, 0))
        step_vector = Vector((distance / math.sin(rad), 0, 0))

        while last_point.x <= max_x:
            # slice_lines.append(first_point.copy())
            # slice_lines.append(last_point.copy())
            slice_lines.append((first_point.copy(), last_point.copy()))

            first_point += step_vector
            last_point += step_vector

    return slice_lines


def _zigzagda_kesisimlere_nokta_ekle(verts_list, zigzag_lines):
    """
    Zigzag için çizgilerinin kesişim yerlerine nokta ekler

    :param verts_list: VectorList: Ana Poly'nin noktaları
    :param zigzag_lines: [(p0, p1), (p0, p1), ...]: LineList

    return [ [p0, p1, p2, p3], [p0, p1], ]
    """
    kesimler = []
    for s0, s1 in zigzag_lines:
        kesisiy = []

        for verts in verts_list:
            for i in range(len(verts)):
                v0 = verts[i - 1]
                v1 = verts[i]

                o = intersect_line_line_2d(s0, s1, v0, v1)

                if o and o != v1.xy:
                    ratio = intersect_point_line(o, v0, v1)[1]
                    kesisiy.append(v0.lerp(v1, ratio))

        # Eğer tekli bir değer çıkarsa, kesişimi atla
        if len(kesisiy) % 2 != 0:
            continue

        # Çizgi üzerinde doğru sıraya koy
        kesisiy.sort(key=lambda x: intersect_point_line(x, s0, s1)[1])

        # Grupla
        # grup = [(v0, v1) for v0, v1 in zip(kesisiy[0::2], kesisiy[1::2])]
        # print(grup)
        # kesimler.append(grup)
        kesimler.append(kesisiy)

    return kesimler


def _zigzag_cizgilerini_birlestir(verts_list, zigzag_lines):
    """Gruplanmış çizgileri uygun olan uçlarından birleştir.

    :param verts_list: VectorList: Ana Poly'nin noktaları
    :param zigzag_lines: [(p0, p1), (p0, p1), ...]: LineList
    """
    # TODO Burada birleştirme işleminde düzenleme yapalım. Çünkü tek çizgi halinde kalanlar çok oluyor.

    parts = []
    parca = []
    p_ind = 0

    while any(zigzag_lines):
        line_points = zigzag_lines[p_ind]

        # İçerikte nokta yoksa, son parçayı paketle.
        if len(line_points) < 2:
            if parca:
                parts.append(parca)
                parca = []
            line_points.clear()

        # Parçanın içi henüz boşsa, ilk çizginin ilk iki noktasını ekle
        elif not parca:
            parca.extend(line_points[:2])
            line_points.remove(parca[0])
            line_points.remove(parca[1])

        # Parçaya mümkünse diğer noktaları eklemeye çalış
        else:
            # Son Nokta
            v_son = parca[-1]

            # En yakın mesafe
            l_min_dist = math.inf

            # Şimdi ele alacağımız nokta
            v_cur = line_points[0]

            # Önceki noktaya, şimdi ele aldığımız noktalar arasındaki en yakın olanını bul
            for v in line_points:

                for verts in verts_list:
                    if (v - v_son).length < l_min_dist and not verts.is_intersect_line(v, v_son):
                        # not is_2_polylines_intersect([v, v_son], verts_main, verts1_cyclic=False):
                        l_min_dist = (v - v_son).length
                        v_cur = v

            # Şimdi bulduğumuz noktaya bağlı nokta bulunur.
            v_cur_ind = line_points.index(v_cur)
            v_aft = line_points[v_cur_ind + (1, -1)[v_cur_ind % 2]]

            ok = True

            for verts in verts_list:

                if verts.is_intersect_line(v_son, v_cur):
                    ok = False
                    break
                # Yeni çizginin, Objedeki çizgilerle kesişip kesişmediğine bak
                # for i in range(len(verts)):
##
                #     if intersect_line_line_2d(v_son, v_cur, verts[i - 1], verts[i]):
                #         ok = False
                #         break

            # Kesişme varsa, son parçayı paketle ve yeni parça oluştur
            if not ok:
                parts.append(parca)
                parca = []

            parca.extend((v_cur, v_aft))

            line_points.remove(v_cur)
            line_points.remove(v_aft)

        p_ind += 1
        if len(zigzag_lines) <= p_ind:
            zigzag_lines.reverse()
            p_ind = 0

    if parca:
        parts.append(parca)

    return parts


# ############################################### ###########################
# ############################################### Poly içini Offsetle doldur
def add_round(lineA_p2, lineA_p1, lineB_p1, lineB_p2, center, angle, is_intersect=False):
    """İki çizgi eğer kesişmiyorsa arasında ki boşluğa çember dilimi ekler.

    :param lineA_p2: Vector: 1. Çizginin başladığı nokta
    :param lineA_p1: Vector: 1. Çizginin çember başlatacak noktası
    :param lineB_p1: Vector: 2. Çizginin çember bitirecek noktası
    :param lineB_p2: Vector: 2. Çizginin bittiği nokta
    :param center: Vector: 2.Merkez noktası
    :param angle: Vector: Merkez açısı
    :param is_intersect: bool: Kesişip kesişmediği bilgisi hazır da gelebilir

    :return VectorList:
    """
    if is_same_point(lineA_p1, lineB_p1):
        return []

    if is_intersect or not intersect_line_line_2d(lineB_p1, lineB_p2, lineA_p1, lineA_p2):
        ang = (angle - math.pi)

        dist = (center - lineA_p1).length

        # TODO çevre ve step hesap kısmını tekrar düzenlemek gerekebilir
        # Çember dilimi çevre uzunluğu bulunur
        cevre = abs(2 * ang * dist)

        if cevre < dist:
            # TODO Bu iki satır tehlikeli ama gancak böyle oluyor. Daha iyisini deneyelim
            # if angle > 0:
            #     return []
            kesisiy = intersect_line_line(lineB_p1, lineB_p2, lineA_p1, lineA_p2)
            return [lineA_p1, kesisiy[0].freeze(), lineB_p1] if kesisiy else []
        elif cevre < 2 * dist:
            step = 2
        elif cevre < 5 * dist:
            step = 5
        else:
            step = 8
            # return [intersect_line_line(lineA_p2, lineA_p1, lineB_p1, lineB_p2)[0].freeze()]

        bm = bmesh.new()
        bmesh.ops.spin(bm,
                       geom=[bm.verts.new(lineA_p1)],
                       axis=(0, 0, -1),
                       steps=step,
                       angle=ang,
                       cent=center
                       )

        verts = [v.co.xyz.freeze() for v in bm.verts[1:-1]]
        # print(verts)

        bm.free()

        return verts

    return []


@add_screen_decorator
def offset_2d(verts, distance=.2):
    """2D ortamda Poly'ye offset uygular"""

    # bpoly değilse, bpoly'ye dönüştür ve yönünü hesapla
    if type(verts) != bpoly:
        verts = bpoly(verts, yon=-1 if distance > 0 else 1)
    else:
        verts.fix()

    # return [verts]
    if len(verts) < 3:
        return []

    # Her noktadaki açı bulunur
    angles = angles_in_verts(verts)

    # İç mi dış mı olduğu düzenlenir.
    ori = verts.yon * (1 if normal(verts).z > 0 else -1)

    ilkparca = bpoly([])
    parts = [ilkparca]
    last_i = len(verts) - 1

    for i in range(len(verts)):
        if not i and not verts.cyclic:
            continue

        v0 = verts[i - 1]
        v1 = verts[i]

        # if (v0-v1).length < distance and
        p = (v0 - v1).orthogonal()

        yon_duzelt = -1 if p.cross(v0 - v1).z < 0 else 1
        p.z = 0
        p.normalize()

        p0 = (v0 - ori * yon_duzelt * p * distance).freeze()
        p1 = (v1 - ori * yon_duzelt * p * distance).freeze()

        # Eğer son noktaları koyuyorsak ve son çizgi uygun değilse atlıyoruz
        if i == last_i and not verts.cyclic and len(ilkparca) > 1 \
                and angles[i - 1] < math.pi and (p0 - p1).length < distance:
            continue

        if len(ilkparca) > 1:
            """"""
            # Şimdi oluşturacağımız çizgi, bir önceki çizgiyi kesiyor mu?
            keser = intersect_line_line_2d(ilkparca[-2], ilkparca[-1], p0, p1)

            # Kesiyorsa, önceki çizginin bitimini ve şimdiki çizginin başlangıcını kesişim yerinde birleştir
            if keser:
                # print("Keser", ilkparca[-2].xy, ilkparca[-1].xy, p0.xy, p1.xy)
                ilkparca.pop(-1)
                p0 = Vector((*keser, verts[i - 1].z)).freeze()
                # ilkparca[-1] = p0 = Vector((*keser, verts[i-1].z)).freeze()
            else:
                pass
                # print(i, "Kesmez", len(ilkparca))
                # elif False:
                # Kesmiyor ise, p0 değiştirilir ve e1 noktasına p0-p1 çizgisindeki en yakın bulunur
                c0, ratio0 = intersect_point_line(ilkparca[-1], p0, p1)
                c1, ratio1 = intersect_point_line(p1, ilkparca[-1], ilkparca[-2])

                # Bir önceki noktanın(e1), en yakın olduğu yer şimdiki çizginin üzerindeyse
                # AnaPoly'de önceki noktanın açısı, 180'e yakınsa,
                # Şimdiki çizgi, şimdiye kadarki çizgilerle kesişmiyorsa
                # Şimdiki çizginin iki noktası da, AnaPoly'ye distance'dan daha yakınsa
                # Şimdiki çizginin iki noktası da, önceki çizgilere yakınsa
                # TODO Buraya alternatif çözüm ara
                """"""
                if 0 < ratio0 < 1 and angles[i - 1] > math.radians(135) and \
                        (ilkparca[-1] - ilkparca[-2]).length < distance and \
                        not ilkparca.is_intersect(bpoly((p0, p1))) and \
                        not verts.is_intersect(bpoly((p0, p1))) and \
                        verts.is_close_distance_to_points(bpoly((ilkparca[-1], ilkparca[-2])), distance) and \
                        ilkparca.is_close_distance_to_points(bpoly((ilkparca[-1], ilkparca[-2])), distance):
                    # if False:
                    """
                    ilkparca.pop(-1)
                    ilkparca.pop(-1)"""

                # Şimdiki ekleyeceğimiz son noktanın, önceki çizgiye en yakın olduğu yer çizginin üzerindeyse
                # ve aradaki mesafe distance'dan kısaysa
                elif 0 < ratio1 < 1 and angles[i - 1] > math.radians(135) and (p0 - ilkparca[-1]).length < distance:

                    # elif False:
                    ilkparca.insert(-1, c1.freeze())

                else:
                    # elif False:
                    # """"""
                    # Eğer kesişim yoksa iki çizgi arasına Round ekler
                    ps = add_round(ilkparca[-2], ilkparca[-1], p0, p1, verts[i - 1], angles[i - 1], is_intersect=True)

                    # Eğer 3 nokta geldiyse, anlıyoruz ki bunlar -> ilkparca[-2], kesisim, p0 'dır
                    # Ortadaki kesisim'i ekliyoruz sadece
                    # print(i, "Girdi", len(ilkparca), ps)
                    if len(ps) == 3:
                        ilkparca.pop(-1)
                        p0 = ps[1]
                    else:
                        ilkparca.extend(ps)
                        # print(i, "Girdi", len(ilkparca))

        ilkparca.append(p0)
        ilkparca.append(p1)

        # Eğer son noktaları koyuyorsak
        if len(ilkparca) > 1 and i == last_i and verts.cyclic:
            ps = add_round(p0, p1, ilkparca[0], ilkparca[1], verts[i], angles[i])

            # Eğer 3 nokta geldiyse, anlıyoruz ki bunlar -> (ilkparca[-2], kesisim, p0) 'dır
            # Ortadaki kesisim'i ekliyoruz sadece
            if len(ps) == 3:
                ilkparca.pop(-1)
                ilkparca.append(ps[1])
            else:
                ilkparca.extend(ps)

    ilkparca.disolve_doubles()
    """"""
    for par in new_parts_from_intersect_self(ilkparca, verts.cyclic):
        par = bpoly(par, copy_conf=verts, fix=False)
        par.disolve_doubles()
        parts.append(par)

    ilkparca.disolve_doubles()

    # return parts
    parcalar_son = []

    # Parçaların uygunluğu son kez kontrol edilir.
    for i in range(len(parts) - 1, -1, -1):

        parca = parts[i]

        # parca başka parçanın içinde varsa diğer parçadan silinir.
        for j, k in enumerate(parts):
            if i == j or len(parca) > len(k):
                continue
            hepsi_var = True
            for u in parca:
                if u not in k:
                    hepsi_var = False
                    break
            if hepsi_var:
                for u in parca:
                    if u in k:
                        k.remove(u)

        """"""
        # 3 noktadan az varsa
        # 3 noktalının alanı küçükse
        # Parça objeyi kesiyorsa
        # Parça objeye distanceden daha yakınsa
        if len(parca) < 3 or \
                (len(parca) == 3 and area_tri(*parca) < .0001) or \
                verts.is_close_distance_to_points(parca, distance) or \
                verts.is_intersect(parca):

            continue

        parcalar_son.append(parca)

    # return parts
    return parcalar_son


# ############################################### ###########################
# ############################################### ###########################
# TODO
#   -> 2 Poly kesişimi
#   -> 2 Poly Birleşimi
#   -> 2 Poly Farkı
#

if __name__ == "__main__":
    orient = -1
    obj = bpy.context.active_object
    # vertices = [i.co.xyz for i in obj.data.splines[0].points]
    # offset_splines(obj.data.splines, distance=.01, add_screen=True)
    # offset_spline(obj.data.splines[0], distance=-.2, add_screen=True)
    # offset_2d(obj.data.splines[0], distance=.2, add_screen=True)
    # clearance_offset_splines(obj.data.splines, .2, add_screen=True)
    clearance_zigzag(obj.data.splines, distance=.2,  add_screen=True)

    # vs = clearance_zigzag(bpoly(vertices, cyclic=True), distance=.2,  add_screen=True)
    # parcas = offset_splines(obj.data.splines, add_screen=True, orientation=1)
    # mp = is_inside(vertices, Vector((16.4917, -17.1315, 0)))

    # verts2 = [i.co.xyz for i in obj.data.splines[1].points]
    # _cakisan_noktayi_geri_cek(vertices, verts2)

    # TODO Offset uygulandıktan sonraki halleri de kendi aralarında kesişebiliyor, bunu da işleyebilsin
    # # İki Poly kesişiyorsa, kesişim yerinden birleştir ve sonra offset uygula
    # if is_2_polylines_intersect(vertices, verts2):
    #     vertices = union_2poly(vertices, verts2, True, True)
    #     vs = offset_2d(vertices, .2, orientation)

    # # Poly1, Poly2'nin içinde mi?
    # elif is_inside_poly_poly(vertices, verts2):
    #     vs = offset_2d(vertices, .2, orientation)
    #     vs.extend(offset_2d(verts2, .2, -orientation))

    # # Poly2, Poly1'nin içinde mi?
    # elif is_inside_poly_poly(verts2, vertices):
    #     vs = offset_2d(vertices, .2, -orientation)
    #     vs.extend(offset_2d(verts2, .2, orientation))

    # # Hiçbirisi değilse
    # else:
    #     vs = offset_2d(vertices, .2, orientation)
    #     vs.extend(offset_2d(verts2, .2, orientation))

    # new_poly_curve(vs, add_screen=True)
    # is_inside(vertices, j)

    # vs = clearance_offset_spline(bpoly(vertices, cyclic=True), distance=.2, add_screen=True)
    # vs = offset_2d(vertices, .001, 1)
    # vs = offset_2d(bpoly(vertices, cyclic=True), .2, -1)
    #vs =
    # print(np)

    # parcas = offset_2d(vertices)
    # new_poly_curve([parcas], add_screen=True)
    # correct_angles(vertices)
    # disolve_doubles(vertices, True)
    # clear_zero_angle(vertices, True)
    # clear_linear_points(vertices, True)
    # new_poly_curve([vertices], add_screen=True)

    # vs = spline_to_poly(obj.data.splines[0])
    # new_poly_curve([vs],add_screen=True)
