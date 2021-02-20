"""
angle_3p            : 3 nokta arasındaki açıyı verir
calc_verts_angles   : Noktalardaki açıları verir
"""
import math


def angle_3p(p_first, p_center, p_last, degree=False, tolerance=.0001):
    """3 noktanın ortasında oluşan açıyı döndürür

    :param p_first: Vector: Başlangıç noktası
    :param p_center: Vector: Açısı hesaplanacak nokta - Köşe noktası
    :param p_last: Vector: Bitiş noktası
    :param degree: bool: Dönüş değeri derece'mi olsun?
    :param tolerance: float: Aynılığı karşılaştırırken tolere edilecek yanılma payı.

    :return bool: radian or degree
    """
    v1 = (p_first - p_center).normalized()
    v2 = (p_last - p_center).normalized()

    # iki doğru da aynı yöndeyse açı 180 derecedir. TODO Burayı düzelt, açı 0 derece de olabilir
    if (v1 + v2).length < tolerance or v2.length < tolerance:
        angle = math.pi
    elif (v1 - v2).length < tolerance or v1.length < tolerance:
        angle = 0
    else:
        angle = v1.angle(v2)

        # İç / Dış açı konusunu bu kısımda çözüyoruz
        # Sağa or Sola dönme durumuna göre, iç açıyı buluyor
        if v1.cross(v2).z > 0:
            angle = math.radians(360) - angle

    return math.degrees(angle) if degree else angle


def angles_in_verts(verts, cyclic=True, degree=False):
    """Köşelerin açılarını bulur. Aynı sırayla listeye kaydeder.
    :param verts: VectorList: Noktalar
    :param cyclic: bool: Kapalı mı?
    :param degree: bool: Dönüş değeri derece'mi olsun?

    return radianList: Noktalarda oluşan açılar. cyclic değilse ilk ve son nokta 90 derece olara döner

    """
    if len(verts) < 3:
        return []

    # Son noktanın indexi
    last_vert = len(verts) - 1

    angles = []

    # Her noktanın açısı bulunur
    for i in range(len(verts)):
        if not i and not cyclic:
            angles.append(math.radians(90))
            continue

        # Önceki, Şimdiki, Sonraki nokta
        p0 = verts[i - 1]
        p1 = verts[i]
        p2 = verts[i + 1 if i != last_vert else 0]

        angles.append(angle_3p(p0, p1, p2, degree=degree))
        # print("angle", math.degrees(angles[-1]))

    return angles
