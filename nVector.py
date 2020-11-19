from mathutils import Vector
import math

# Faydalı olabilecek kaynaklar:
# Uzay Geometri;
#   http://www.watewatik.com/1-unite-uzayda-vektorler/ders-4/islemler
#   https://www.youtube.com/watch?v=R_sw6Klf0pY
#
# Bezier eğrileri;
#   http://bilgisayarkavramlari.sadievrenseker.com/2009/10/31/bezier-egrileri-bezier-curves/
# NURBS;
#   http://bilgisayarkavramlari.sadievrenseker.com/2009/08/10/splines-seritler/
#
# BERNSTEIN POLiNOMLARI
#   http://acikerisim.ege.edu.tr:8081/jspui/bitstream/11454/3441/1/abdullahgungoz2008.pdf
# Üç noktası bilinen çemberin merkezi;
#   https://math.stackexchange.com/questions/1076177/3d-coordinates-of-circle-center-given-three-point-on-the-circle
#   https://github.com/sergarrido/random/tree/master/circle3d
#   https://matematik.academy/wp-content/uploads/2015/04/%C3%96ABT-Uzayda-Do%C4%9Fru-ve-D%C3%BCzlem-PDF.pdf
#
# Üç noktası bilinen çemberin merkezi; (2 Boyutta - Türkçe - Linkin sonunda)
#   https://www.r10.net/programlama/1131947-verilen-3-noktadan-gececek-cember-cizdirmek.html
#
# Üç noktası bilinen çemberin yarıçapı; (Greek000 isimli kullanıcı)
#   https://www.physicsforums.com/threads/equation-of-a-circle-through-3-points-in-3d-space.173847/
#
# Sympy modülü
#   https://docs.sympy.org/latest/tutorial/index.html
#
# Blender Curve Koordinat noktalarını bulma;
#   https://github.com/baronwatts/blender-curve-coordinate-points/blob/master/export_curve_points.py
#
# Çemberin genel denklemi, Üç noktası bilinen çemberin denklemi
#   http://capyayinlari.com.tr/demo/geometri-cember.pdf


# Nurbs araştır:
#   https://math.stackexchange.com/questions/417030/what-is-the-general-formula-for-nurbs-curves
#


class nVector:
    @classmethod
    def bul_uzaklik_2p(cls, p0, p1):
        """İki nokta arasındaki mesafeyi döndürür.
        :param p0: Vector   : X,Y,Z
        :param p1: Vector   : X,Y,Z
        :return:   Float    : d --> Noktalar arası uzaklık
        """
        return math.sqrt(pow((p0.x-p1.x), 2) + pow((p0.y-p1.y), 2) + pow((p0.z-p1.z), 2))

    @classmethod
    def bul_cember_yaricapi_3p(cls, p0, p1, p2):
        """Çevresi üzerindeki 3 noktası bilinen çemberin yarıçapını döndürür
        :param p0: Vector   : X,Y,Z
        :param p1: Vector   : X,Y,Z
        :param p2: Vector   : X,Y,Z
        :return:   Float    : R --> Çemberin yarıçapı
        """
        a = cls.bul_uzaklik_2p(p0, p1)
        b = cls.bul_uzaklik_2p(p0, p2)
        c = cls.bul_uzaklik_2p(p1, p2)

        ust = a * b * c
        alt = math.sqrt(2 * (pow(a * b, 2) + pow(b * c, 2) + pow(c * a, 2)) - pow(a, 4) - pow(b, 4) - pow(c, 4))
        return ust / alt

    @classmethod
    def bul_cember_merkezi_3p(cls, p1, p2, p3, duzlem="G17"):
        """Üç noktası verilen çemberin merkez koordinatını döndürür.
        Kaynak: https://math.stackexchange.com/questions/1076177/3d-coordinates-of-circle-center-given-three-point-on-the-circle
        User  : mululu
        :param p1:  Vector  : Point1
        :param p2:  Vector  : Point2
        :param p3:  Vector  : Point3
        :param duzlem       : ["G17", "G18", "G19", "XYZ"]  Düzlem seçin, G17:XY,  G18:XZ,  G19:YZ,  XYZ:3Dsistem
        :return:    Vector  : Çemberin merkez koordinatı
        """
        if duzlem == "XYZ":
            # P1-P2 arası vektör
            Cx = p2.x - p1.x
            Cy = p2.y - p1.y
            Cz = p2.z - p1.z

            # P1-P3 arası vektör
            Bx = p3.x - p1.x
            By = p3.y - p1.y
            Bz = p3.z - p1.z

            # 
            B2 = p1.x ** 2 - p3.x ** 2 + p1.y ** 2 - p3.y ** 2 + p1.z ** 2 - p3.z ** 2
            C2 = p1.x ** 2 - p2.x ** 2 + p1.y ** 2 - p2.y ** 2 + p1.z ** 2 - p2.z ** 2

            CByz = Cy * Bz - Cz * By
            CBxz = Cx * Bz - Cz * Bx
            CBxy = Cx * By - Cy * Bx
            try:
                ZZ1 = -(Bz - Cz * Bx / Cx) / (By - Cy * Bx / Cx)
            except:
                ZZ1 = 0

            try:
                Z01 = -(B2 - Bx / Cx * C2) / (2 * (By - Cy * Bx / Cx))
            except:
                Z01 = 0

            try:
                ZZ2 = -(ZZ1 * Cy + Cz) / Cx
            except:
                ZZ2 = 0

            try:
                Z02 = -(2 * Z01 * Cy + C2) / (2 * Cx)
            except:
                Z02 = 0

            try:
                dz = -((Z02 - p1.x) * CByz - (Z01 - p1.y) * CBxz - p1.z * CBxy) / (ZZ2 * CByz - ZZ1 * CBxz + CBxy)
            except:
                dz = 999999999     # Hata çıkarsa bozuk sayı verir

            dx = ZZ2 * dz + Z02
            dy = ZZ1 * dz + Z01

            return Vector((dx, dy, dz))

        elif duzlem == "G17":
            ko = cls.bul_cember_merkezi_2D_3p(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
            return Vector((ko[0], ko[1], 0))
        elif duzlem == "G18":
            ko = cls.bul_cember_merkezi_2D_3p(p1.x, p1.z, p2.x, p2.z, p3.x, p3.z)
            return Vector((ko[0], 0, ko[1]))
        elif duzlem == "G19":
            ko = cls.bul_cember_merkezi_2D_3p(p1.y, p1.z, p2.y, p2.z, p3.y, p3.z)
            return Vector((0, ko[0], ko[1]))

    @classmethod
    def bul_cember_merkezi_2D_3p(cls, x1, y1, x2, y2, x3, y3):
        # Kaynak: http://www.ambrsoft.com/TrigoCalc/Circle3D.htm

        kxy1 = pow(x1, 2) + pow(y1, 2)
        kxy2 = pow(x2, 2) + pow(y2, 2)
        kxy3 = pow(x3, 2) + pow(y3, 2)

        A = x1 * (y2-y3) - y1 * (x2-x3) + x2*y3 - x3*y2
        B = kxy1*(y3-y2) + kxy2*(y1-y3) + kxy3*(y2-y1)
        C = kxy1*(x2-x3) + kxy2*(x3-x1) + kxy3*(x1-x2)
        # D = kxy1*(x3*x2-x2*y3) + kxy2*(x1*y3-x3*y1) + kxy3*(x2*y1-x1*y2)
        x = -(B / (2*A)) if abs(A) != 0 else 999999999
        y = -(C / (2*A)) if abs(A) != 0 else 999999999
        # r = math.sqrt( pow(x-x1,2) + pow(y-y1,2) )
        return x, y

    @classmethod
    def bul_duzlemin_denklemi_3p(cls, p1, p2, p3):
        """Üç noktası verilen düzlemin denklemini döndürür. Uyarı : Noktalar tek doğru üzerinde olmamalı
        :param p1:  Vector  : Point1 Düzlem üzerinden bir nokta
        :param p2:  Vector  : Point2 Düzlem üzerinden bir nokta
        :param p3:  Vector  : Point3 Düzlem üzerinden bir nokta
        :return:    Denklem : from sympy import symbols
        """
        # Uyarı : Bu Fonksiyon, şu modül ile geçerlidir ve şuan işleme alınmamıştır.
        #       from sympy import symbols

        # x, y, z = symbols("x y z")                  # P   : Düzlem üzerinde herhangi bir P noktası
        # p1_p =  [x-p1.x,    y-p1.y,    z-p1.z]      # p1P : P1'den P'ye bir doğru
        # p1_p2 = [p2.x-p1.x, p2.y-p1.y, p2.z-p1.z]   # p1P2: P1'den P2'e bir doğru
        # p1_p3 = [p3.x-p1.x, p3.y-p1.y, p3.z-p1.z]   # p1P3: P1'den P3'e bir doğru
        # M = [p1_p, p1_p2, p1_p3, p1_p, p1_p2]       # Matris
        # t = 0
        # for i in range(3):                          # Matrisin determinantı alınır.
        #     t += M[i][0] * M[i+1][1] * M[i+2][2] - M[i][2] * M[i+1][1] * M[i+2][0]
        # return t

    @classmethod
    def bul_dogrunun_denklemi_2p(cls, p1, p2):
        """İki noktası verilen doğrunun denklemini döndürür
        :param p1:  Vector  : Point
        :param p2:  Vector  : Point
        :return:    Denklem : from sympy import symbols
        """
        # Uyarı : Bu Fonksiyon, şu modül ile geçerlidir ve şuan işleme alınmamıştır.
        #       from sympy import symbols

        # k = symbols("k")        # katsayı, PB vektör uzunluğunun yüzde kaçında gibi
        # x = p1.x + k*(p2.x - p1.x)
        # y = p1.y + k*(p2.y - p1.y)
        # z = p1.z + k*(p2.z - p1.z)
        # return x,y,z #Vector((x,y,z))

    @classmethod
    def bul_dogrunun_ortasi_2p(cls, p1, p2):
        x = (p2.x+p1.x) / 2
        y = (p2.y+p1.y) / 2
        z = (p2.z+p1.z) / 2
        return Vector((x,y,z))

    def _buub(cls, t, p0, p1, p2, p3):
        """ 4 noktası bilinen BezierCurve'un üstünden bir noktanın koordinarını döndürür. sadece X,Y veya Z
        :param t:   Float [0.0 : 1.0]   Bulunan nokta, bezier'in yüzde kaçında olsun gibi
        :param p0:  Float   : Point0 koordinatı : Başlangıç noktası
        :param p1:  Float   : Point1 koordinatı
        :param p2:  Float   : Point2 Koordinatı
        :param p3:  Float   : Point3 Koordinatı : Bitiş noktası
        :return:    Float   : %t'de bulunan nokta
        """
        a = (1 - t)
        b = t

        a1 = 1 * pow(a, 3) * p0
        a2 = 3 * pow(a, 2) * b * p1
        a3 = 3 * pow(b, 2) * a * p2
        a4 = 1 * pow(b, 3) * p3
        nokta = a1 + a2 + a3 + a4

        return nokta

    def _buub2(self, t, p0, p1, ):
        pass

    @classmethod
    def bul_bezier_nokta_4p1t(cls, t, p0, p1, p2, p3):
        """ 4 noktası bilinen BezierCurve'un üstünden bir noktanın koordinarını döndürür
        :param t:   Float [0.0 : 1.0]   Bulunan nokta, bezier'in yüzde kaçında olsun
        :param p0:  Float   : Point0 koordinatı : Başlangıç noktası
        :param p1:  Float   : Point1 koordinatı
        :param p2:  Float   : Point2 Koordinatı
        :param p3:  Float   : Point3 Koordinatı : Bitiş noktası
        :return:    Float   : %t'de bulunan nokta
        """
        x = cls._buub(cls, t, p0.x, p1.x, p2.x, p3.x)
        y = cls._buub(cls, t, p0.y, p1.y, p2.y, p3.y)
        z = cls._buub(cls, t, p0.z, p1.z, p2.z, p3.z)
        return Vector((x, y, z))

    @classmethod
    def carp_2v(cls, v1, v2):
        """ İki vektörün benzer koordinatlarının çarğımını döndürür. Yani x'i x ile, y'yi y ile çarpar
        :param v1:  Vector :
        :param v2:  Vector :
        :return:    Vector :
        """
        temp = []

        for x, i in enumerate(v1):
            temp.append(i * v2[x])

        return Vector(temp)

    @classmethod
    def bol_1s1v(cls, s1, v1):
        """Sabit / v1.x  , Sabit / v1.y şeklinde değerleri böler ve vektör döndürür
        :param s1:  Float   : Bir sayı
        :param v1:  Vector  : Bir koordinat değeri
        :return:    Vectör  : Sabit sayı tarafından bölünmüş vektör
        """
        temp = []

        for i in range(3):
            if v1[i] == 0:
                temp.append(0)
            else:
                temp.append(s1 / v1[i])

        return Vector(temp)

    @classmethod
    def faktoriyel(cls, f):
        tum = 1
        for i in range(2,f+1):
            tum *= i
        return tum

    @classmethod
    def bernstein_polinomu(cls, i, n, t):
        """n'inci dereceden Bernstein  polinomu
        :param i:   Float   : Başlangıç -> 0
        :param n:   Float   : Bitiş     -> Kaç adet değer varsa - 1
        :param t:   Float   : 0.0-1.0   -> Oran
        :return:
        """
        f = cls.faktoriyel(n) / (cls.faktoriyel(i) * cls.faktoriyel(n-i))   # Binom katsayısı
        return f * pow(t, i) * pow((1-t), (n-i))

    @classmethod
    def bul_bezier_egrisi_1t1pl(cls, t, p_list):
        """ Gelişim aşamasında
        :param t:       Float   : 0.0-0.1 arası.
        :param p_list:  List    : Point List -> Eğri üzerindeki noktalar
        :return:    t oranındaki noktanın koordinatı
        """
        n = len(p_list)
        tum = Vector((0.0,0.0,0.0))
        for i in range(n):
            ks = cls.bernstein_polinomu(i, n, t)
            tum += ks * p_list[i]

        return tum

    @classmethod
    def bul_nurbs_1t1pl(cls, t, context):
        # ### UYARI!!!!! Gelişim aşamasında
        # Toplamların 0'dan mı 1'den mi başladıklarına dikkat et..
        nurb =context.active_object.data.splines[0]
        n = len(nurb.points)

        if t == 1:
            return nurb.points[n-1].co
        elif t == 0:
            return nurb.points[0].co

        # Normalize faktörü
        payda = 0
        for j in range(n):
            Njn = cls.bernstein_polinomu(j, n, t)
            wj = nurb.points[j].weight
            payda+= Njn*wj

        tum = Vector((0.0,0.0,0.0, 0.0))
        for i in range(n):
            Nin = cls.bernstein_polinomu(i, n, t)
            wi = nurb.points[i].weight
            Rin = (Nin*wi) / payda if payda != 0 else 0
            tum += nurb.points[i].co * (Rin if payda != 0 else 1)
            # if t == 1:
            #     print("payda :",payda)
            #     print("Nin   :",Nin)
            #     print("wi    :",wi)
            #     print("tum---:",tum)
        return tum

    @classmethod
    def bul_yonu_1m3p(cls, m, p1, p2, p3):
        """ Merkezi verilen ve çemberin çeperinde verilen 3 noktanın hangi yöne doğru döndüklerini hesaplar.
        Saat yönü veya tersi yön.
        :param m:   Vector  : Merkez koordinatı
        :param p1:  Vector  : Point1    Başlanılan nokta
        :param p2:  Vector  : Point2    Orta nokta
        :param p3:  Vector  : Point3    Gidilen nokta
        :return:    Yön : G2 -> Saat yönü    G3 -> Saat yönü tersi
        """
        r = cls.bul_uzaklik_2p(m, p1)
        a1 = cls.merkeze_nokta_kac_derecede(m, r, p1)
        a2 = cls.merkeze_nokta_kac_derecede(m, r, p2)
        a3 = cls.merkeze_nokta_kac_derecede(m, r, p3)

        deger = 9.312
        if round(p1.y, 3) == deger or round(p2.y, 3) == deger or round(p3.y, 3) == deger:
            print("\ta1, a2, a3", a1, a2, a3)

        if a1 > a2 > a3:
            return 2
        elif a1 > a2 and a3 > a1 and a3 > a2:
            return 2
        elif a1 < a2 and a1 < a3 and a2 > a3:
            return 2
        # elif a1 > a2 and a2 < a3:
        #     return "G2"
        # elif a1 > a2 and a1 > a3 and a2 < a3:
        #     return "G2"
        else:
            return 3

    @classmethod
    def merkeze_nokta_kac_derecede(cls, m, r, p):
        """Hedef Noktanın, Merkez Noktaya yaptığı açı hesaplanır
        :param m: Vector    : Merkez koordinat
        :param r: Float     : Yarıçap
        :param p: Vector    : Point -> Çemberin çevresinden bir nokta
        :return:    XYZ'de kaç derece
        """
        # ## Uyarı !!!   Bu formül yeterince hesaplanmamıştır.
        # ##             3 Boyutlu karışık işlemlerde doğru sonuç döndürmeyebilir
        x = p.x - m.x            # X Noktaları arası mesafe
        y = p.y - m.y            # Y Noktaları arası mesafe
        z = p.z - m.z            # Z Noktaları arası mesafe

        h = math.sqrt(pow(x, 2) + pow(y, 2))    # XY'nin Hipotenüsü

        # aci_xy = ((2*math.pi) - math.acos( x / h ))  if y < 0 else math.acos( x / h )
        # aci_xz = ((2*math.pi) - math.acos( h / r ))  if y < 0 else math.acos( h / r )
        bolum = x / r
        if bolum < -1:
            bolum = -1
        elif bolum > 1:
            bolum = 1

        aci_xyz = ((2*math.pi) - math.acos(bolum)) if y < 0 else math.acos(bolum)

        return aci_xyz

    @classmethod
    def bul_dogru_uzerindemi_3p(cls, p1_ilk, p3_son, p2_bak, yuvarla=3):
        """P2 noktasını kontrol eder. P1 ile başlayıp, P3 ile biten doğru parçasının üzerinde mi?
        :param p1_ilk:  Vector  : Point1    Doğrunun başlangıç noktası
        :param p3_son:  Vector  : Point2    Doğrunun bitiş noktası
        :param p2_bak:  Vector  : Point3    Sorgulanan nokta
        :param yuvarla: Int     : 3         Virgülden kaç basamaktan ötesi hesaplanmasın
        :return:        Bool    : True-> Üzerinde   False-> Değil
        """

        oran_xy = (p3_son.x - p1_ilk.x) / (p3_son.y - p1_ilk.y) if (p3_son.y - p1_ilk.y) else 1
        oran_xz = (p3_son.x - p1_ilk.x) / (p3_son.z - p1_ilk.z) if (p3_son.z - p1_ilk.z) else 1

        # Orana Bak
        obak_xy = (p3_son.x - p2_bak.x) / (p3_son.y - p2_bak.y) if (p3_son.y - p2_bak.y) else 1
        obak_xz = (p3_son.x - p2_bak.x) / (p3_son.z - p2_bak.z) if (p3_son.z - p2_bak.z) else 1

        return round(obak_xy, yuvarla) == round(oran_xy, yuvarla) and round(obak_xz, yuvarla) == round(oran_xz, yuvarla)

    @classmethod
    def yuvarla_vector(cls, basamak, vector):
        return Vector((round(vector.x, basamak), round(vector.y, basamak), round(vector.z, basamak)))

    @classmethod
    def bul_cember_uzerindemi_(cls, p1_ilk, p2_orta, p3_son, p0_sorgu):
        # Henüz tamamlanmadı
        merkez = cls.yuvarla_vector(3, cls.bul_cember_merkezi_3p(p1_ilk, p2_orta, p3_son))
        sorgu1 = cls.yuvarla_vector(3, cls.bul_cember_merkezi_3p(p1_ilk, p0_sorgu, p2_orta))
        sorgu2 = cls.yuvarla_vector(3, cls.bul_cember_merkezi_3p(p1_ilk, p0_sorgu, p3_son))
        return merkez == sorgu1 and merkez == sorgu2

    @classmethod
    def bul_cember_uzerinde_noktalar_1m2p(cls, m, p1, p2):
        pass

    @classmethod
    def bul_ucgenin_acilari_3p(cls, p1, p2, p3):
        """3 noktasın koordinatları verilen üçgenin 3 köşesinin de açısı bulunur.
        :param p1:  Vector  : Point1    Doğrunun başlangıç noktası
        :param p2:  Vector  : Point2    Doğrunun bitiş noktası
        :param p3:  Vector  : Point3    Sorgulanan nokta
        :return:        Bool    : True-> Üzerinde   False-> Değil
        """

        l1 = cls.bul_uzaklik_2p(p2, p3)
        l2 = cls.bul_uzaklik_2p(p1, p3)
        l3 = cls.bul_uzaklik_2p(p1, p2)

        a1 = ((pow(l1, 2) - pow(l2, 2) - pow(l3, 2)) / (2*l2*l3))