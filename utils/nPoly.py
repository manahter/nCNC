import math
import bpy
from mathutils import Vector
from mathutils.geometry import intersect_line_line_2d, intersect_point_line, intersect_line_line


def calc_verts_angles(verts):
    """Köşelerin açılarını bulur. Aynı sırayla listeye kaydeder."""
    # TODO Warning !!! Deneysel

    if len(verts) < 3:
        return []

    # Son noktanın indexi
    last_vert = len(verts) - 1

    angles = []

    # Her noktanın açısı bulunur
    for i in range(len(verts)):
        # Önceki, Şimdiki, Sonraki nokta
        p0 = verts[i - 1]
        p1 = verts[i]
        p2 = verts[i + 1 if i != last_vert else 0]

        # Şimdiki noktanın açısı bulunur. (p1'in açısı -> Vector1 ile Vector2 arasında)
        v1 = p0 - p1
        v2 = p2 - p1
        angle = v1.angle(v2)
        # TODO Açıları ya hepsi iç ya hepsi dış olarak buluyoruz ama hepsi iç mi dış mı onu belirleyemiyoruz.
        # Sağa or Sola dönme durumuna göre, iç açıyı buluyor
        if v1.cross(v2).z > 0:
            angle = math.radians(360) - angle

        angles.append(angle)
        print("angle", math.degrees(angle))

    return angles


def calc_verts_bisector(verts):
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
        p0 = verts[i - 1]
        p1 = verts[i]
        p2 = verts[i + 1 if i != last_vert else 0]

        # TODO p2 noktasını bulurken, kesişen noktalarda, diğer aynı noktayı bulup, komşu noktası alınmalı.

        # for j, p2_ in enumerate(verts):
        #     if i == j:
        #         continue

        #     if (p2_ - p1).length < .0001:
        #         if j > i:
        #             # p2 = verts[j - 1]
        #             p2 = verts[j + 1] if j < last_vert else verts[0]
        #         else:
        #             p2 = verts[j - 1]
        #             # p2 = verts[j + 1] if j < last_vert else verts[0]
        #         break

        # Şimdiki noktanın açısı bulunur. (p1'in açısı -> Vector1 ile Vector2 arasında)
        v1 = (p0 - p1).normalized()
        v2 = (p2 - p1).normalized()

        # print(v1, v2, (v1+v2).normalized())

        bisectors.append((v1+v2).normalized())
        # ort = Vector((*(p[0].xy - p[1].xy).orthogonal().normalized() * distance, 0))
        #
        # print(ort)
    return bisectors


def is_close_distance_to_points(verts_main, verts_target, distance):
    """Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
    verts_target'daki noktalar sırayla ele alınıp, verts_main'deki noktalara istenen distance'dan yakın mı kontrol
    edilir.

    :param verts_main: VectorList: Ana Poly'nin noktaları
    :param verts_target: VectorList: İncelenen Poly'nin noktaları
    :param distance: float: İncelenecek mesafe, uzaklık

    return bool:
        True -> Evet yakın nokta/lar var.
        False-> Hayır hiçbir nokta yakın değil.
    """
    # Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
    for t in verts_target:
        for m in range(len(verts_main)):
            if not m:
                continue
            p0 = verts_main[m - 1]
            p1 = verts_main[m]
            c, ratio = intersect_point_line(t, p0, p1)
            mes = (c - t).length
            if 1 >= ratio >= 0 and (mes + .01 < distance):
                return True

    return False


def is_2_poly_intersect(verts1, verts2, in_2d=True):
    """İki poly çizgileri arasında kesişen çizgi varsa, kesişen kısımlarından parçalara ayır

    :param verts1: VectorList: 1. Poly'nin noktaları
    :param verts2: VectorList: 2. Poly'nin noktaları
    :param in_2d: bool: Kesişim 2D olarak mı incelensin?

    return bool:
        False-> Kesişmez
    """

    for t in range(len(verts2)):
        t0 = verts2[t - 1]
        t1 = verts2[t]
        for m in range(len(verts1)):
            m0 = verts1[m - 1]
            m1 = verts1[m]

            # print(m0, m1, t0, t1)

            if in_2d:
                if intersect_line_line_2d(t0, t1, m0, m1):
                    return True
            else:
                # TODO Henüz kodlanmadı
                intersect_line_line(t0, t1, m0, m1)
    return False


def split_parts_from_intersect_in_self(verts_target, tersli_duzlu=False):
    """Kesişen çizgi varsa, kesişen kısımlarından parça oluştur ve oluşan parçaları döndür.
    Ana parça verts_target içinde kalır.

    :param verts_target: VectorList: İncelenen Poly'nin noktaları
    :param tersli_duzlu: bool: True ise-> 0. listeyi ters çvir, 1.liste duz, 2. ters....

    return [ [VectorList],... ]:
        Parçalar VectorList'ler şeklinde döndürülür
    """
    # Şimdi oluşan parçalar
    parcalar = []

    # Şimdi eklenen nokta
    v = verts_target[-1]

    # Parçadaki tüm noktalar tersten sırayla alınır.
    for n in range(len(verts_target) - 3, 0, -1):
        if not n:
            continue

        # Eksi 1. nokta
        e1 = verts_target[-2]

        # Sıradaki iki nokta
        v0 = verts_target[n - 1]
        v1 = verts_target[n]

        # Son eklenen iki noktanın oluşturduğu çizgi ile, Sıradaki iki noktanın oluşturduğu çizgi kesişiyor mu?
        o = intersect_line_line_2d(e1, v, v0, v1)

        # Çizgiler ucları dışında biryerden kesişiyorsa
        if o and o != e1.xy and o != v.xy and o != v0.xy and o != v1.xy:
            # Kesişen noktalar arasında kalan noktalardan yeni bir parça oluştur
            parca = [t.copy() for t in verts_target[n - 1:]]
            parca[0].xy = parca[-1].xy = o

            # Önceki noktanın konumunu kesişim noktasına güncelle
            e1.xy = o

            # Yeni parçayı ilkparça'dan çıkart
            for t in verts_target[n:-2]:
                verts_target.remove(t)

            # Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
            # Yakın değilse bu parçayı ekle. Evet parça uygundur ve eklenebilir
            if tersli_duzlu:
                if not len(parcalar) % 2:
                    parca.reverse()
            parcalar.append(parca)

    return parcalar


def disolve_doubles(verts):
    """Peş Peşe 2 tane aynı nokta varsa bir tanesi silinir"""
    # Verts sayısı 0 ise bitir
    if not len(verts):
        return

    # Tersten alıyoruz ki,
    for i in range(len(verts) - 1, -1, -1):
        if verts[i-1] == verts[i]:
            verts.pop(i)


def offset(verts, distance=.2, orientation=-1):
    """Poly'ye offset uygular ve yeni Poly noktalarını döndürür.

    :param verts: VectorList:    Poly'nin pointleri
    :param distance: float: Mesafe
    :param orientation: int: -1 or +1 -> iç veya dış offset

    return VectorList: Poly'nin offset almnış hali
    """

    # Poly çizgileri kesişmez hale getirilir
    non_intersecting_poly(verts)

    disolve_doubles(verts)

    angles = calc_verts_angles(verts)

    bisectors = calc_verts_bisector(verts)

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

        # TODO!!! Geri çekmede bazı yerlerde sorun yaşıyoruz, bunu çözelim
        # ##########################################################
        # Bir Önceki noktaya bak, içbükey mi, Dar açılıysa, geri çek
        # ##########################################################
        # if len(ilkparca) > 4:
        if len(ilkparca) > 4 and orientation > 0:   # TODO -> Buraya geçici olarak orientation ekledik
            # Eklediğimiz son 2 noktayı alıyoruz
            e1 = ilkparca[-1]
            e2 = ilkparca[-2]
            # Eklediğimiz sondan ikinci noktayı alıyoruz.
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

                        # if ang > math.radians(180):
                        #     v2 = p0 - p1
                        #     ang = v1.angle(v2)

                        # Son noktadan şimdiki noktaya olan kenar ile objedeki yakın kenarın kesiştiği nokta
                        ya = intersect_line_line(e1, v, p0, p1)[0]

                        # Distance nokta, oluşturğumuz kenarın neresine geliyor (oran)
                        ratio = abs(distance / math.sin(ang)) / (ya - v).length
                        ilkparca[-1] = ya.lerp(v, ratio)

        ilkparca.append(v)

        # ##########################################################
        # Kesişen çizgi varsa, kesişen kısımlarından parçalara ayır
        parts = split_parts_from_intersect_in_self(ilkparca)
        if parts:
            # Eğer parçaların herhangi birisi, distance'den daha yakınsa ekleme.
            for p in parts:
                if not is_close_distance_to_points(verts, p, distance):
                    parcalar.append(p)

    # İlkparçayı da kontrol edelim.
    # if not is_2_poly_intersect(verts, ilkparca) and not is_close_distance_to_points(verts, ilkparca, distance):
    #     # TODO diğer parçalarla kesişiyorsa onlarla birleştir
    #     parcalar.append(ilkparca)

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
                    k.remove(u)

        # 3 noktadan az varsa işlem yapılmaz
        # for n in range(len(verts)):
        #     if not n:
        #         continue

        #     p0 = verts[n - 1]
        #     p1 = verts[n]

        #     for k in parca:

        #         c, ratio = intersect_point_line(k, p0, p1)
        #         mes = (c - k).length
        #         if 1 >= ratio >= 0 and (mes + .01 < distance):  # and (angles[j] < math.radians(180)):
        #             print("sildik", k)
        #             parca.remove(k)
        #             break

        # Yeni parçadaki noktalardan herhangi birisi Objeye, distance'dan fazla yakın mı?
        # Yakın değilse bu parçayı ekle. Evet parça uygundur ve eklenebilir
        if len(parca) < 3 or is_close_distance_to_points(verts, parca, distance) or is_2_poly_intersect(verts, parca):
            continue

        parcalar_son.append(parca)
        # Demek ki bu parça uygun öyleyse Eklenir.
        # obj.data.splines.new("POLY")
        # obj.data.splines[-1].use_cyclic_u = True
        # yenler = obj.data.splines[-1].points
        # yenler[-1].co.xyz = parca[0]

        # for v in parca[1:]:
        #     if v.xyz != yenler[-1].co.xyz:
        #         yenler.add(1)
        #         yenler[-1].co.xyz = v

        # print(len(yenler), "as")
    # print(*parcalar, sep="\n"*5)
    return parcalar_son


# ############################################### ###########################
# ############################################### Poly'yi kesişmez hale getir
def _kesisim_noktalarini_bul(vertices, z=0):
    """Poly'de kesişim noktalarını bul ve biriktir

    :param vertices: VectorList:    Poly'nin pointleri
    :param z: int:    Kesişim noktasında Z'de hangi seviye baz alınsın. # TODO Z şuan kullanım dışı
                   -1 -> Min Z
                    0 -> Orta Z
                    1 -> Max Z

    return [(index, Vector), ...]   -> Eklenen nokta ve indexi şeklinde tuple'lar döndürülür
    """
    kesisimler = []
    for i in range(len(vertices)):
        v0 = vertices[i - 1]
        v1 = vertices[i]
        vs = (v0, v1)
        kesisiy = []
        for j in range(len(vertices)):
            v2 = vertices[j - 1]
            v3 = vertices[j]

            if v2 in vs or v3 in vs:
                continue

            o = intersect_line_line_2d(v0, v1, v2, v3)
            if o:
                # TODO !!!
                #   Kesişim yerine eklenen noktanın Z'de yeri belli olsun.

                z0 = v0.lerp(v1, intersect_point_line(o, v0.xy, v1.xy)[1]).z
                z1 = v2.lerp(v3, intersect_point_line(o, v2.xy, v3.xy)[1]).z
                # if z > 0:
                #     z = max((z0, z1))
                # elif z < 0:
                #     z = min((z0, z1))
                # else:
                z = (z0 + z1) / 2

                o = Vector((*o, z))
                kesisiy.append((i, o))

        # v0-v1 aralığında yeni eklenen kesişim noktalarının sırasını düzenliyoruz.
        kesisiy.sort(key=lambda x: intersect_point_line(x[1], v0, v1)[1])
        kesisimler.extend(kesisiy)

    return kesisimler


def _kesisim_yerlerine_nokta_ekle(vertices):
    """Kesişim noktalarına yeni vertexler ekler.

    :param vertices: VectorList:    Poly'nin pointleri

    return vertices -> Aynı vertices listesini geri döndürür.
    """
    # Kesişim noktaları bulunur -> [(index, Vector), ...]
    kesisimler = _kesisim_noktalarini_bul(vertices)

    # Kesişim noktalarına yeni vertexleri ekle
    kaydi = 0
    for i, v in kesisimler:
        vertices.insert(i + kaydi, v)
        kaydi += 1

    return vertices


def _kesisimden_yon_degis(vertices):
    """Kesişim yerlerine nokta konmuş Poly'de çizgiler ilerlerken kesişim yerlerinden diğer yöne sapar. Böylece
    kenar çizgileri kesişmez olur.

    :param vertices: VectorList:    Poly'nin pointleri

    return vertices -> Aynı vertices listesini geri döndürür.
    """
    len_vert = len(vertices)

    for i in range(len_vert):
        v0 = vertices[i]
        for j in range(i + 1, len_vert):
            v1 = vertices[j]
            if (v0 - v1).length < .0001:
                bura = vertices[i + 1:j][::-1]
                for l in range(i + 1, j):
                    vertices[l] = bura[l - (i + 1)]
                break

    return vertices


def non_intersecting_poly(vertices):
    _kesisim_yerlerine_nokta_ekle(vertices)

    ##########################################
    # Kesişim noktalarından dönüşler yap. İlk verts'e geldiğinde bitir
    _kesisimden_yon_degis(vertices)


# ###############################################
# ###############################################
def new_poly_curve(polys):
    """Noktalardan yeni bir Poly oluşturulur"""
    # Curve Data oluştur
    curve = bpy.data.curves.new("npoly", "CURVE")

    for points in polys:
        # Poly spline oluştur
        curve.splines.new("POLY")

        # ilk ve son nokta eşitse, son noktayı sil
        if points[0] == points[-1]:
            points.pop(-1)

        # Kapalı yap
        curve.splines[-1].use_cyclic_u = True

        # Curve Pointleri al
        curpt = curve.splines[-1].points

        # Gelen point sayısı kadar Curve'da point oluşturulur
        curpt.add(len(points) - 1)

        # Gelen pointler Curve'ye eklenir
        for j, v in enumerate(points):
            if v.xyz != curpt[-1].co.xyz:
                curpt[j].co.xyz = v

    # Obje oluşturlup sahneye eklenir
    obje = bpy.data.objects.new("npoly", curve)
    obje.data.dimensions = '3D'
    bpy.context.scene.collection.objects.link(obje)


obj = bpy.context.active_object

vertices = [i.co.xyz for i in obj.data.splines[0].points]


# non_intersecting_poly(vertices)
# new_poly_curve([vertices])
# En az 3 nokta veya daha fazla nokta varsa burası hesaplanır.
if len(vertices) >= 3:
    parcalar = offset(vertices, distance=.2, orientation=1)

    new_poly_curve(parcalar)

