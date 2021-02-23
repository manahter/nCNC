import math
from .angles import angle_3p
from mathutils.geometry import intersect_line_line_2d, intersect_point_line, intersect_line_line
from mathutils import Vector


def offset_splines2(splines, distance=.2, orientation=-1, add_screen=True):
    """
    :param splines: obj.data.splines: gibi
    :param distance: float: Mesafe
    :param orientation: int: -1 or +1 -> iç veya dış offset
    :param add_screen: bool:
        True -> Ekrana ekle ve objeyi döndür
        False-> Ekrana ekleme, polyleri döndür

    return [VectorList, VectorList...] or CurveObje: Spline'ların offset almış hali
    """
    parcalar = []
    cyclics = []
    for s in splines:
        parcas = offset_spline(s, distance, orientation, add_screen=False)
        parcalar.extend(parcas)

        # TODO cyclic düzenle
        cyclics.extend([s.use_cyclic_u for i in range(len(parcas))])

    if add_screen:
        return new_poly_curve(parcalar, add_screen=True)

    return parcalar


def bul_kesis_line_poly(p0, p1, poly, cyclic=False):
    """Line ile Poly'nin kesişimini bulur
    :param p0: Vector: Line'ın 0. noktası
    :param p1: Vector: Line'ın 1. noktası
    :param poly: Vectors: Poly verts
    :param cyclic: bool: Kapalı mı?

    return [(poly_ind0, poly_ind1), ...]
    """
    # [(index, Vector), ...]
    kesisim = []
    for i in range(len(poly)):
        if not i and not cyclic:
            continue
        v0 = poly[i - 1]
        v1 = poly[i]

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

    print("Kesişimler", kesisim)
    return kesisim


def _cakisan_noktayi_geri_cek(verts1, verts2, mm=.001):
    """2 Poly'de çakışan noktaları bulur. Yani sadece noktaların aynılığı kontrol edilir. Çizgi kesişimlerine bakılmaz.

    return: indexs -> [(Poly1_index,..), (Poly2_index,..)]"""
    inds = []

    for i in range(len(verts1)):

        v0 = verts1[i]

        for j in range(len(verts2)):

            if is_same_point(v0, verts2[j]):
                verts2[j] = verts2[j].lerp(verts2[j - 1], mm / (verts2[j] - verts2[j - 1]).length)


def closest_point_on_poly(verts, p):
    """p'nin poly'ye en yakın olduğu nokta"""

    min_p = None
    normal = None

    # Poly cyclic varsayılır
    for i in range(len(verts)):
        # if not min_p:
        #     min_p = verts[i]
        #     continue
        #
        # if (verts[i]-p).length < (min_p-p).length:
        #     min_p = verts[i]
        # continue

        o, ratio = intersect_point_line(p, verts[i - 1], verts[i])

        # print("Ratio", ratio)
        if 1 < ratio or ratio < 0:
            # print("Heeeeeeeeeeee")
            o = verts[i - 1] if (p - verts[i - 1]).length < (p - verts[i]).length else verts[i]

        if not min_p:
            min_p = o
            normal = (o - p).normalized()
            continue

        if (o - p).length < (min_p - p).length:
            min_p = o
            normal = (o - p).normalized()

    return min_p, normal


def correct_angles(verts, distance=.2, cyclic=True):
    """distance'ın giremediği köşeleri düzelt"""
    # 90 dereceden dar açı tespit edilir ve indexi alınır
    verts.disolve_doubles()
    det = detect_acute_angle(verts, cyclic)
    while det:
        len_verts = len(verts)

        ind1, ang = det
        ind2 = ind1 + 1 if ind1 + 1 < len_verts else 0
        ind0 = len_verts - 1 if ind1 - 1 < 0 else ind1 - 1

        p0 = verts[ind0]
        p1 = verts[ind1]
        p2 = verts[ind2]

        tan = math.tan(ang / 2)

        edge = distance / tan if tan else distance
        len_p0 = (p1 - p0).length
        len_p2 = (p1 - p2).length

        ratio0 = edge / len_p0 if len_p0 else -1
        ratio2 = edge / len_p2 if len_p2 else -1

        p1_sil = False
        if 0 <= ratio2 <= 1:
            np0 = p1.lerp(p2, ratio2)
            verts.insert(ind2, np0)
        else:
            p1_sil = True
            verts.pop(ind1)

        # p1'den önceki ve sonraki nokta
        if 0 <= ratio0 <= 1:
            np2 = p1.lerp(p0, ratio0)
            verts.insert(ind1, np2)
        elif not p1_sil:
            verts.pop(ind1)

        verts.disolve_doubles()
        det = detect_acute_angle(verts, cyclic)


def detect_acute_angle(verts, cyclic=True):
    """Dar açı tara. Noktaları gezer, dar açı bulduğu gibi indexini döndürür"""

    len_verts = len(verts) - (0 if cyclic else 1)
    rad90 = math.radians(90)
    rad270 = math.radians(270)

    for i in range(len(verts)):
        if not i and not cyclic:
            continue
        if i + 1 == len_verts and cyclic:
            ang = angle_3p(verts[i - 1], verts[i], verts[0])
        else:
            ang = angle_3p(verts[i - 1], verts[i], verts[i + 1])
        if ang < rad90:  # or ang > rad270:
            return i, ang

    return


def is_2_polylines_intersect(verts1, verts2, in_2d=True, verts1_cyclic=True, verts2_cyclic=True):
    """İki poly çizgileri arasında kesişen çizgi var mı?

    :param verts1: VectorList: 1. Poly'nin noktaları
    :param verts2: VectorList: 2. Poly'nin noktaları
    :param in_2d: bool: Kesişim 2D olarak mı incelensin?
    :param verts1_cyclic: bool: Poly1 Kapalı mı?
    :param verts2_cyclic: bool: Poly2 Kapalı mı?

    return bool:
        False-> Kesişmez
    """

    for t in range(len(verts2)):
        if not t and not verts2_cyclic:
            continue
        t0 = verts2[t - 1]
        t1 = verts2[t]
        for m in range(len(verts1)):
            if not m and not verts1_cyclic:
                continue

            m0 = verts1[m - 1]
            m1 = verts1[m]

            # print(m0, m1, t0, t1)

            if in_2d:
                if intersect_line_line_2d(t0, t1, m0, m1):
                    return True
            else:
                # TODO Henüz 3D'de kesişim kısmı kodlanmadı
                intersect_line_line(t0, t1, m0, m1)

    return False


def is_close_distance_to_points(verts_main, verts_target, distance, cyclic=True):
    """Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
    verts_target'daki noktalar sırayla ele alınıp, verts_main'deki noktalara istenen distance'dan yakın mı kontrol
    edilir.

    :param verts_main: VectorList: Ana Poly'nin noktaları
    :param verts_target: VectorList: İncelenen Poly'nin noktaları
    :param distance: float: İncelenecek mesafe, uzaklık
    :param cyclic: bool: verts_main kapalı mı

    return bool:
        True -> Evet yakın nokta/lar var.
        False-> Hayır hiçbir nokta yakın değil.
    """
    # Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
    for t in verts_target:
        for m in range(len(verts_main)):
            if not m and not cyclic:
                continue
            p0 = verts_main[m - 1]
            p1 = verts_main[m]
            c, ratio = intersect_point_line(t, p0, p1)
            mes = (c - t).length
            if 1 >= ratio >= 0 and (mes + .001 < distance):
                return True

    return False


# #################################################################################### Clearance
def clearance_offset_splines(splines, distance=.2, add_screen=False):
    parts = []
    for s in splines:
        parts.extend(clearance_offset_spline(s, distance, add_screen=False))

    if add_screen:
        return new_poly_curve(parts, add_screen=True)

    return parts


def clearance_offset_spline(spline, distance=.2, add_screen=False):
    verts = bpoly(spline, yon=orientation) if type(spline) == Spline else spline
    parts = clearance_offset(verts, distance)

    if add_screen:
        return new_poly_curve(parts, add_screen=True)

    return parts


def clearance_offset(verts, distance=.2):
    """Offset yapa yapa, şeklin içini doldurur"""
    parts = []

    for vs in offset_2d(verts, distance, -1):
        parts.append(vs)
        parts.extend(clearance_offset(vs, distance))
    return parts



def yeni_parcalar_overlaps(verts0, verts1):
    kesisen_noktalar = list(set(verts0) & set(verts1))

    if len(kesisen_noktalar) < 2:
        return

    # verts0 çakışan noktalardan parçalarına ayrılır
    inds0 = [verts0.index(kp) for kp in kesisen_noktalar]
    inds0.sort()
    # print("verts0", verts0)
    # print("inds0", inds0)
    parts0 = [verts0[inds0[i-1]: inds0[i] + 1] for i in range(len(inds0))]
    # print("parts0", parts0)

    # verts1 çakışan noktalardan parçalarına ayrılır
    inds1 = [verts1.index(kp) for kp in kesisen_noktalar]
    inds1.sort()
    # print("inds1", inds1)
    parts1 = [verts1[inds1[i-1]: inds1[i] + 1] for i in range(len(inds1))]
    # print("parts1", parts1)

    parts = []
    # Tüm parçaları dön ve uc uca birşebilenleri birleştir
    for p0 in parts0:
        # print("p0", p0)
        for p1 in parts1:
            # print("p1", p1)

            if p0[0] == p1[-1]:
                parts.append(p0 + p1)
                parts1.remove(p1)
                break
            elif p0[0] == p1[0]:
                p1.reverse()
                parts.append(p0 + p1)
                parts1.remove(p1)
                break
            elif p0[-1] == p1[0]:
                parts.append(p1 + p0)
                parts1.remove(p1)
                break
            elif p0[-1] == p1[-1]:
                p1.reverse()
                parts.append(p1 + p0)
                parts1.remove(p1)
                break

    parts = [bpoly(i, copy_conf=verts0) for i in parts]

    # Örtüşen noktaları geri çek
    # for k in kesisen_noktalar:
    #     for part in parts:
    #         if k in part:
    #             i = part.index(k)
    #             part[i] = k.lerp(part[i-1], .001 / (k - part[i-1]).length).freeze()

    # print(kesisen_noktalar)
    return parts

