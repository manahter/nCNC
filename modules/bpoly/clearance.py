import math
from mathutils.geometry import intersect_line_line_2d, intersect_point_line
from mathutils import Vector
from bpy.types import Spline
from .common import *
from .offset import offset_splines

__all__ = [
    "clearance_offset_splines",
    "clearance_zigzag"
]


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

