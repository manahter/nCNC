import bpy
import bmesh
import math
from mathutils import Vector


# ############################################### ###########################
# ############################################### Z'de Dilimle
def bmesh_slice(data, step_z):
    """BMesh'i dilimle

    :param data: Mesh data
    :param step_z: float: Z'de kaç mm aralıklarla dilimlensin

    return curveList
    """
    # TODO !!!
    #   Yüzey katmanlarını da taramayı ekleyelim

    curves = []
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.weld_verts(bm)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.7), verts=bm.verts, edges=bm.edges)

    for planar_edges in bmesh_planar_parts(bm):
        # Düzlemsel parçada yüzey içindeki gereksiz BMEdge'leri siliyoruz.
        for e in planar_edges[::-1]:
            # Bu kenar 2 tane yüzeyi mi birleştiriyor. O zaman sil
            if e.is_contiguous:
                planar_edges.remove(e)

        # Curve oluşturuyoruz
        curves.extend(bmedges_to_curve(planar_edges))

        # BMesh'den düzlemsel parçayı siliyoruz.
        bmesh.ops.delete(bm, geom=planar_edges, context="EDGES")

    verts_z = [v.co.z for v in bm.verts]
    min_z = min(verts_z, default=0)
    max_z = max(verts_z, default=0)
    step = max_z - step_z

    if step < min_z != max_z:
        step = min_z

    while step >= min_z:
        # BMesh'ten Z ekseninde bir kesit alınır
        cut = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                                     plane_co=Vector((0, 0, (step + .001 if step == min_z else step))),
                                     plane_no=Vector((0, 0, -1)),
                                     dist=0
                                     )["geom_cut"]

        # TODO !!Çok yavaş bir yöntem olduğu için şimdilik iptal
        #   Arada yüzey kaldıysa, yüzeyide traşla
        # for f in faces_in_z_range(bm, step, step+step_z):
        #     curves.extend(bmedges_to_curve(f.edges))

        step -= step_z
        if step < min_z and step + step_z != min_z:
            # En alt katman dilimlenebilsin diye..
            step = min_z

        curves.extend(
            bmedges_to_curve(
                # Edge'lerden Curve yap
                [e for e in cut if isinstance(e, bmesh.types.BMEdge)]
            )
        )

    return curves


def faces_in_z_range(bm, min_z, max_z):
    """Z ekseninde min_z ile max_z arasındaki yüzeyleri döndürür."""
    # bm.faces.ensure_lookup_table()
    return [f for f in bm.faces[:] if all([min_z <= v.co.z <= max_z for v in f.verts[:]])]


# ############################################### ###########################
# ############################################### BMEdge'leri doğru sırayla birleştirip Curve oluştur
def bmedges_to_curve(edges):
    """BMEdge'leri birleştirerek curve oluşturur.
    return:
        [ curve ] or [ ]
    """
    # Vertexleri indexlere ayır
    # {ind: [Edge1, Edge2], ind: [Edge1, Edge2]}
    inds = {}
    for e in edges:
        for ind in [e.verts[0].index, e.verts[1].index]:
            if ind in inds:
                # Önceki eklenen edge ile şimdi eklenen edge vertexlerini birleştir.
                verts = (*inds[ind], *e.verts[:])

                # Ortanca Vertex bulunur
                mid = max(verts, key=verts.count)

                # Vertexler kümelenir ve ortanca çıkartılır
                vts = list(set(verts))
                vts.remove(mid)

                # Vertexler, sırasına göre gruplanır.
                inds[ind] = [vts[0], mid, vts[1]]
            else:
                inds[ind] = e.verts[:]

    # print("indexes", *inds.values(), sep="\n")
    polys = []

    for ind, verts in inds.items():
        if len(verts) < 3:
            # polys.append(verts)
            verts.clear()
            continue
        polys.append(biless(inds, verts))

    # Noktalardan Spline oluştur
    if polys:
        # Eğri oluşturulur
        curve = bpy.data.curves.new("nLink", 'CURVE')
        curve.dimensions = '3D'
        # Spline oluşturulur
        for poly in polys:
            if len(poly) < 2:
                continue

            spline = curve.splines.new("POLY")

            # Burada Kapalı Curve olup olmadığına karar vermek için, ilk ve son noktaları arasındaki mesafeye bakıyoruz
            if (poly[0].co.xyz - poly[-1].co.xyz).length < .01:
                spline.use_cyclic_u = True

                # Fazlalık yapmasın diye siliyoruz. Çünkü ilk ve son vertex aynı.
                poly.remove(poly[-1])

                # Kapalı Curve ise Başlangıç noktasını değiştir. X ve Y de en küçük noktayı başlangıç noktası yap
                ind = poly.index(min(poly, key=lambda k: [k.co.x, k.co.y]))
                bas = poly[:ind]
                poly = poly[ind:]
                poly.extend(bas)

            spline.points[0].co.xyz = poly[0].co.xyz
            for v in poly[1:]:
                spline.points.add(1)
                spline.points[-1].co.xyz = v.co.xyz

        return [curve]
    return []


def biless(data, bilesen):
    """Vertexleri birleştirir.
    :param data: dict: Birbiriyle bağlantı kuran vertexler
        { 0: [vertex-1, vertex0, vertex1],
          1: [vertex0, vertex1, vertex2], ... }
    :param bilesen: list: Birleşmiş Vertexler listesi. birleşim noktalarına göre sıralanmışlardır.

    return: bilesen
    """

    # Birleşendeki son Vertexi alıyoruz ve datadan o vertex bağlı diğerlerini bulup alıyoruz.
    _verts = data[bilesen[-1].index].copy()

    # Vertexleri aldık içini temizleyelim.
    data[bilesen[-1].index].clear()

    # Bitir, 3 taneden az vertex varsa, bilesen 2 taneden az ise, vertexlerin ilki ve sonuncusu aynıysa dön
    if (len(_verts) < 3) or (len(bilesen) < 2) or bilesen[0] == bilesen[-1]:  # len(set(_verts) - set(bilesen)) < 1 or
        return bilesen

    # Vertexlerdeki son
    if bilesen[-2] != _verts[0]:
        _verts.reverse()

    bilesen = biless(data, bilesen[:-2] + _verts)
    bilesen.reverse()
    return biless(data, bilesen)


# ############################################### ###########################
# ############################################### ##BMesh'in düzlemsel parçalarını döndür
def bmesh_planar_parts(bm):
    """Düzlemsel parçaları döndürür. Edgeleri parçalarına ayırır ve düzlemsel olup olmadıklarını sorgular.
    return:
    [
        { Edge1, Edge2..}   -> Part1
        { Edge1, Edge2..}   -> Part2
    ]
    """
    return [list(p["edges"]) for p in bmesh_independent_parts(bm) if is_planar(p["edges"])]


def bmesh_independent_parts(bm):
    """BMesh'i bağımsız parçalarına ayırır.
    return:
    [
        {"verts": {Vert1, Vert2...}, "edges": {Edge1, Edge2...}}    -> Part1
        {"verts": {Vert1, Vert2...}, "edges": {Edge1, Edge2...}}    -> Part2...
    ]
    """
    bm.edges.ensure_lookup_table()

    edges = bm.edges[:]
    parts = []
    while edges:
        is_append = False
        for e in edges[::-1]:
            v0, v1 = e.verts[:]
            for p in parts:
                if v0 in p["verts"] or v1 in p["verts"]:
                    p["edges"].add(e)
                    p["verts"].add(v0)
                    p["verts"].add(v1)
                    edges.remove(e)
                    is_append = True
                    break

            if is_append:
                break

        if not is_append:
            e = edges[-1]
            v0, v1 = e.verts[:]
            parts.append({"verts": {v0, v1}, "edges": {e}})

    return parts


def is_planar(edges):
    """BMEdge'lerin düzlemsel olup olmadığını döndürür"""
    for e in edges:
        # İki kenarın birbirine bitişik olduğunda, arada kalan görünmeyen yüzeyleri telafi edebilmek için, alanları
        # kontrol edilerek işleme devam edilir.
        if e.is_contiguous and e.calc_face_angle(None) and \
                e.link_faces[0].calc_area() > 0.01 and e.link_faces[1].calc_area() > 0.01:
            return False
    return True