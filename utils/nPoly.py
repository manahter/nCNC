import math
import bpy
from mathutils import Vector
from mathutils.geometry import intersect_line_line_2d, intersect_point_line, intersect_line_line
import mathutils

# TODO Dönüş yoktalarına Round eklenebilir. Mesela bir dikdörgene dış offset uygulandığında, köşeleri round olacak
#   şekilde düzenlenebilir.


# ############################################### ###########################
# ############################################### Offset Uygula, Curve oluştur
def new_poly_curve(polys, add_screen=False, cyclic=True):
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

    for points in polys:
        if len(points) < 2:
            continue

        # Poly spline oluştur
        curve.splines.new("POLY")

        # ilk ve son nokta eşitse, son noktayı sil
        if points[0] == points[-1]:
            points.pop(-1)

        # Kapalı yap
        curve.splines[-1].use_cyclic_u = cyclic

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


def offset(verts, distance=.2, orientation=-1):
    """Poly'ye offset uygular ve yeni Poly noktalarını döndürür.

    :param verts: VectorList:    Poly'nin pointleri
    :param distance: float: Mesafe
    :param orientation: int: -1 or +1 -> iç veya dış offset

    return VectorList: Poly'nin offset almnış hali
    """
    # Poly çizgileri kesişmez hale getirilir
    non_intersecting_poly(verts)

    # İç mi dış mı olduğu düzenlenir.
    orientation *= -1 if mathutils.geometry.normal(verts).z > 0 else 1

    # Peş peşe aynı olan noktaları temizle
    disolve_doubles(verts)

    # Her noktadaki açı bulunur
    angles = calc_verts_angles(verts)
    angles.append(angles[0])

    # Her noktadaki açıortay bulunur
    bisectors = calc_verts_bisector(verts)
    bisectors.append(bisectors[0])

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

        # TODO!!! Geri çekmede bazı yerlerde sorun yaşıyoruz, bunu çözelim
        # ##########################################################
        # Bir Önceki noktaya bak, içbükey mi, Dar açılıysa, geri çek
        # ##########################################################
        # if len(ilkparca) > 4:
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

        ilkparca.append(v)

        # ##########################################################
        # Kesişen çizgi varsa, kesişen kısımlarından parçalara ayır
        parts = split_parts_from_intersect_in_self(ilkparca)
        if parts:

            # Eğer parçaların herhangi birisi, distance'den daha yakınsa ekleme.
            for p in parts:
                if not is_close_distance_to_points(verts, p, distance):
                    parcalar.append(p)

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
        if len(parca) < 3 or is_close_distance_to_points(verts, parca, distance) or is_2_poly_intersect(verts, parca):
            continue

        parcalar_son.append(parca)
    return parcalar_son


# ############################################### ###########################
# ############################################### Noktalardaki, açıyı ve açıortay vektörünü bul
def calc_verts_angles(verts):
    """Köşelerin açılarını bulur. Aynı sırayla listeye kaydeder."""
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

        # İç / Dış açı konusunu bu kısımda çözüyoruz
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

        # Şimdiki noktanın açısı bulunur. (p1'in açısı -> Vector1 ile Vector2 arasında)
        v1 = (p0 - p1).normalized()
        v2 = (p2 - p1).normalized()

        bisectors.append((v1+v2).normalized())

    return bisectors


# ############################################### ###########################
# ############################################### Noktalar çizgilere yakın mı veya çizgiler kesişiyor mu
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


def is_2_poly_intersect(verts1, verts2, in_2d=True, verts1_cyclic=True, verts2_cyclic=True):
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
        if not verts1_cyclic and not t:
            continue
        t0 = verts2[t - 1]
        t1 = verts2[t]
        for m in range(len(verts1)):
            if not verts2_cyclic and not m:
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


# ############################################### ###########################
# ############################################### Kendi içinde kesişen yerlerden ayırarak yeni parça oluştur.
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
        if v != v0 and o and o != e1.xy and o != v.xy and o != v0.xy and o != v1.xy:
            # Kesişen noktalar arasında kalan noktalardan yeni bir parça oluştur
            parca = [t.copy() for t in verts_target[n - 1:]]

            # Kesişim noktasının Z değerini de bul. Yan, 3D noktayı bul
            o = v0.lerp(v1, intersect_point_line(o, v0.xy, v1.xy)[1])

            parca[0] = parca[-1] = o

            # Önceki noktanın konumunu kesişim noktasına güncelle
            e1.xyz = o

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

    # Tersten alıyoruz ki, silinince listede kayma olmasın
    for i in range(len(verts) - 1, -1, -1):
        if verts[i-1] == verts[i]:
            verts.pop(i)


# ############################################### ###########################
# ############################################### Poly'yi kesişmez hale getir
def non_intersecting_poly(vertices):
    _kesisim_yerlerine_nokta_ekle(vertices)

    ##########################################
    # Kesişim noktalarından dönüşler yap. İlk verts'e geldiğinde bitir
    _kesisimden_yon_degis(vertices)


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


# ############################################### ###########################
# ############################################### Poly içini Zigzagla doldur
def zigzag(verts, angle=45, distance=1.0):
    """
    Poly vertslerinin içte kalan kısmına zigzag oluşturur.

    :param verts: VectorList: Dilimlenecek Poly'nin noktaları
    :param angle: int: Dilimleyici hangi açıda olsun
    :param distance: float: Dilimler arası mesafe ne kadar olsun

    return [(p0, p1, p2, p3), (p0, p1), ...]    -> Parçalar
    """
    # Zigzag çizgilerini hesapla
    zigzag_lines = _zigzag_vektorlerini_olustur(verts, angle, distance)

    # Zigzag çizgilerinin Ana Poly'yi kestiği noktalara yeni nokta ekle
    kesimli_hali = _zigzagda_kesisimlere_nokta_ekle(verts, zigzag_lines)

    # Ana Poly'ye minik bir offset uygula ve zigzag çigilerini uygun şekilde birleştir.
    # Offsetin sebebi, zigzag çizgilerine çok yakın olanları kesiyor saymasın diyedir..
    return _zigzag_cizgilerini_birlestir(offset(verts, .0001, 1)[0], kesimli_hali)


def _zigzag_vektorlerini_olustur(verts, angle=45, distance=1.0):
    """
    Zigzag için çizgilerini oluşturur.

    :param verts: VectorList: Dilimlenecek Poly'nin noktaları
    :param angle: int: Dilimleyici hangi açıda olsun
    :param distance: float: Dilimler arası mesafe ne kadar olsun

    return [(p0, p1), (p0, p1), ...]    -> Lines
    """
    min_x = min(verts, key=lambda v: v.x).x - .1
    min_y = min(verts, key=lambda v: v.y).y - .1
    max_x = max(verts, key=lambda v: v.x).x + .1
    max_y = max(verts, key=lambda v: v.y).y + .1

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


def _zigzagda_kesisimlere_nokta_ekle(verts_main, zigzag_lines):
    """
    Zigzag için çizgilerinin kesişim yerlerine nokta ekler

    :param verts_main: VectorList: Ana Poly'nin noktaları
    :param zigzag_lines: [(p0, p1), (p0, p1), ...]: LineList

    return [ [p0, p1, p2, p3], [p0, p1], ]
    """
    kesimler = []
    for s0, s1 in zigzag_lines:
        kesisiy = []
        for i in range(len(verts_main)):
            v0 = verts_main[i - 1]
            v1 = verts_main[i]

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


def _zigzag_cizgilerini_birlestir(verts_main, zigzag_lines):
    """Gruplanmış çizgileri uygun olan uçlarından birleştir.

    :param verts_main: VectorList: Ana Poly'nin noktaları
    :param zigzag_lines: [(p0, p1), (p0, p1), ...]: LineList


    """

    parcalar = []
    parca = []
    p_ind = 0

    while any(zigzag_lines):
        line_points = zigzag_lines[p_ind]

        # İçierikte nokta yoksa, son parçayı paketle.
        if len(line_points) < 2:
            if parca:
                parcalar.append(parca)
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

                if (v - v_son).length < l_min_dist and \
                        not is_2_poly_intersect([v, v_son], verts_main, verts1_cyclic=False):
                    l_min_dist = (v - v_son).length
                    v_cur = v

            # Şimdi bulduğumuz noktaya bağlı nokta bulunur.
            v_cur_ind = line_points.index(v_cur)
            v_aft = line_points[v_cur_ind + (1, -1)[v_cur_ind % 2]]

            ok = True

            # Yeni çizginin, Objedeki çizgilerle kesişip kesişmediğine bak
            for i in range(len(verts_main)):

                if intersect_line_line_2d(v_son, v_cur, verts_main[i-1], verts_main[i]):
                    ok = False
                    break

            # Kesişme varsa, son parçayı paketle ve yeni parça oluştur
            if not ok:
                parcalar.append(parca)
                parca = []

            parca.extend((v_cur, v_aft))

            line_points.remove(v_cur)
            line_points.remove(v_aft)

        p_ind += 1
        if len(zigzag_lines) <= p_ind:
            zigzag_lines.reverse()
            p_ind = 0

    if parca:
        parcalar.append(parca)

    return parcalar


"""
obj = bpy.context.active_object

vertices = [i.co.xyz for i in obj.data.splines[0].points]


# non_intersecting_poly(vertices)
# new_poly_curve([vertices], add_screen=True)
# En az 3 nokta veya daha fazla nokta varsa burası hesaplanır.
if len(vertices) >= 3:
    parcalar = offset(vertices, distance=.2, orientation=-1)

    new_poly_curve(parcalar, add_screen=True)
"""
