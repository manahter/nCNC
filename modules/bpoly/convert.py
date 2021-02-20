"""
spline_to_poly      : Spline'ı Poly noktalarına dönüştürür.
"""
from mathutils.geometry import interpolate_bezier


def spline_to_poly(spline):
    """Spline'ı Poly olacak şekilde çevirir. Poly noktalarını döndürür

    return VectorList: Vertices
    """
    # TODO NURBS için de geliştirme yap

    verts = []

    # Bezier ise Poly olacak şekilde noktalar oluşturulur
    if spline.type == "BEZIER":
        points = spline.bezier_points[:]

        for i in range(len(points)):
            if not spline.use_cyclic_u and not i:
                verts.append(points[0].co)
                continue

            verts.extend(
                interpolate_bezier(
                    points[i - 1].co, points[i - 1].handle_right,
                    points[i].handle_left, points[i].co,
                    spline.resolution_u + 1
                )[1:]
            )

            if not i:
                verts.append(points[0].co)

    elif spline.type == "POLY":

        verts.extend([i.co.xyz for i in spline.points])

    return verts
