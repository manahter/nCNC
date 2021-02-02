import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.geometry import intersect_line_line_2d, intersect_point_line, intersect_line_line, interpolate_bezier
import mathutils


# TODO
#   Bazı Köşeler'e Round eklenebilir


# ############################################### ###########################
# ############################################### Offset Uygula, Curve oluştur
def new_poly_curve(polys, add_screen=False, cyclic=True, cyclics=[]):
    """Noktalardan yeni bir Poly oluşturulur.

    :param polys: [ [poly_points], [...], ... ] -> Poly pointlerin listesi
    :param add_screen: bool:
        True -> Ekrana ekle ve objeyi döndür
        False-> Ekrana ekleme, curve'ü döndür
    :param cyclic: bool: Kapalı mı?

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
        curve.splines[-1].use_cyclic_u = cyclics[j] if len(cyclics) else cyclic

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


def offset_splines(splines, distance=.2, orientation=-1, add_screen=True):
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
        return new_poly_curve(parcalar, add_screen=True, cyclics=cyclics)

    return parcalar


def offset_spline(spline, distance=.2, orientation=-1, add_screen=True):
    """Spline'a offset uygular.

    :param spline: obj.data.splines[0]: gibi
    :param distance: float: Mesafe
    :param orientation: int: -1 or +1 -> iç veya dış offset
    :param add_screen: bool:
        True -> Ekrana ekle ve objeyi döndür
        False-> Ekrana ekleme, polyleri döndür

    return [VectorList, VectorList...] or CurveObje: Spline'ın offset almış hali
    """
    vertices = spline_to_poly(spline)

    cyclic = spline.use_cyclic_u or is_cyclic(vertices)
    parcalar = offset_2d(vertices, distance, orientation, cyclic=cyclic)

    # parcalar = clearance_offset(parcalar, distance)

    if add_screen:
        return new_poly_curve(parcalar, add_screen=True, cyclic=cyclic)

    return parcalar


def offset1_rev1(verts, distance=.2, orientation=-1):
    """Poly'ye offset uygular ve yeni Poly noktalarını döndürür.

    :param verts: VectorList:    Poly'nin pointleri
    :param distance: float: Mesafe
    :param orientation: int: -1 or +1 -> iç veya dış offset

    return [VectorList, VectorList...]: Poly'nin offset almış hali
    """
    # Peş peşe aynı olan noktaları temizle
    disolve_doubles(verts)

    # Aynı Doğru üzerindeki noktaları temizle
    clear_linear_points(verts)

    # Sıfır derece açı oluşturan noktaları temizle
    clear_zero_angle(verts)

    # TODO Distance'nin sığmadığı açıları temizle.

    # Poly çizgileri kesişmez hale getirilir
    non_intersecting_poly(verts)

    if len(verts) < 3:
        return []

    # İç mi dış mı olduğu düzenlenir.
    ori = orientation * -1 if mathutils.geometry.normal(verts).z > 0 else orientation

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
    son_index = len(bisectors) - 1

    # Tüm açıortay vektörlerini sırayla al
    for j, i in enumerate(bisectors):
        # Elimizde bir dik üçgen olduğunu düşünelim
        # açı         -> angles[j]   -> noktadaki açı
        # Komşu kenar -> distance
        # Hipotenüs   -> Açıortay vektörünün uzunluğunu kullanarak bulacağız
        # Sonra açıortay doğrultusunda, hipotenüs kadar uzat

        # Açı 0 veya 180 dereceyse atlanır.
        if not angles[j] or angles[j] == math.radians(180):
            continue

        # açı 180'den büyükse, karşı açıyı kullan (360'dan çıkart)
        if angles[j] > math.radians(180):
            angle = math.radians(360) - angles[j]
            ti = -(distance / math.sin(angle / 2))
        else:
            ti = (distance / math.sin(angles[j] / 2))

        v = verts[j] + i * ti * ori

        if not len(ilkparca):
            ilkparca.append(v)
            continue

        # Şimdiki eklenecek nokta, son eklenen noktayla aynıysa işlemi atla
        if is_same_point(v, ilkparca[-1]):
            continue

        # Eğer şimdi eklenecek çizgi, ana Poly ile kesişiyorsa
        # if j > 1 and is_2_poly_intersect(verts, [ilkparca[-1], v], verts2_cyclic=False):

        #     # TODO Kesişmeden önceki mümkün yere yeni nokta ekle
        #     # Son iki nokta ile oluşan çizgi ana Poly ile kesişiyor mu?
        #     kes = intersect_line_poly(ilkparca[-1], v, verts)

        #     # Kesişim varsa, Kesişmeden önceki uygun yere nokta ekle. TODO sonraki uygun yere de nokta ekleme nasıl olur
        #     if kes:
        #         print("Var\n"*5)
        #         ara_p = shorten_line_if_close_to_poly(ilkparca[-1], kes[0][2], kes[0][:-1], check_intersect=True)[1]
        #         if not is_same_point(ara_p, ilkparca[-1]):
        #             ilkparca.append(ara_p)
        #         # ilkparca.append(v)
        #         # continue

        # Yeni çizgi kendi içinde kesişiyorsa noktayı ekle ve devam et.
        if j != son_index and is_2_poly_intersect(ilkparca[:-1], [ilkparca[-1], v], verts2_cyclic=False):
            ilkparca.append(v)

            """"""
            # ##########################################################
            # Kesişen çizgi varsa, kesişen kısımlarından parçalara ayır
            parts = split_parts_from_intersect_in_self(ilkparca)
            if parts:

                # Eğer parçaların herhangi birisi, distance'den daha yakınsa ekleme.
                for p in parts:
                    if not is_close_distance_to_points(verts, p, distance):
                        parcalar.append(p)
            continue

        # ##########################################################
        # Noktamız, Çizgilere yakınsa geri çek
        # ##########################################################

        # Eğer iç Offset ise
        if orientation < 0:

            # İlk çizgi oluştuysa, 0. noktanın kenarlara yakınlığını ve kesişme durumunu kontrol et
            if len(ilkparca) == 1:
                print("ilk parça gir ", ilkparca[-1])
                v, ilkparca[-1] = shorten_line_if_close_to_poly(v, ilkparca[-1], verts, check_intersect=True)
                print("ilk parça çık ", ilkparca[-1])

            e1 = ilkparca[-1]
            # Son çizgiyi oluştuyorsak, Sonuncu noktanın kenarlara yakınlığını ve kesişme durumunu kontrol et
            if j == son_index:
                ilkparca[-1], v = shorten_line_if_close_to_poly(e1, v, verts, check_intersect=True)

            # Ara noktaları oluşturuyorsak, noktaların kenarlara sadece yakınlığını kontrol et
            else:
                ilkparca[-1], v = shorten_line_if_close_to_poly(e1, v, verts, check_intersect=False)

        # Şimdiki eklenecek nokta, son eklenen noktayla aynıysa işlemi atla
        if is_same_point(v, ilkparca[-1]):
            print("Aynı atla", v)
            continue

        # if len(ilkparca) > 4:
        # if len(ilkparca) > 1:
        if False:
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

            # Eğer offset iç ise, iç açıyı bulmak için dış açıyı 360'dan çıkarıyoruz
            if ori < 0:
                ang = math.radians(360) - ang

            # Eğer son noktadaki açı 90 dereceden küçükse, geri çekmek gerekebilir. Şimdi onu inceliyoruz.
            if ang < math.radians(90):

                # Noktadan çizgiye mesafe kontrolü
                # Objedeki çizgileri sırayla geziyoruz
                for n in range(len(verts)):
                    if not n:
                        continue

                    # Objedeki sıradaki 2 nokta alınır
                    p0 = verts[n - 1]
                    p1 = verts[n]

                    # Eklediğimiz son noktanın obje çizgisine mesafesi bulunur
                    c, ratio = intersect_point_line(e1, p0, p1)

                    # Mesafe distance'den küçükse, Son nokta geri çekilir.
                    mes = (c - e1).length
                    if (1 >= ratio >= 0) and (mes + .01 < distance):  # and (angles[j] < math.radians(180)):

                        # İç ise, Başlangıç Noktası e2 (eksi 2. nokta)'yı al.
                        # Dış ise, şimdi ekleyeceğimiz noktayı al
                        fs = v if ori > 0 else e2

                        # Son noktadan şimdiki noktaya olan vektör (Kenar 1)
                        v1 = fs - e1
                        # Objedeki yakın olduğumuz kenarın vektörü (Kenar 2)
                        v2 = p0 - p1

                        # Bu iki kenar arasındaki açı
                        ang = v1.angle(v2)

                        # Son noktadan şimdiki noktaya olan kenar ile objedeki yakın kenarın kesiştiği nokta
                        ya = intersect_line_line(e1, fs, p0, p1)[0]

                        # Distance nokta, oluşturğumuz kenarın neresine geliyor (oran)
                        ratio = abs(distance / math.sin(ang)) / (ya - fs).length
                        ilkparca[-1] = ya.lerp(fs, ratio)

        ilkparca.append(v)

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
        if len(
                parca) < 3:  # or is_close_distance_to_points(verts, parca, distance) or is_2_poly_intersect(verts, parca):
            continue

        parcalar_son.append(parca)
    return parcalar_son


def offset1(verts, distance=.2, orientation=-1, cyclic=True):
    """Poly'ye offset uygular ve yeni Poly noktalarını döndürür.

    :param verts: VectorList:    Poly'nin pointleri
    :param distance: float: Mesafe
    :param orientation: int: -1 or +1 -> iç veya dış offset

    return [VectorList, VectorList...]: Poly'nin offset almış hali
    """
    # Peş peşe aynı olan noktaları temizle
    disolve_doubles(verts)

    # Aynı Doğru üzerindeki noktaları temizle
    clear_linear_points(verts, cyclic)

    # Sıfır derece açı oluşturan noktaları temizle
    clear_zero_angle(verts, cyclic)

    # TODO Distance'nin sığmadığı açıları temizle.

    # Poly çizgileri kesişmez hale getirilir
    non_intersecting_poly(verts, cyclic)

    if len(verts) < 3:
        return []

    # İç mi dış mı olduğu düzenlenir.
    ori = orientation * -1 if mathutils.geometry.normal(verts).z > 0 else orientation

    # Her noktadaki açı bulunur
    angles = calc_verts_angles(verts, cyclic)

    # Her noktadaki açıortay bulunur
    bisectors = calc_verts_bisector(verts, cyclic)

    if cyclic:
        angles.append(angles[0])
        bisectors.append(bisectors[0])

        # Üstten beri listenin sonuna ilk noktayı tekrar ekliyoruz çünkü altlarda biryerde çıkan sorunu engelliyoruz böylece
        verts.append(verts[0])

    ilkparca = []
    parcalar = [ilkparca]
    son_index = len(bisectors) - 1

    # Tüm açıortay vektörlerini sırayla al
    for j, i in enumerate(bisectors):
        # Elimizde bir dik üçgen olduğunu düşünelim
        # açı         -> angles[j]   -> noktadaki açı
        # Komşu kenar -> distance
        # Hipotenüs   -> Açıortay vektörünün uzunluğunu kullanarak bulacağız
        # Sonra açıortay doğrultusunda, hipotenüs kadar uzat

        # Açı 0 veya 180 dereceyse atlanır.
        if not angles[j] or angles[j] == math.radians(180):
            continue

        # açı 180'den büyükse, karşı açıyı kullan (360'dan çıkart)
        if angles[j] >= math.radians(180):
            angle = math.radians(360) - angles[j]
            ti = -(distance / math.sin(angle / 2))
        else:
            angle = angles[j]
            ti = (distance / math.sin(angle / 2))
        vect = i * ti * ori
        v = verts[j] + vect

        if not len(ilkparca):
            ilkparca.append(v)
            continue

        # if angle < math.radians(60): # and (verts[j] - verts[j-1]).length < vect.length:
        #     print("Girrr")
        #     continue
        ilkparca.append(v)
        continue
        # Şimdiki eklenecek nokta, son eklenen noktayla aynıysa işlemi atla
        # if is_same_point(v, ilkparca[-1]):
        #     continue

        # Eğer şimdi eklenecek çizgi, ana Poly ile kesişiyorsa
        # if j > 1 and is_2_poly_intersect(verts, [ilkparca[-1], v], verts2_cyclic=False):

        #     # TODO Kesişmeden önceki mümkün yere yeni nokta ekle
        #     # Son iki nokta ile oluşan çizgi ana Poly ile kesişiyor mu?
        #     kes = intersect_line_poly(ilkparca[-1], v, verts)

        #     # Kesişim varsa, Kesişmeden önceki uygun yere nokta ekle. TODO sonraki uygun yere de nokta ekleme nasıl olur
        #     if kes:
        #         print("Var\n"*5)
        #         ara_p = shorten_line_if_close_to_poly(ilkparca[-1], kes[0][2], kes[0][:-1], check_intersect=True)[1]
        #         if not is_same_point(ara_p, ilkparca[-1]):
        #             ilkparca.append(ara_p)
        #         # ilkparca.append(v)
        #         # continue

        # ##########################################################
        # Noktamız, Çizgilere yakınsa geri çek
        # ##########################################################
        # Eğer iç Offset ise
        if False:
            # if orientation < 0:

            # İlk çizgi oluştuysa, 0. noktanın kenarlara yakınlığını ve kesişme durumunu kontrol et
            if len(ilkparca) == 1:
                print("ilk parça gir ", ilkparca[-1])
                v, ilkparca[-1] = shorten_line_if_close_to_poly(v, ilkparca[-1], verts, check_intersect=True)
                print("ilk parça çık ", ilkparca[-1])

            e1 = ilkparca[-1]
            # Son çizgiyi oluştuyorsak, Sonuncu noktanın kenarlara yakınlığını ve kesişme durumunu kontrol et
            if j == son_index:
                ilkparca[-1], v = shorten_line_if_close_to_poly(e1, v, verts, check_intersect=True)

            # Ara noktaları oluşturuyorsak, noktaların kenarlara sadece yakınlığını kontrol et
            else:
                ilkparca[-1], v = shorten_line_if_close_to_poly(e1, v, verts, check_intersect=False)

        # Şimdiki eklenecek nokta, son eklenen noktayla aynıysa işlemi atla
        if is_same_point(v, ilkparca[-1]):
            continue

        # if len(ilkparca) > 4:
        # if len(ilkparca) > 1:
        if False:
            # Eklediğimiz son 2 noktayı alıyoruz
            e1 = ilkparca[-1]
            e2 = ilkparca[-2]

            # Eklediğimiz sondan ikinci noktayı, ama e1'den farklıysa alıyoruz. Farklı değilse, daha önceki nokta alınır
            for t in ilkparca[::-1]:
                if t != e1:
                    e2 = t
                    break

            # Şimdi ekleyeceğimiz nokta ile son iki noktayı alıp, son noktada oluşan açıyı buluyoruz
            ang = calc_verts_angles([e2, e1, v], cyclic)[1]

            # Eğer offset iç ise, iç açıyı bulmak için dış açıyı 360'dan çıkarıyoruz
            if ori < 0:
                ang = math.radians(360) - ang

            # Eğer son noktadaki açı 90 dereceden küçükse, geri çekmek gerekebilir. Şimdi onu inceliyoruz.
            if ang < math.radians(90):

                # Noktadan çizgiye mesafe kontrolü
                # Objedeki çizgileri sırayla geziyoruz
                for n in range(len(verts)):
                    if not n:
                        continue

                    # Objedeki sıradaki 2 nokta alınır
                    p0 = verts[n - 1]
                    p1 = verts[n]

                    # Eklediğimiz son noktanın obje çizgisine mesafesi bulunur
                    c, ratio = intersect_point_line(e1, p0, p1)

                    # Mesafe distance'den küçükse, Son nokta geri çekilir.
                    mes = (c - e1).length
                    if (1 >= ratio >= 0) and (mes + .01 < distance):  # and (angles[j] < math.radians(180)):

                        # İç ise, Başlangıç Noktası e2 (eksi 2. nokta)'yı al.
                        # Dış ise, şimdi ekleyeceğimiz noktayı al
                        fs = v if ori > 0 else e2

                        # Son noktadan şimdiki noktaya olan vektör (Kenar 1)
                        v1 = fs - e1
                        # Objedeki yakın olduğumuz kenarın vektörü (Kenar 2)
                        v2 = p0 - p1

                        # Bu iki kenar arasındaki açı
                        ang = v1.angle(v2)

                        # Son noktadan şimdiki noktaya olan kenar ile objedeki yakın kenarın kesiştiği nokta
                        ya = intersect_line_line(e1, fs, p0, p1)[0]

                        # Distance nokta, oluşturğumuz kenarın neresine geliyor (oran)
                        ratio = abs(distance / math.sin(ang)) / (ya - fs).length
                        ilkparca[-1] = ya.lerp(fs, ratio)

        # ilkparca.append(v)

        # Yeni çizgi kendi içinde kesişiyorsa noktayı ekle ve devam et.
        # if j != son_index and is_2_poly_intersect(ilkparca[:-1], [ilkparca[-1], v], verts2_cyclic=False):
        #     ilkparca.append(v)

        """
        #     # ##########################################################
        #     # Kesişen çizgi varsa, kesişen kısımlarından parçalara ayır
        parts = split_parts_from_intersect_in_self(ilkparca)
        if parts:

            # Eğer parçaların herhangi birisi, distance'den daha yakınsa ekleme.
            for p in parts:
                if not is_close_distance_to_points(verts, p, distance):
                    parcalar.append(p)
        continue"""

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
        if len(
                parca) < 3:  # or is_close_distance_to_points(verts, parca, distance) or is_2_poly_intersect(verts, parca):
            continue

        parcalar_son.append(parca)
    return parcalar_son


def offset0(verts, distance=.2, orientation=-1):
    """Poly'ye offset uygular ve yeni Poly noktalarını döndürür.
    :param verts: VectorList:    Poly'nin pointleri
    :param distance: float: Mesafe
    :param orientation: int: -1 or +1 -> iç veya dış offset
    return [VectorList, VectorList...]: Poly'nin offset almış hali
    """
    # Peş peşe aynı olan noktaları temizle
    disolve_doubles(verts)

    # Aynı Doğru üzerindeki noktaları temizle
    clear_linear_points(verts)

    # Sıfır derece açı oluşturan noktaları temizle
    clear_zero_angle(verts)

    # Poly çizgileri kesişmez hale getirilir
    non_intersecting_poly(verts)

    if len(verts) < 3:
        return []

    # İç mi dış mı olduğu düzenlenir.
    orientation *= -1 if mathutils.geometry.normal(verts).z > 0 else 1

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
        if not angles[j]:
            # Açı 0 dereceyse atlanır.
            continue

        if angles[j] > math.radians(180):
            angle = math.radians(360) - angles[j]
            ti = -(distance / math.sin(angle / 2))
        else:
            ti = (distance / math.sin(angles[j] / 2))

        v = verts[j] + i * ti * orientation

        # ##########################################################
        # Bir Önceki noktaya bak, içbükey mi, Dar açılıysa, geri çek
        # ##########################################################
        # if len(ilkparca) > 4:
        if len(ilkparca) > 1:
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

            # Eğer offset iç ise, iç açıyı bulmak için dış açıyı 360'dan çıkarıyoruz
            if orientation < 0:
                ang = math.radians(360) - ang

            # Eğer son noktadaki açı 90 dereceden küçükse, geri çekmek gerekebilir. Şimdi onu inceliyoruz.
            if ang < math.radians(90):

                # Noktadan çizgiye mesafe kontrolü
                # Objedeki çizgileri sırayla geziyoruz
                for n in range(len(verts)):
                    if not n:
                        continue

                    # Objedeki sıradaki 2 nokta alınır
                    p0 = verts[n - 1]
                    p1 = verts[n]

                    # Eklediğimiz son noktanın obje çizgisine mesafesi bulunur
                    c, ratio = intersect_point_line(e1, p0, p1)

                    # Mesafe distance'den küçükse, Son nokta geri çekilir.
                    mes = (c - e1).length
                    if (1 >= ratio >= 0) and (mes + .01 < distance):  # and (angles[j] < math.radians(180)):

                        # İç ise, Başlangıç Noktası e2 (eksi 2. nokta)'yı al.
                        # Dış ise, şimdi ekleyeceğimiz noktayı al
                        fs = v if orientation > 0 else e2

                        # Son noktadan şimdiki noktaya olan vektör (Kenar 1)
                        v1 = fs - e1
                        # Objedeki yakın olduğumuz kenarın vektörü (Kenar 2)
                        v2 = p0 - p1

                        # Bu iki kenar arasındaki açı
                        ang = v1.angle(v2)

                        # Son noktadan şimdiki noktaya olan kenar ile objedeki yakın kenarın kesiştiği nokta
                        ya = intersect_line_line(e1, fs, p0, p1)[0]

                        # Distance nokta, oluşturğumuz kenarın neresine geliyor (oran)
                        ratio = abs(distance / math.sin(ang)) / (ya - fs).length
                        ilkparca[-1] = ya.lerp(fs, ratio)

        ilkparca.append(v)
        """"""
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


def spline_to_poly(spline):
    """Spline'ı Poly olacak şekilde çevirir. Poly noktalarını döndürür"""
    # TODO NURBS için de geliştirme yap

    vertices = []

    # Bezier ise Poly olacak şekilde noktalar oluşturulur
    if spline.type == "BEZIER":
        points = spline.bezier_points[:]

        for i in range(len(points)):
            if not spline.use_cyclic_u and not i:
                vertices.append(points[0].co)
                continue

            vertices.extend(
                interpolate_bezier(
                    points[i - 1].co, points[i - 1].handle_right,
                    points[i].handle_left, points[i].co,
                    spline.resolution_u + 1
                )[1:]
            )

            if not i:
                vertices.append(points[0].co)

    elif spline.type == "POLY":

        vertices.extend([i.co.xyz for i in spline.points])

    return vertices


def shorten_line_if_close_to_poly(line_p0, line_p1, verts, distance=.2, shorten_p0=False, shorten_p1=True, cyclic=True,
                                  check_intersect=False):
    """ TODO shorten_p0-p1 düzenle -> ekle
            line_p0-p1 aynı gelirse veya geri çekilip birbirinin tersine dönerse durumunu düzenle -> ekle
    Eğer p0-p1 arasında oluşan çizgi, poly çizgilerine yakınsa, kısalt. Eğer kesişiyorlarsa dokunma.

    :param verts: VectorList: Poly'nin noktaları
    :param line_p0: Vector: Çizginin ilk noktası
    :param line_p1: Vector: Çizginin son noktası
    :param distance: float: Sorgulanacak mesafe
    :param shorten_p0: bool: p0 kısaltılmak üzere sorgulansın mı?
    :param shorten_p1: bool: p1 kısaltılmak üzere sorgulansın mı?
    :param cyclic: bool: Poly kapalı mı?
    :param check_intersect: bool: Kesişimi sorgula

    return (new_p0, new_p1)
    """
    yon_ilk = (line_p1 - line_p0).normalized()

    for i in range(len(verts)):
        if not i and not cyclic:
            continue

        # Poly'den sıradaki 2 nokta alınır
        n0 = verts[i - 1]
        n1 = verts[i]

        # Kesişiyorsalar ya da ele alacağımız 2 Poly noktası aynıysa atlıyoruz
        if (not check_intersect and is_intersect_line_line_2d(line_p0, line_p1, n0, n1)) or n0 == n1:
            continue

        # Eklediğimiz son noktanın obje çizgisine mesafesi bulunur
        c, ratio = intersect_point_line(line_p1, n0, n1)

        # Mesafe distance'den küçükse, Son nokta geri çekilir.
        mes = (c - line_p1).length
        if (1 >= ratio >= 0) and (mes + .01 < distance):

            # Kenar 1'in vektörü
            v1 = line_p0 - line_p1

            # Objedeki yakın olduğumuz kenarın vektörü
            v2 = n0 - n1

            # Bu iki kenar arasındaki açı
            ang = v1.angle(v2)

            # Kenar 1 ile objedeki yakın kenarın kesiştiği nokta
            ya = intersect_line_line(line_p0, line_p1, n0, n1)
            if not ya:
                continue

            # Distance nokta, oluşturğumuz kenarın neresine geliyor (oran)
            ratio = abs(distance / math.sin(ang)) / (ya[0] - line_p0).length
            line_p1 = ya[0].lerp(line_p0, ratio)

    yon_son = (line_p1 - line_p0).normalized()

    # Çizginin ters dönüp dönmediği kontrol edilir. Ters dönmüşse, şimdiki nokta iptal demektir
    # if is_same_point(yon_ilk, -yon_son):
    #     return line_p0, line_p0

    return line_p0, line_p1


def is_intersect_line_line_2d(lineA_p1, lineA_p2, lineB_p1, lineB_p2):
    """Bu metodu oluşturmamızın nedeni; çünkü mevcut metod, köşe noktaları aynı olunca da kesişiyor kabul ediyor.
    Bu metod sadece True-False döndürür"""
    o = intersect_line_line_2d(lineA_p1, lineA_p2, lineB_p1, lineB_p2)

    # Çizgiler ucları dışında biryerden kesişiyorsa
    return o and \
           lineA_p1 not in (lineB_p1, lineB_p2) and \
           lineA_p2 not in (lineB_p1, lineB_p2) and \
           o != lineA_p1.xy and o != lineA_p2.xy and \
           o != lineB_p1.xy and o != lineB_p2.xy


# ############################################### ###########################
# ############################################### Noktalardaki, açıyı ve açıortay vektörünü bul
def angle_3p(p_first, p_center, p_last, radian=True, tolerance=.0001):
    """3 noktanın ortasında oluşan açıyı döndürür

    :param p_first: Vector: Başlangıç noktası
    :param p_center: Vector: Açısı hesaplanacak nokta - Köşe noktası
    :param p_last: Vector: Bitiş noktası
    :param radian: bool: Dönüş değeri radian'mı
    :param tolerance: float: Aynılığı karşılaştırırken tolere edilecek yanılma payı.

    :return bool: radian or degree
    """
    v1 = (p_first - p_center).normalized()
    v2 = (p_last - p_center).normalized()

    # iki doğru da aynı yöndeyse açı 180 derecedir. TODO Burayı düzelt, açı 0 derece de olabilir
    if (v1 + v2).length < tolerance or v2.length < tolerance:
        angle = math.radians(180)
    elif (v1 - v2).length < tolerance or v1.length < tolerance:
        angle = 0
    else:
        angle = v1.angle(v2)

        # İç / Dış açı konusunu bu kısımda çözüyoruz
        # Sağa or Sola dönme durumuna göre, iç açıyı buluyor
        if v1.cross(v2).z > 0:
            angle = math.radians(360) - angle

    return angle if radian else math.degrees(angle)


def calc_verts_angles(verts, cyclic=True):
    """Köşelerin açılarını bulur. Aynı sırayla listeye kaydeder."""
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

        angles.append(angle_3p(p0, p1, p2))
        # print("angle", math.degrees(angles[-1]))

    return angles


def bisector_3p(p_first, p_bisector, p_last, tolerance=.0001):
    """3 noktanın ortasında oluşan açıortayın birim vektörünü döndürür

    :param p_first: Vector: Başlangıç noktası
    :param p_bisector: Vector: Açıortayı hesaplanacak nokta - Köşe noktası
    :param p_last: Vector: Bitiş noktası
    :param tolerance: float: Aynılığı karşılaştırırken tolere edilecek yanılma payı.

    :return Vector: Açıortay birim vektörü
    """

    # Şimdiki noktanın açıortayı bulunur. (p1'deki açıortay -> Vector1 ile Vector2 arasında)
    v1 = (p_first - p_bisector).normalized()
    v2 = (p_last - p_bisector).normalized()

    if (v1 - v2).length < tolerance or (v1 + v2).length < tolerance:
        # print("Olur mii\n"*10)
        ort = v1.orthogonal()
        ort.z = 0
        if ort.cross(v2).z > 0:
            ort *= -1
        return ort.normalized()
    else:
        return (v1 + v2).normalized()


def calc_verts_bisector(verts, cyclic=True):
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
        if not i and not cyclic:
            # bisectors.append(bisector_3p(verts[i], -verts[i], verts[i+1]))
            # ort = (verts[0].normalized() - verts[1].normalized()).orthogonal()
            # if ort.z < 0:
            #     ort *= -1
            # ort.z = verts[0].z
            # bisectors.append(ort.normalized())
            bisectors.append(bisector_3p(verts[i], -verts[i], verts[i + 1]))
            continue

        # Önceki, Şimdiki, Sonraki nokta
        p0 = verts[i - 1]
        p1 = verts[i]
        p2 = verts[i + 1 if i != last_vert else 0]

        bisectors.append(bisector_3p(p0, p1, p2))
        # print("bisectors", bisectors[-1])

    return bisectors


# ############################################### ###########################
# ############################################### Noktalar çizgilere yakın mı veya çizgiler kesişiyor mu
def is_close_distance_to_points(verts_main, verts_target, distance, cyclic=True):
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
            if not m and not cyclic:
                continue
            p0 = verts_main[m - 1]
            p1 = verts_main[m]
            c, ratio = intersect_point_line(t, p0, p1)
            mes = (c - t).length
            if 1 >= ratio >= 0 and (mes + .001 < distance):
                return True

    return False


def intersect_line_poly(line_p0, line_p1, verts, in_2d=True, cyclic=True):
    """Line'ın Poly ile kesiştiği yerleri döndürür. SOnuçlar, line_p0'a en yakın olandan en uzak olana doğru sıralanır

    :param verts: VectorList: Poly'nin noktaları
    :param line_p0: Vector: Çizginin ilk noktası
    :param line_p1: Vector: Çizginin son noktası
    :param in_2d: bool: Kesişim 2D olarak mı incelensin?
    :param cyclic: bool: Poly Kapalı mı?

    return [(p0, p1, p_cut), ...] -> Şeklinde kesiştiği çizgileri noktaları şeklinde döndürür
    """
    lines = []
    for m in range(len(verts)):
        if not cyclic and not m:
            continue

        m0 = verts[m - 1]
        m1 = verts[m]

        if in_2d:
            o = intersect_line_line_2d(line_p0, line_p1, m0, m1)

            # Çizgiler ucları dışında biryerden kesişiyorsa
            if o:  # and o != line_p0.xy and o != line_p1.xy and o != m0.xy and o != m1.xy:

                # Kesişim noktasının Z değerini de bul. Yani 3D noktayı bul
                o = line_p0.lerp(line_p1, intersect_point_line(o, line_p0.xy, line_p1.xy)[1])

                lines.append((m0, m1, o))
        else:
            # TODO Henüz 3D'de kesişim kısmı kodlanmadı
            intersect_line_line(line_p0, line_p1, m0, m1)

    # line_p0'a en yakın olandan en uzak olana doğru sıralanır.
    lines.sort(key=lambda l: (line_p0 - l[2]).length)

    return lines


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


def is_linear_3p(p0, p1, p2, tolerance=.0001):
    """3 nokta aynı doğru üzerinde mi?

    :param p0: Vector: Point 0
    :param p1: Vector: Point 1
    :param p2: Vector: Point 2
    :param tolerance: float: Karşılaştırırken hesaplanan yanılma payı
    """
    n1 = (p1 - p0).normalized()
    n2 = (p2 - p1).normalized()
    # return n1 == n2 or (n1 - n2).length < tolerance
    # iki vektör aynıysa veya birbirine aşırı yakınsa, doğrusal kabul edilir
    return n1 == n2 or (n1 - n2).length < tolerance or (n1 + n2).length < tolerance


def is_same_point(p0, p1, tolerance=.0001):
    """2 noktanın aynı olup olmadığı kontrol edilir

    :param p0: Vector: Nokta 1
    :param p1: Vector: Nokta 2
    :param tolerance: float: Karşılaştırırken hesaplanan yanılma payı

    return: bool:
        True -> Aynı
        False-> Farklı
    """
    return (p0 == p1) or (p0 - p1).length < tolerance


def is_cyclic(verts, tolerance=.001):
    """Poly kapalı mı?

    :param verts: VectorList:
    :param tolerance: float: Karşılaştırırken hesaplanan yanılma payı

    return bool
    """
    return is_same_point(verts[-1], verts[0], tolerance)


# ############################################### ###########################
# ############################################### Kendi içinde kesişen yerlerden ayırarak yeni parça oluştur.
def split_parts_from_intersect_in_self(verts_target, tersli_duzlu=False):  # TODO cycles=True özelliği ekle
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


def disolve_doubles(verts, tolerance=0.0001):
    """Peş Peşe 2 tane aynı nokta varsa bir tanesi silinir"""
    # Verts sayısı 0 ise bitir
    if not len(verts):
        return

    # Tersten alıyoruz ki, silinince listede kayma olmasın
    for i in range(len(verts) - 1, -1, -1):
        if is_same_point(verts[i - 1], verts[i], tolerance=tolerance):
            verts.pop(i)


def clear_linear_points(verts, cyclic=True):
    """Aynı doğru üzerindeki noktaları temizle"""
    len_verts = len(verts) - 1
    for i in range(len(verts)):
        if i in (0, 1) or (i == 2 and not cyclic):
            continue

        j = len_verts - i
        # p0, p1, p2 -> Aynı doğru üzerinde mi?
        if is_linear_3p(verts[j], verts[j + 1], verts[j + 2]):
            verts.pop(j + 1)


def clear_zero_angle(verts, cyclic=True, tolerance=.001):
    """Sıfır derecelik açı oluşturan noktayı temizler"""

    len_verts = len(verts) - (2 if cyclic else 1)

    for i in range(len(verts)):
        if i in (0, 1) or (i == 2 and not cyclic):
            continue

        j = len_verts - i

        if is_same_point(verts[j + 2], verts[j], tolerance=tolerance):
            verts.pop(j + 2)
            verts.pop(j + 1)


# ############################################### ###########################
# ############################################### Kesişim yerlerinden yeni parçalar
def kesis(vertices, cyclic=True):
    _kesisim_yerlerine_nokta_ekle(vertices, cyclic)

    parcalar = []
    for i in range(len(vertices)):
        v0 = vertices[i]

        for j in range(i + 1, len(vertices)):

            if is_same_point(v0, vertices[j]):
                parcalar.append(vertices[i: j])

    for p in parcalar:
        for v in p:
            if v in vertices:
                vertices.remove(v)

    return parcalar


# ############################################### ###########################
# ############################################### Poly'yi kesişmez hale getir
def non_intersecting_poly(vertices, cyclic=False):
    # Öncelikle çakışan noktaları buluyoruz ki buralardan dönüş yapılmasın
    # cakisan = _cakisan_noktalari_bul(vertices, only_firsts=True)

    # Çakışan noktaları birbirinden birazcık uzaklaştır
    _cakisan_noktalari_uzaklastir(vertices)

    _kesisim_yerlerine_nokta_ekle(vertices, cyclic)

    # Önceden çakışan noktalar hariç, Kesişim noktalarından dönüşler yap. İlk verts'e geldiğinde bitir
    _kesisimden_yon_degis(vertices)  # , excluding=cakisan)


def _cakisan_noktalari_bul(vertices, only_firsts=False):
    """Çakışan noktaları bulur

    :param vertices: VectorList:    Poly'nin pointleri
    :param only_firsts: bool:       Çakışan noktaların sadece küçük indexli olanını al

    :return indexList: Çakışan noktaların indexleri
    """
    len_vert = len(vertices)

    indexs = []

    for i in range(len(vertices)):

        v0 = vertices[i]

        for j in range((0, i + 1)[only_firsts], len_vert):

            if is_same_point(v0, vertices[j]):
                indexs.append(i)

    return indexs


def _cakisan_noktalari_uzaklastir(vertices):
    """Çakışan noktaları birbirinden uzaklaştırır

    :param vertices: VectorList:    Poly'nin pointleri
    """
    len_vert = len(vertices)

    for i in range(len(vertices)):

        v0 = vertices[i]

        for j in range(i + 1, len_vert):

            if is_same_point(v0, vertices[j]):
                vertices[i] = vertices[i].lerp(vertices[i - 1], .001 / (vertices[i] - vertices[i - 1]).length)


def _kesisim_noktalarini_bul(vertices, z=0, cyclic=False):
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
        if not i and not cyclic:
            continue

        v0 = vertices[i - 1]
        v1 = vertices[i]
        vs = (v0, v1)

        kesisiy = []
        for j in range(len(vertices)):
            if not j and not cyclic:
                continue

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


def _kesisim_yerlerine_nokta_ekle(vertices, cyclic=False):
    """Kesişim noktalarına yeni vertexler ekler.

    :param vertices: VectorList:    Poly'nin pointleri

    return vertices -> Aynı vertices listesini geri döndürür.
    """
    # Kesişim noktaları bulunur -> [(index, Vector), ...]
    kesisimler = _kesisim_noktalarini_bul(vertices, cyclic=cyclic)

    # Kesişim noktalarına yeni vertexleri ekle
    kaydi = 0
    for i, v in kesisimler:
        vertices.insert(i + kaydi, v.freeze())
        kaydi += 1

    return vertices


def _kesisimden_yon_degis(vertices, tolerance=.0001, excluding=[]):
    """Kesişim yerlerine nokta konmuş Poly'de çizgiler ilerlerken kesişim yerlerinden diğer yöne sapar. Böylece
    kenar çizgileri kesişmez olur.

    :param vertices: VectorList:    Poly'nin pointleri
    :param tolerance: float:        İki nokta arasındaki mesafedir. Mesafe Tolerans kadardan küçükse, aynı nokta sayılır

    return vertices -> Aynı vertices listesini geri döndürür.
    """
    len_vert = len(vertices)

    for i in range(len_vert):
        v0 = vertices[i]

        if i in excluding:
            continue

        for j in range(i + 1, len_vert):
            v1 = vertices[j]
            if is_same_point(v0, v1, tolerance=tolerance):
                bura = vertices[i + 1:j][::-1]
                for l in range(i + 1, j):
                    vertices[l] = bura[l - (i + 1)]
                break

    return vertices


# ############################################### ###########################
# ############################################### Poly içini Zigzagla doldur
def clearance_zigzag(verts, angle=45, distance=1.0):
    """
    Poly vertslerinin içte kalan kısmına zigzag oluşturur.

    :param verts: VectorList: Dilimlenecek Poly'nin noktaları. Orjinal listeyi verme. Copy List olsun.
    :param angle: int: Dilimleyici hangi açıda olsun
    :param distance: float: Dilimler arası mesafe ne kadar olsun

    return [(p0, p1, p2, p3), (p0, p1), ...]    -> Poly Parçalar
    """

    # Zigzag çizgilerini hesapla
    zigzag_lines = _zigzag_vektorlerini_olustur(verts, angle, distance)

    # Zigzag çizgilerinin Ana Poly'yi kestiği noktalara yeni nokta ekle
    kesimli_hali = _zigzagda_kesisimlere_nokta_ekle(verts, zigzag_lines)

    # Ana Poly'ye minik bir offset uygula ve zigzag çigilerini uygun şekilde birleştir.
    # Offsetin sebebi, zigzag çizgilerine çok yakın olanları kesiyor saymasın diyedir..
    return _zigzag_cizgilerini_birlestir(offset_2d(verts, .0001, 1)[0], kesimli_hali)


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

                if intersect_line_line_2d(v_son, v_cur, verts_main[i - 1], verts_main[i]):
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


# ############################################### ###########################
# ############################################### Poly içini Offsetle doldur
def clearance_offset_splines(splines, distance=.2, add_screen=False):
    parcalar = []
    for s in splines:
        parcalar.extend(clearance_offset_spline(s, distance, add_screen=False))

    if add_screen:
        return new_poly_curve(parcalar, add_screen=True, cyclic=True)

    return parcalar


def clearance_offset_spline(spline, distance=.2, add_screen=False):
    verts = spline_to_poly(spline)
    parcalar = clearance_offset(verts, distance)

    if add_screen:
        return new_poly_curve(parcalar, add_screen=True, cyclic=True)

    return parcalar


def clearance_offset(verts, distance=.2):
    """Offset yapa yapa, şeklin içini doldurur"""
    parcalar = []

    for vs in offset_2d(verts, distance, -1):
        parcalar.append(vs)
        parcalar.extend(clearance_offset(vs, distance))
    return parcalar


def correct_angles(verts, distance=.2, cyclic=True):
    """distance'ın giremediği köşeleri düzelt"""
    # 90 dereceden dar açı tespit edilir ve indexi alınır
    disolve_doubles(verts)
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
        # hip = bisector_3p()
        len_p0 = (p1 - p0).length
        len_p2 = (p1 - p2).length

        # tip = [edge]
        # if len_p0:
        #     tip.append(len_p0)
        # if len_p2:
        #     tip.append(len_p2)

        # edge = min(tip)

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

        disolve_doubles(verts)
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
        ang = (angle - math.radians(180))

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


def offset_2d(verts, distance=.2, orientation=-1, cyclic=True):
    # Peş peşe aynı olan noktaları temizle
    disolve_doubles(verts)

    # Sıfır derece açı oluşturan noktaları temizle
    clear_zero_angle(verts, cyclic)

    # Aynı Doğru üzerindeki noktaları temizle
    clear_linear_points(verts, cyclic)

    # Poly çizgileri kesişmez hale getirilir
    non_intersecting_poly(verts, cyclic)

    if len(verts) < 3:
        return []

    # Her noktadaki açı bulunur
    angles = calc_verts_angles(verts)

    # İç mi dış mı olduğu düzenlenir.
    ori = orientation * (1 if mathutils.geometry.normal(verts).z > 0 else -1)

    ilkparca = []
    parcalar = [ilkparca]
    last_i = len(verts) - 1
    for i in range(len(verts)):
        if not i and not cyclic:
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
        if i == last_i and not cyclic and len(ilkparca) > 1 \
                and angles[i - 1] < math.radians(180) and (p0 - p1).length < distance:
            continue

        if len(ilkparca) > 1:
            # ilkparca.extend(add_round(ilkparca[-2], ilkparca[-1], p0, p1, verts[i-1], angles[i-1]))

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
            # elif False:
                # Kesmiyor ise, p0 değiştirilir ve e1 noktasına p0-p1 çizgisindeki en yakın bulunur
                c0, ratio0 = intersect_point_line(ilkparca[-1], p0, p1)
                c1, ratio1 = intersect_point_line(p1, ilkparca[-1], ilkparca[-2])

                # Bir önceki noktanın(e1), en yakın olduğu yer şimdiki çizginin üzerindeyse
                # AnaPoly'de önceki noktanın açısı, 180'e yakınsa,
                # Şimdiki çizgi, şimdiye kadarki çizgilerle kesişmiyorsa
                # Şimdiki çizginin iki noktası da, AnaPoly'ye distance'dan daha yakınsa
                # Şimdiki çizginin iki noktası da, önceki çizgilere yakınsa
                if 0 < ratio0 < 1 and angles[i-1] > math.radians(135) and \
                        not is_2_poly_intersect(ilkparca, (p0, p1), verts1_cyclic=False, verts2_cyclic=False) and \
                        not is_2_poly_intersect(verts, (p0, p1), verts1_cyclic=False, verts2_cyclic=False) and \
                        is_close_distance_to_points(verts, (ilkparca[-1], ilkparca[-2]), distance, cyclic=cyclic) and \
                        is_close_distance_to_points(ilkparca, (ilkparca[-1], ilkparca[-2]), distance, cyclic=cyclic):
                # if False:
                    ilkparca.pop(-1)
                    ilkparca.pop(-1)

                # Şimdiki ekleyeceğimiz son noktanın, önceki çizgiye en yakın olduğu yer çizginin üzerindeyse
                # ve aradaki mesafe distance'dan kısaysa
                elif 0 < ratio1 < 1 and angles[i-1] > math.radians(135) and (p0 - ilkparca[-1]).length < distance:

                # elif False:
                    ilkparca.insert(-1, c1.freeze())

                else:
                # elif False:
                    # """"""
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
        if len(ilkparca) > 1 and i == last_i and cyclic:
            ps = add_round(p0, p1, ilkparca[0], ilkparca[1], verts[i], angles[i])

            # Eğer 3 nokta geldiyse, anlıyoruz ki bunlar -> (ilkparca[-2], kesisim, p0) 'dır
            # Ortadaki kesisim'i ekliyoruz sadece
            if len(ps) == 3:
                ilkparca.pop(-1)
                ilkparca.append(ps[1])
            else:
                ilkparca.extend(ps)

    disolve_doubles(ilkparca)
    """"""
    for par in kesis(ilkparca, cyclic):
        disolve_doubles(par)
        parcalar.append(par)

    disolve_doubles(ilkparca)

    # return parcalar
    parcalar_son = []

    # Parçaların uygunluğu son kez kontrol edilir.
    for i in range(len(parcalar)-1, -1, -1):

        parca = parcalar[i]

        # parca başka parçanın içinde varsa diğer parçadan silinir.
        for j, k in enumerate(parcalar):
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
                (len(parca) == 3 and mathutils.geometry.area_tri(*parca) < .0001) or \
                is_close_distance_to_points(verts, parca, distance, cyclic) or \
                is_2_poly_intersect(verts, parca, verts1_cyclic=cyclic, verts2_cyclic=cyclic):
            continue

        parcalar_son.append(parca)
    return parcalar_son


if __name__ == "__main__":
    obj = bpy.context.active_object
    # vertices = [i.co.xyz for i in obj.data.splines[0].points]
    # parcas = clearance_offset_splines(obj.data.splines)
    parcas = offset_splines(obj.data.splines, add_screen=True, orientation=-1)

    # parcas = offset_2d(vertices)
    # new_poly_curve([parcas], add_screen=True)
    # correct_angles(vertices)
    # disolve_doubles(vertices, True)
    # clear_zero_angle(vertices, True)
    # clear_linear_points(vertices, True)
    # new_poly_curve([vertices], add_screen=True)

    # vs = spline_to_poly(obj.data.splines[0])
    # new_poly_curve([vs],add_screen=True)
