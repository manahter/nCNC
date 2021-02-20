"""
new_parts_from_intersect    : Poly'yi kendini kestiği noktalardan ayırarak yeni parçalar döndürür
non_intersecting_poly       : Poly'yi kendini kesmez hale getirir
"""
from mathutils.geometry import intersect_line_line_2d, intersect_point_line, normal
from mathutils import Vector
from .is_ import is_same_point, is_on_line


# ############################################### Kesişim yerlerinden yeni parçalar
def new_parts_from_intersect_self(verts, cyclic=True):
    """Poly'yi kendini kestiği noktalardan ayırarak yeni parçalar döndürür

    :param verts: VectorList: Poly noktaları
    :param cyclic: bool: Kapalı mı?

    return VectorList_Lists: Parçalar döndürülür
    """
    _kesisim_yerlerine_nokta_ekle(verts, cyclic)

    parcalar = []

    # Çakışan noktalardan yeni parçalar
    for i in range(len(verts)):
        v0 = verts[i]

        for j in range(i + 1, len(verts)):

            if is_same_point(v0, verts[j]):
                parcalar.append(verts[i: j])

    # Yeni parçaları ana parçadan çıkar
    for p in parcalar:
        for v in p:
            if v in verts:
                verts.remove(v)

    return parcalar


def new_parts_from_overlaps(verts0, verts1):
    parts = []
    kes0 = []
    kes1 = []
    ind0 = len(verts0) - 1

    # disolve_doubles(verts0)
    # disolve_doubles(verts1)

    dogrultu0 = -(1 if normal(verts0).z > 0 else -1)
    dogrultu1 = (1 if normal(verts1).z > 0 else -1)

    # Çakışan yerlerden yeni parçalar oluştur
    while ind0 > -1:
        len_vs0 = len(verts0)
        if not len_vs0:
            break
        if len_vs0 <= ind0:
            ind0 = len_vs0 - 1

        p0 = verts0[ind0]

        if p0 in verts1:
            # Kesişen noktaların indexleri kaydedilir
            kes0.append(ind0)
            kes1.append(verts1.index(p0))

            # Eğer 2 tane kesişen nokta bulunduysa, 2'si arasında kalanlardan yeni parça oluşturulur
            if len(kes0) == 2:
                # print(verts0[kes0[0]], verts0[kes0[1]])
                # TODO buradaki max+1 lerde sorun çıkabilir. Burayı sonra düzelt
                part0 = verts0[min(kes0):max(kes0) + 1]

                # Verts1'den koparılacak parça, Verts0'ın iç tarafında mı kalıyor?
                part1_icte = verts0.is_inside_point(verts1[max(kes1) - 1])

                # İç offset ise ve -> verts0 ile verts1'in doğrultusu zıt ise,
                # Dş offset ise ve -> oluşturulacak part1 verts0'ın dışında kalıyorsa
                if (verts0.yon < 0 and dogrultu0 != dogrultu1 and kes1[0] < kes1[1]) or \
                        (verts0.yon > 0 and not part1_icte):
                    part1 = verts1[max(kes1):] + verts1[0:min(kes1) + 1]
                else:
                    part1 = verts1[min(kes1):max(kes1) + 1]

                for j, p in enumerate(part0[:-1]):
                    if not j:
                        continue
                    verts0.remove(p)

                for j, p in enumerate(part1[:-1]):
                    if not j:
                        continue
                    verts1.remove(p)

                kes0.clear()
                kes1.clear()
                if part0[0] == part1[0]:
                    part1.reverse()

                parts.append(verts1.new_bpoly(part0 + part1, fix=False))

                kes_son = parts[-1][-1]

                kes0.append(verts0.index(kes_son))
                kes1.append(verts1.index(kes_son))

        ind0 -= 1

    """"""
    # TODO
    #   Bu ikisi arası iyi oldu mu bilmiyorum. İleride birdaha burayı kontrol edelim
    # Yeni parçalarda en çok çakışan noktası olanı bul
    yeni0 = []
    ind0 = 0

    # Verts0 ile Verts1'i çakışan noktalarından birleştir
    # Verts0'ı dön
    while ind0 < len(verts0):
        # p0 = verts0[ind0]
        p0 = verts0.pop(ind0)

        # Point, Verts1'in içinde var mı?
        if p0 in verts1:

            # Point Verts1'de hangi indexte
            ind1 = verts1.index(p0)

            # Verts1'de birleşme yönü, ileri doğru mu geri doğru mu? 1;ileri, -1;geri
            yon = 1 if verts1[ind1 - 1] in verts0 else -1

            # İlk kesişen noktadan başlayıp, sonraki kesişen noktaya kadar biriktir.
            while verts1[ind1] not in verts0:
                p1 = verts1.pop(ind1)
                yeni0.append(p1)
                if yon < 0 and ind1 > -1:
                    ind1 += yon

                if ind1 >= len(verts1):
                    ind1 = 0
                if not len(verts1):
                    break

            if not len(verts1):
                break

            p0 = verts1.pop(ind1)

            ind0 = verts0.index(p0) + 1
        # else:

        yeni0.append(p0)

        # ind0 += 1

    verts0.clear()
    verts0.extend(yeni0)
    verts1.clear()
    # print("Verts0", verts0)
    # TODO
    #   Bu ikisi arası iyi oldu mu bilmiyorum. İleride birdaha burayı kontrol edelim
    # print("Yeni", yeni0)

    return parts


def add_point_to_intersects(verts0, verts1):
    """İki Poly çizgilerinin kesişen yerlerine iki poly için de nokta ekler. İkisi de kapalı olmalı"""
    for i in range(len(verts0) - 1, -1, -1):
        p0 = verts0[i]
        p1 = verts0[i - 1]

        # kesers = bul_kesis_line_poly(p0, p1, verts1, True)
        kesers = verts1.calc_intersect_line(p0, p1)

        # Kesişim noktaları tersten okunur
        for ind, p2 in kesers:
            verts0.insert(i, p2)

        # Sıraya koyuyoruz ki, indexe eklerken sorun yaşamayalım
        kesers = sorted(kesers, key=lambda x: x[0])

        # Kesişim noktaları tersten okunur
        for ind, p2 in kesers[::-1]:
            verts1.insert(ind, p2)


# ############################################### Poly'yi kesişmez hale getir
def non_intersecting_poly(verts, cyclic=False):
    """Poly'yi kesişmez hale getirir. Herhangi birşey döndürmez. verts listesi üzerinde işlem yapar
    :param verts: VectorList: Poly noktaları
    :param cyclic: bool: Kapalı mı?
    """
    # Öncelikle çakışan noktaları buluyoruz ki buralardan dönüş yapılmasın
    # cakisan = _cakisan_noktalari_bul(verts, only_firsts=True)
    # cakisan = _cakisan_noktalari_bul2(verts)

    # Çakışan noktaları birbirinden birazcık uzaklaştır
    _cakisan_noktalari_uzaklastir(verts)

    # TODO Nokta çizginin üzerindeyse, biraz uzaklaştır.
    _cakisan_nokta_cizgi_uzaklastir(verts)

    _kesisim_yerlerine_nokta_ekle(verts, cyclic)

    # Önceden çakışan noktalar hariç, Kesişim noktalarından dönüşler yap. İlk verts'e geldiğinde bitir
    _kesisimden_yon_degis(verts)#, excluding=cakisan)


# ############################################### Bu scripte has metodlar
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


def _cakisan_noktalari_bul2(vertices):
    """Çakışan noktaları bulur

    :param vertices: VectorList:    Poly'nin pointleri

    :return indexList: Çakışan noktaların indexleri
    """
    len_vert = len(vertices)

    points = []

    for i in range(len_vert):

        v0 = vertices[i]

        for j in range(i+1, len_vert):

            if is_same_point(v0, vertices[j]):
                points.append(v0)
                vertices[j] = v0

    return points


def _cakisan_noktalari_uzaklastir(vertices):
    """Çakışan noktaları birbirinden uzaklaştırır

    :param vertices: VectorList:    Poly'nin pointleri
    """
    len_vert = len(vertices)

    for i in range(len(vertices)):

        v0 = vertices[i]

        for j in range(i + 1, len_vert):

            if is_same_point(v0, vertices[j]):
                # TODO Burada hangi noktayı uzaklaştırdığımız çok önemli
                #   Dar açılı olanı uzaklaştırmak lazım. Tabi henüz bunu düzenlemedik. Alttaki satır geçici düzenlendi.

                vertices[i] = vertices[i].lerp(vertices[i - 1], .001 / (vertices[i] - vertices[i - 1]).length)
                # vertices[j] = vertices[j].lerp(vertices[j - 1], .001 / (vertices[j] - vertices[j - 1]).length)


def _cakisan_nokta_cizgi_uzaklastir(vertices, cyclic=False):
    len_vert = len(vertices)

    for i in range(len_vert):
        if not i and not cyclic:
            continue

        v0 = vertices[i-1]
        v1 = vertices[i]

        for j in range(len_vert):

            if i in (j, j-1):
                continue

            if is_on_line(v0, v1, vertices[j]):
                vertices[j] = vertices[j].lerp(vertices[j - 1], .001 / (vertices[j] - vertices[j - 1]).length)


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

        if v0 in excluding:
            continue

        for j in range(i + 1, len_vert):
            v1 = vertices[j]

            if is_same_point(v0, v1, tolerance=tolerance):
                bura = vertices[i + 1:j][::-1]
                for l in range(i + 1, j):
                    vertices[l] = bura[l - (i + 1)]
                break

    return vertices




