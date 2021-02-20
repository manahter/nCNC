import math
import bpy
from mathutils import Vector
from mathutils.geometry import intersect_line_line_2d, intersect_point_line, intersect_line_line, interpolate_bezier
import mathutils


# ############################################### ###########################
# ############################################### Offset Uygula, Curve oluştur
def new_bezier_curve(beziers, add_screen=False, cyclic=True):
    """Noktalardan yeni bir Poly oluşturulur.

    :param polys: [ [poly_points], [...], ... ] -> Poly pointlerin listesi
    :param add_screen: bool:
        True -> Ekrana ekle ve objeyi döndür
        False-> Ekrana ekleme, curve'ü döndür
    :param cyclic: bool: Kapalı mı?

    return: object or curve
    """
    # Curve Data oluştur
    curve = bpy.data.curves.new("npoly", "CURVE")

    for points in beziers:
        if len(points) < 2:
            continue

        # Poly spline oluştur
        curve.splines.new("BEZIER")

        # ilk ve son nokta eşitse, son noktayı sil
        # if points[0] == points[-1]:
        #     points.pop(-1)

        # Kapalı yap
        curve.splines[-1].use_cyclic_u = cyclic

        # Curve Pointleri al
        curpt = curve.splines[-1].bezier_points

        # Gelen point sayısı kadar Curve'da point oluşturulur
        curpt.add(len(points) // 3 - 1)

        # Gelen pointler Curve'ye eklenir
        for i in range(len(points) // 3):
            j = i * 3
            # if v.xyz != curpt[-1].co.xyz:
            curpt[i].handle_left = points[j]
            curpt[i].co = points[j+1]
            curpt[i].handle_right = points[j+2]

    if add_screen:
        # Obje oluşturlup sahneye eklenir
        obje = bpy.data.objects.new("npoly", curve)
        obje.data.dimensions = '3D'
        bpy.context.scene.collection.objects.link(obje)
        return obje
    return curve


def offset(pointis, distance=.2, orientation=-1, resolution=12):
    """Poly'ye offset uygular ve yeni Poly noktalarını döndürür.

    :param verts: VectorList:    Poly'nin pointleri
    :param distance: float: Mesafe
    :param orientation: int: -1 or +1 -> iç veya dış offset

    return VectorList: Poly'nin offset almnış hali
    """

    verts_calc = []
    verts = []
    # Tüm Bezier pointleri gez ve, handle'ların yerine bezier üzerindeki ilk noktaları al
    for i in range(len(pointis)):
        p0 = pointis[i-1]
        p1 = pointis[i]
        p2 = pointis[i+1] if i + 1 < len(pointis) else pointis[0]

        handle_l = mathutils.geometry.interpolate_bezier(p0.co, p0.handle_right, p1.handle_left, p1.co, resolution)[-2]
        handle_r = mathutils.geometry.interpolate_bezier(p1.co, p1.handle_right, p2.handle_left, p2.co, resolution)[1]

        verts_calc.extend((handle_l, p1.co, handle_r))
        verts.extend((p1.handle_left, p1.co, p1.handle_right))

    # Poly çizgileri kesişmez hale getirilir
    # non_intersecting_poly(verts)

    # İç mi dış mı olduğu düzenlenir.
    orientation *= -1 if mathutils.geometry.normal(verts).z > 0 else 1

    # Peş peşe aynı olan noktaları temizle
    # disolve_doubles(verts)

    # Her noktadaki açı bulunur
    angles = calc_verts_angles(verts, verts_calc, resolution)
    #angles.append(angles[0])

    # Her noktadaki açıortay bulunur
    bisectors = calc_verts_bisector(verts, verts_calc, resolution)
    #bisectors.append(bisectors[0])

    # Üstten beri listenin sonuna ilk noktayı tekrar ekliyoruz çünkü altlarda biryerde çıkan sorunu engelliyoruz böylece
    verts.append(verts[0])

    ilkparca = []
    parcalar = [ilkparca]

    # Tüm açıortay vektörlerini sırayla al
    for j, i in enumerate(bisectors):
        # Elimizde bir dik üçgen olduğunu düşünelim
        # i noktadaki açıyı biliyoruz -> angles[j]
        # Açının yanındaki kenar uzunluğu -> distance
        # Açıortay vektörünün uzunluğunu hipotenüs olarak düşünelim ve bunu bulalım
        # Sonra açıortay doğrultusunda, hipotenüs kadar uzat
        # Kısaca OFFSETI BUL
        # açı 180'den büyükse, karşı açıyı kullan (360'dan çıkart)

        if angles[j] > math.radians(180):
            angle = math.radians(360) - angles[j]
            ti = (distance / math.sin(angle / 2))
            v = verts[j] - i * ti * orientation
        else:
            ti = (distance / math.sin(angles[j] / 2))
            v = verts[j] + i * ti * orientation

        # handle = j % 3

        # if handle == 0:
        #     pass
        #     # e1 = ilkparca[-1]
        #     # e1.lerp(v)
        # elif handle == 2:
        #     e1 = ilkparca[-1]
        #     len_kose = (verts[j] - v).length
        #     len_hndl = (v - e1).length
        #     kac_kati = len_hndl / len_kose
        #     len_kose = ((kac_kati + 1) * len_kose) / kac_kati

        #     v = v.lerp(e1,  distance * len_kose / len_hndl)



        # elif di == 0:
        #     to = (verts[j] - verts[j+1]).orthogonal()
        #     # if mathutils.geometry.normal([verts[j], verts[j+1], verts[j+2]]).cross(to).z > 0:  # * mathutils.geometry.normal(verts).z > 0:
        #     # if angles[j+1] > math.radians(180):  # * mathutils.geometry.normal(verts).z > 0:
        #     if to.z < 0:  # * mathutils.geometry.normal(verts).z > 0:
        #         to *= -1
        #     else:
        #         to *= 1

        #     to.z = 0

        #     v = verts[j] - to.normalized() * distance

        # else:
        #     to = (verts[j-1] - verts[j]).orthogonal()
        #     # if mathutils.geometry.normal([verts[j-2], verts[j-1], verts[j]]).cross(to).z > 0:   # * mathutils.geometry.normal(verts).z > 0:
        #     if to.z < 0:   # * mathutils.geometry.normal(verts).z > 0:
        #         to *= -1
        #     else:
        #         to *= 1

        #     to.z = 0

        #     v = verts[j] + to.normalized() * distance

        # TODO!!! Geri çekmede bazı yerlerde sorun yaşıyoruz, bunu çözelim
        # ##########################################################
        # Bir Önceki noktaya bak, içbükey mi, Dar açılıysa, geri çek
        # ##########################################################
        # if len(ilkparca) > 4:
        """
        if len(ilkparca) > 4 and orientation > 0:   # TODO -> Buraya geçici olarak orientation ekledik
            # Eklediğimiz son 2 noktayı alıyoruz
            e1 = ilkparca[-1]
            e2 = ilkparca[-2]

            # Eklediğimiz sondan ikinci noktayı, ama e1'den farklıysa alıyoruz. Farklı değilse, daha önceki nokta alınır
            for t in ilkparca[::-1]:
                if t != e1:
                    e2 = t
                    break

            # Şimdi ekleyeceğimiz nokta ile son iki noktayı alıp, son noktada oluşan açıyı buluyoruz
            ang = calc_verts_angles([e2, e1, v])[1]

            # Eğer son noktadaki açı 90 dereceden küçükse, geri çekmek gerekebilir. Şimdi onu inceliyoruz.
            if ang < math.radians(90):

                # Noktadan çizgiye mesafe kontrolü
                # Objedeki çizgileri sırayla geziyoruz
                for n in range(len(verts)):
                    if not n:
                        continue

                    # Objedeki sıradaki 2 nokta alınır
                    p0 = verts[n-1]
                    p1 = verts[n]

                    # Eklediğimiz son noktanın obje çizgisine mesafesi bulunur
                    c, ratio = intersect_point_line(e1, p0, p1)

                    # Mesafe distance'den küçükse, Son nokta geri çekilir.
                    mes = (c - e1).length
                    if (1 >= ratio >= 0) and (mes + .01 < distance): # and (angles[j] < math.radians(180)):
                        # Son noktadan şimdiki noktaya olan vektör (Kenar 1)
                        v1 = v - e1
                        # Objedeki yakın olduğumuz kenarın vektörü (Kenar 2)
                        v2 = p0 - p1

                        # Bu iki kenar arasındaki açı
                        ang = v1.angle(v2)

                        # Son noktadan şimdiki noktaya olan kenar ile objedeki yakın kenarın kesiştiği nokta
                        ya = intersect_line_line(e1, v, p0, p1)[0]

                        # Distance nokta, oluşturğumuz kenarın neresine geliyor (oran)
                        ratio = abs(distance / math.sin(ang)) / (ya - v).length
                        ilkparca[-1] = ya.lerp(v, ratio)
"""
        ilkparca.append(v)

        # ##########################################################
        # Kesişen çizgi varsa, kesişen kısımlarından parçalara ayır
        # parts = split_parts_from_intersect_in_self(ilkparca)
        # if parts:

        #     # Eğer parçaların herhangi birisi, distance'den daha yakınsa ekleme.
        #     for p in parts:
        #         if not is_close_distance_to_points(verts, p, distance):
        #             parcalar.append(p)

    parcalar_son = []

    # Parçaların uygunluğu son kez kontrol edilir.
    for parca in parcalar:

        # parca başka parçanın içinde varsa diğer parçadan silinir.
        for k in parcalar:
            if parca == k or len(parca) > len(k):
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

        # Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
        # Yakın değilse bu parçayı ekle. Evet parça uygundur ve eklenebilir
        if len(parca) < 3:# or is_close_distance_to_points(verts, parca, distance) or is_2_poly_intersect(verts, parca):
            continue

        parcalar_son.append(parca)
    return parcalar_son


# ############################################### ###########################
# ############################################### Noktalardaki, açıyı ve açıortay vektörünü bul
def angle_3p(p_first, p_angle, p_last, radian=True):
    """
    3 noktanın ortasında oluşan açıyı döndürür
    """
    v1 = p_first - p_angle
    v2 = p_last - p_angle

    # iki doğru da aynı yöndeyse açı 180 derecedir. TODO Burayı düzelt, açı 0 derece de olabilir
    if (v1 - v2).length < .0001 or (v1 + v2).length < .0001:
        angle = math.radians(180)
    else:
        angle = v1.angle(v2)

        # İç / Dış açı konusunu bu kısımda çözüyoruz
        # Sağa or Sola dönme durumuna göre, iç açıyı buluyor
        if v1.cross(v2).z > 0:
            angle = math.radians(360) - angle

    return angle if radian else math.degrees(angle)


def calc_verts_angles(verts, verts_calc, resolution):
    """Köşelerin açılarını bulur. Aynı sırayla listeye kaydeder."""
    if len(verts) < 3:
        return []

    # Son noktanın indexi
    last_vert = len(verts) - 1

    angles = []

    # Her noktanın açısı bulunur
    for i in range(len(verts)):
        p1 = verts[i]

        a1 = angle_3p(verts_calc[i - 1], p1, verts_calc[i + 1 if i != last_vert else 0])
        a2 = angle_3p(verts[i - 1], p1, verts[i + 1 if i != last_vert else 0])

        angle = min(a1, a2)

        angles.append(angle)
        print("angle", math.degrees(angle))

    return angles


def calc_verts_bisector(verts, verts_calc, resolution):
    """Noktadaki açıortay. Noktada birleşen 2 kenarın açıortay birim vektörünü verir.

    :param verts: VectorList:
    :return: VectorList -> Açıortay birim vektörler"""
    if len(verts) < 2:
        return []

    # Son noktanın indexi
    last_vert = len(verts) - 1

    bisectors = []

    # Offset oluşturulur
    for i in range(len(verts)):
        # Önceki, Şimdiki, Sonraki nokta

        p1 = verts[i]

        if i % 3 == 1:
            p0 = verts_calc[i - 1]
            p2 = verts_calc[i + 1 if i != last_vert else 0]
        else:
            p0 = verts[i - 1]
            p2 = verts[i + 1 if i != last_vert else 0]

        # if i % 3 == 1:
        #     p0 = mathutils.geometry.interpolate_bezier(verts[i - 3], verts[i - 2], p0, p1, resolution)[-2]
        #     print("P2 önce", p2)
        #     if i + 3 < last_vert:
        #         p2 = mathutils.geometry.interpolate_bezier(p1, p2, verts[i + 2], verts[i + 3], resolution)[1]
        #     else:
        #         p2 = mathutils.geometry.interpolate_bezier(p1, p2, verts[0], verts[1], resolution)[1]
        #     print("P2 sonra", p2)

        # Şimdiki noktanın açıortayı bulunur. (p1'deki açıortay -> Vector1 ile Vector2 arasında)
        v1 = (p0 - p1).normalized()
        v2 = (p2 - p1).normalized()

        if (v1 - v2).length < .0001 or (v1 + v2).length < .0001:
            ort = v1.orthogonal()
            ort.z = (v1.z + v2.z) / 2

            # Bu üçünün yönü ile Genelin yönü çarpıştırılır. Z'si büyükse, dikme negatif yapılır
            if mathutils.geometry.normal([v1, ort, v2]).z * mathutils.geometry.normal(verts).z > 0:
                ort *= -1
            bisectors.append(ort.normalized())
        else:
            bisectors.append((v1+v2).normalized())

        print("bisectors", bisectors[-1])

    return bisectors


obj = bpy.context.active_object

pointis = obj.data.splines[0].bezier_points[:]

full_points = []
for p in pointis:
    full_points.extend((p.handle_left, p.co, p.handle_right))


parcalar = offset(pointis, orientation=-1)
# parcalar = offset(full_points, orientation=-1)

new_bezier_curve(parcalar, True)
