"""
disolve_doubles     : Binik noktaları temizle
clear_linear_points : Aynı doğrudaki ara noktaları temizle
clear_zero_angle    : 0 derece açıları temizle
"""
from .is_ import is_same_point, is_linear_3p


# ############################################### Aşağısı henüz kullanılmadı
import math
from .angles import angle_3p

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
