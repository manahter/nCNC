import math
import bmesh
from mathutils.geometry import area_tri, normal, intersect_line_line_2d, intersect_point_line, intersect_line_line
from mathutils import Vector
from bpy.types import Spline

from .is_ import *
from .angles import angles_in_verts
from .intersect import (
    new_parts_from_intersect_self,
    new_parts_from_overlaps,
    add_point_to_intersects
)
from .common import *

__all__ = [
    "offset_splines",
    "offset_spline",
    "offset_2d"
]


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

        # if type(s) in (list, Spline):
        if not isinstance(s, bpoly):
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

            # TODO iki poly'nin örtüşen noktaları varsa, bu noktaların sayısı önemli, iki ve katlarıysa, bu noktalardan
            #   yeni parçalar oluştur. Veya başka birşey düşün

            # Örtüşen noktalar
            kesis = list(set(verts0) & set(verts1))

            # TODO Çakışan noktalar dışındaki noktalar şeklin içindeyse, fillet uygula

            """"""
            # Çakışan noktalar dışındakiler objenin içindeyse çakışan noktalarda PAH kır
            if len(kesis) and yon > 0:
                # verts1, verts0 şeklinin içinde mi? (Kesişim noktaları hariç)
                if verts0.is_inside_bpoly(verts1, except_verts=kesis):
                    verts1.chamfer(kesis, size=.005)

                else:#if verts1.is_inside_bpoly(verts0, except_verts=kesis):
                    verts0.chamfer(kesis, size=.005)

                # parts_orj.extend(yeni_parcalar_overlaps(verts0, verts1))
                # verts0.clear()
                # verts1.clear()

            # İki Poly kesişiyorsa, kesişim yerinden birleştir
            if verts0.is_intersect(verts1):
                # verts0 ve verts 1'i birleştir
                verts0.weld(verts1)
                verts0.disolve_doubles()
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
    # return parts_orj

    # Offsetler oluşturulur
    parts = []
    for verts in parts_orj:
        for parca in offset_spline(verts, distance):
            parts.append(
                bpoly(parca, copy_conf=verts)
            )
    # return parts
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
def offset_2d(verts, distance=.2):
    """2D ortamda Poly'ye offset uygular"""

    # bpoly değilse, bpoly'ye dönüştür ve yönünü hesapla
    if type(verts) != bpoly:
        verts = bpoly(verts, yon=-1 if distance > 0 else 1)
    else:
        verts.fix()

    # TODO Kendi içinde çakışan noktaları geri çek
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
                ilkparca.pop(-1)
                p0 = Vector((*keser, verts[i - 1].z)).freeze()
                # ilkparca[-1] = p0 = Vector((*keser, verts[i-1].z)).freeze()
            else:
                pass
                # Kesmiyor ise, p0 değiştirilir ve e1 noktasına p0-p1 çizgisindeki en yakın bulunur
                c0, ratio0 = intersect_point_line(ilkparca[-1], p0, p1)
                c1, ratio1 = intersect_point_line(p1, ilkparca[-1], ilkparca[-2])

                # Bir önceki noktanın(e1), en yakın olduğu yer şimdiki çizginin üzerindeyse
                # AnaPoly'de önceki noktanın açısı, 180'e yakınsa,
                # Şimdiki çizgi, şimdiye kadarki çizgilerle kesişmiyorsa
                # Şimdiki çizginin iki noktası da, AnaPoly'ye distance'dan daha yakınsa
                # Şimdiki çizginin iki noktası da, önceki çizgilere yakınsa
                # TODO Buraya alternatif çözüm ara
                if ori < 0 and 0 < ratio0 < 1 and angles[i - 1] > math.radians(135) and \
                        (ilkparca[-1] - ilkparca[-2]).length < distance and \
                        not ilkparca.is_intersect(bpoly((p0, p1))) and \
                        not verts.is_intersect(bpoly((p0, p1))) and \
                        verts.is_close_distance_to_points(bpoly((ilkparca[-1], ilkparca[-2])), distance) and \
                        ilkparca.is_close_distance_to_points(bpoly((ilkparca[-1], ilkparca[-2])), distance):
                    # if False:
                    """"""
                    ilkparca.pop(-1)
                    ilkparca.pop(-1)

                # Şimdiki ekleyeceğimiz son noktanın, önceki çizgiye en yakın olduğu yer çizginin üzerindeyse
                # ve aradaki mesafe distance'dan kısaysa
                elif 0 < ratio1 < 1 and angles[i - 1] > math.radians(135) and (p0 - ilkparca[-1]).length < distance:

                    # elif False:
                    ilkparca.insert(-1, c1.freeze())

                else:
                    """"""
                    # Eğer kesişim yoksa iki çizgi arasına Round ekler
                    ps = add_round(ilkparca[-2], ilkparca[-1], p0, p1, verts[i - 1], angles[i - 1], is_intersect=True)

                    # Eğer 3 nokta geldiyse, anlıyoruz ki bunlar -> ilkparca[-2], kesisim, p0 'dır
                    # Ortadaki kesisim'i ekliyoruz sadece
                    if len(ps) == 3:
                        ilkparca.pop(-1)
                        p0 = ps[1]
                    else:
                        ilkparca.extend(ps)

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
                (len(parca) == 3 and area_tri(*parca) < .001) or \
                verts.is_close_distance_to_points(parca, distance) or \
                verts.is_intersect(parca):

            continue

        parcalar_son.append(parca)

    # return parts
    return parcalar_son


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

        bm.free()

        return verts

    return []


# TODO İkiden fazla çakışan noktası olan 2 poly'yi birleştirirken, sorun oluşuyor. Buraya bir çözüm bulmamız lazım
if __name__ == "__main__":
    import bpy
    obj = bpy.context.active_object
    # vs0 = bpoly([i.co.xyz for i in obj.data.splines[1].points], cyclic=True, fix=False)
    # vs1 = bpoly([i.co.xyz for i in obj.data.splines[1].points], cyclic=True)

    # from .intersect import _cakisan_nokta_cizgi_uzaklastir

    # snc = _cakisan_nokta_cizgi_uzaklastir(vs0)
    # # snc = yeni_parcalar_overlaps(vs0, vs1)
    # from .common import new_poly_curve

    # new_poly_curve([chamfer(vs0, [vs0[1], vs0[3]])], True)
    # new_poly_curve([vs0], True)
    offset_splines(obj.data.splines, distance=.2, add_screen=True)
