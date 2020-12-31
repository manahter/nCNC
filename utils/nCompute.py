import math
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_point_line


# References;
# Circle Center;
# https://blender.stackexchange.com/questions/28239/how-can-i-determine-calculate-a-circumcenter-with-3-points


def replace_col(M, i, C):
    for r in range(len(M)):
        M[r][i] = C[r]


def circle_center_(B, C, N):
    m_d = Matrix([
        B, C, N
    ])
    col = [B.dot(B) * 0.5,
           C.dot(C) * 0.5,
           0]
    m_x = m_d.copy()
    replace_col(m_x, 0, col)
    m_y = m_d.copy()
    replace_col(m_y, 1, col)
    m_z = m_d.copy()
    replace_col(m_z, 2, col)
    m_d_d = m_d.determinant() or 1
    x = m_x.determinant() / m_d_d
    y = m_y.determinant() / m_d_d
    z = m_z.determinant() / m_d_d

    return Vector([x, y, z])


def circle_center(A, B, C):
    B_ = B - A
    C_ = C - A
    N = B_.cross(C_)
    return A + circle_center_(B_, C_, N)


def closest_dist_point(bm, v):
    """
    :bm: bmesh
    :v: Vector
    Point to check
    Noktanın Bmesh'deki kenarlara olan uzaklığına bakar. En yakın kenara olan uzaklığını döndürür
    """

    dist = math.inf
    for e in bm.edges[:]:
        ipl = intersect_point_line(v, e.verts[0].co, e.verts[1].co)
        if 0 <= ipl[1] <= 1:
            _dist = (v - ipl[0]).length
        else:
            _dist = min((v - e.verts[0].co).length, (v - e.verts[1].co).length)

        if _dist < dist:
            dist = _dist
    return dist
    # return min([(v - intersect_point_line(v, e.verts[0].co, e.verts[1].co)[0]).length for e in bm.edges[:]])


def closest_dist_line(bm, v0, v1):
    dist = math.inf
    for e in bm.edges[:]:
        for v in e.verts:
            ipl = intersect_point_line(v.co, v0, v1)
            if 0 <= ipl[1] <= 1:
                _dist = (v.co - ipl[0]).length
            else:
                _dist = min((v.co - v0).length, (v.co - v1).length)

            if _dist < dist:
                dist = _dist
    return dist


def disolve_verts_on_edge(edges, dist=0.0):
    """ Bu fonksiyon artık kullanılmıyor. Belki sonra işe yarar. Ama bunun yerine blender'da kullanışlılar var.
    :edges: BMEdge
    :dist: distance
    """

    dist_vec = Vector((dist, dist, dist))

    # BEdge Verts 0->minXY 1-> maxXY
    for e in edges:
        v0 = e.verts[0]
        v1 = e.verts[1]
        if v0.co.x > v1.co.x:
            _ = v0.co.copy()
            v0.co = v1.co
            v1.co = _

    # BEdge sort minX...maxX
    edges = sorted(edges, key=lambda x: x.verts[0].co.x)

    lines = []

    for e in edges:
        if not len(lines):
            lines.append(e)
            continue

        l_v0, l_v1 = [i.co for i in lines[-1].verts]
        e_v0, e_v1 = [i.co for i in e.verts]

        vec_l = l_v1 - l_v0
        vec_e = e_v1 - e_v0

        if vec_e < dist_vec:
            continue
        elif vec_l < dist_vec:
            lines[-1] = e
            continue

        ang = vec_e.angle(vec_l)

        is_linear = round(ang, 3) == 0 or round(ang, 4) == 3.1416

        if is_linear and (l_v0.x == e_v0.x or l_v1.x >= e_v0.x or l_v1 - e_v0 < dist_vec):
            l_v1.xyz = (e_v1, l_v1)[l_v1.x > e_v1.x]
        else:
            lines.append(e)

    return lines