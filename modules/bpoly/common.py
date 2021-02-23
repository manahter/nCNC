import bpy
from mathutils.geometry import intersect_line_line_2d, intersect_point_line, intersect_line_line
from mathutils import Vector
from bpy.types import Spline

from .is_ import *
from .convert import spline_to_poly
from .intersect import non_intersecting_poly

__all__ = [
    "bpoly",
    "add_screen_decorator"
]


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

    def __getitem__(self, item):
        """Bu değişiklik sayesinde;
        list[-2:3] -> gibi liste aralığını almaya tersten başlanabilecek
        """
        # istenen index, item sayısından büyükse, modunu alıp bakmaya 0 dan devam etsin
        if isinstance(item, int):
            return super().__getitem__(item % len(self))

        # Stop değeri, item sayısından büyükse, kalan itemleri biriktirmeye 0 dan devam etsin
        if isinstance(item, slice) and item.stop and item.stop > len(self):
            stop = item.stop - len(self)

            r0 = super().__getitem__(slice(item.start, None, item.step))
            r1 = super().__getitem__(slice(0, stop, item.step))

            return r0 + r1

        # start değeri 0'dan küçükse ve stop değeri 0'dan büyükse veya
        # start değeri, stop değerinden büyükse
        # Kesişim noktaları 0 olacağı için itemleri bu şekilde biriktir
        if isinstance(item, slice) and item.start and item.stop and \
                ((item.start < 0 and item.stop > 0) or
                 (item.start > item.stop)):
            start = item.start
            stop = item.stop
            step = item.step

            r0 = super().__getitem__(slice(start, None, step))
            r1 = super().__getitem__(slice(0, stop, step))

            return r0 + r1

        return super().__getitem__(item)

    def __setitem__(self, key, value):
        if isinstance(key, int):
            # Key-> index değeri, item sayısından büyük olabilir. Bu durumda başa sararak index'i al
            super().__setitem__(key % len(self), value)

        super().__setitem__(key, value)

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

            ks = other_bpoly.calc_intersect_line(p0, p1)

            # if ks and ks[0][1] in (p0, p1):
            #     pol1_new = other_bpoly[ks[0][0]:] + other_bpoly[:ks[0][0]]
            #     new_list = self[i:] + self[:i] + pol1_new[::-1]

            #     print("Yaa hanım teyze böyl böyle işte")
            #     self.clear()
            #     self.extend(new_list)

            #     return
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

        # Freeze
        self.freeze()

    def freeze(self):
        for i in self:
            try:
                # if not i.is_frozen and not i.is_wrapped:
                i.freeze()
            except:
                pass

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

    def is_inside_bpoly(self, other_bpoly, except_verts=[]):
        """self, other_bpoly şeklinin içinde mi?"""

        for p in other_bpoly:
            if p in except_verts:
                continue

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

    def chamfer(self, verts, size=.01):
        """verts'lere pah kırma uygula"""

        for v in verts:

            while v in self:
                i = self.index(v)
                v0 = self[i - 1]
                v1 = self[i]
                v2 = self[i + 1]

                self[i] = v1.lerp(v2, size / (v1 - v2).length).freeze()
                self.insert(i, v1.lerp(v0, size / (v1 - v0).length).freeze())

        return self

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
