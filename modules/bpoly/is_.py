"""
Bu modülde birtakım sorgulamalar yer alır

is_close_distance_to_points : Noktalar çizgilere yakın mı?
is_2_poly_intersect         : Çizgiler kesişiyor mu?
is_linear_3p                : 3 nokta lineer mi
is_same_point               : 2 nokta aynı mı?
is_cyclic                   : Kapalı mı? İlk ve son noktasının aynılığı kontrol edilir.
"""


def is_linear_3p(p0, p1, p2, tolerance=.0001):
    """3 nokta aynı doğru üzerinde mi? Noktaların sırası farketmeksizin bakılır

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


def is_on_line(p0, p1, v):
    """v, çizgi üzerinde mi?"""
    return (p0 - v).length + (p1 - v).length - (p0 - p1).length < .001


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
