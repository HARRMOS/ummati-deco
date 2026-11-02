"""
AYAH by INOMA — pièces imprimables (CadQuery).
    ../.venv-cad/bin/python ayah_parts.py          -> stl/*.stl  +  step/*.step

Toutes les cotes sont en mm. Les cotes marquées « À VÉRIFIER » dépendent des composants
réellement achetés : mesure-les au pied à coulisse et corrige-les ici avant d'imprimer.

Visserie : vis M3 + inserts laiton M3 à chaud (trou Ø4,0 × 6 mm, type Ruthex M3x5.7).
"""
import math, os
import numpy as np
import cadquery as cq

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)
os.makedirs(os.path.join(OUT, "step"), exist_ok=True)

# ============================================================== PARAMÈTRES
H = 215.0                       # hauteur totale de l'objet
WF, DF = 0.92, 0.85             # proportions largeur / profondeur (design v3)
BASE_TOP = 0.20 * H             # 43 : dessus de la base = pied de la niche
PLATE_T = 3.0                   # fond démontable
BASE_A, BASE_B = 83.0, 71.0     # demi-axes de la base (en bas)
BASE_TAPER = 0.965              # la base s'affine vers le haut
WALL = 2.5                      # parois de la base
SHELL_T = 3.0                   # parois de la niche
TOP_FILLET = 4.0
FACET_Y = -62.0                 # face plate avant (écran)

INSERT_D, INSERT_L = 4.0, 6.0   # insert M3
CLEAR_D = 3.4                   # passage vis M3
FIT = 0.15                      # jeu d'emboîtement

# --- composants (À VÉRIFIER)
ESP_L, ESP_W = 64.0, 28.5       # ESP32-S3 DevKitC (clone 2 × USB-C)
ESP_POST_H = 5.0                # dégagement sous la carte (montée composants vers le bas, broches en haut)
AMP_L, AMP_W = 19.5, 18.5       # MAX98357A
SD_L, SD_W = 42.0, 24.5         # module microSD SPI
SPK_D, SPK_FLANGE = 52.0, 3.0   # haut-parleur 50–52 mm
SCR_ACTIVE = (43.5, 23.5)       # fenêtre visible écran 1,9" 170×320
SCR_PCB = (52.0, 28.0, 4.5)     # module écran (L, H, épaisseur verre+PCB)
ENC_HOLE = 7.3                  # EC11 : canon M7
SHAFT_D, SHAFT_FLAT = 6.0, 4.5  # axe en D de l'EC11
BRASS_D = 4.0                   # tube laiton de suspension

# ============================================================== DESIGN (identique au rendu v3)
def X(v): return v * H * WF
def Y(v): return v * H * DF
def Z(v): return v * H

Y_FRONT = Y(-0.13)
ZS = [.20, .25, .30, .35, .40, .45, .50, .55, .60, .65, .70, .75, .80, .85, .90, .95, .975, 1.0]
XL = [-.370, -.389, -.401, -.406, -.407, -.403, -.393, -.377, -.354, -.324, -.287, -.236, -.167, -.080, -.022, .017, .024, .028]
XR = [.382, .393, .409, .416, .420, .418, .413, .403, .389, .368, .342, .311, .272, .230, .175, .108, .071, .028]
YB = [.300, .307, .312, .316, .315, .313, .305, .293, .279, .260, .234, .203, .164, .121, .076, .023, -.05, -.125]
C1 = [(-.36, .205), (-.37, .30), (-.355, .40), (-.32, .50), (-.265, .58), (-.19, .66), (-.10, .74), (-.02, .81), (.06, .865)]
C2 = [(-.285, .205), (-.29, .30), (-.265, .40), (-.21, .50), (-.135, .58), (-.05, .66), (.02, .74), (.06, .865)]
C3 = [(-.24, .17), (-.245, .30), (-.22, .40), (-.16, .50), (-.08, .58), (.02, .66), (.09, .745), (.15, .81)]
R1 = [(.15, .81), (.215, .77), (.27, .71), (.31, .64), (.345, .55), (.36, .45), (.362, .35), (.35, .25), (.33, .17)]


def catmull(pts, n=16):
    P = [np.array(p, float) for p in pts]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t1 = np.linalg.norm(p1 - p0) ** .5; t2 = t1 + np.linalg.norm(p2 - p1) ** .5; t3 = t2 + np.linalg.norm(p3 - p2) ** .5
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            a1 = (t1 - t) / t1 * p0 + t / t1 * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / t2 * a1 + t / t2 * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(P[-2])
    return np.array(out)


def resample(poly, step=1.2):
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])
    t = np.linspace(0, s[-1], max(3, int(s[-1] / step) + 1))
    return np.stack([np.interp(t, s, poly[:, 0]), np.interp(t, s, poly[:, 1])], 1)


def curve(pts, step=1.2):
    c = catmull(pts)
    return resample(np.stack([X(c[:, 0]), Z(c[:, 1])], 1), step)


zs_s = catmull(list(zip(ZS, XL)))[:, 0]
xl_s, xr_s, yb_s = (catmull(list(zip(ZS, a)))[:, 1] for a in (XL, XR, YB))


def section(zn):
    xl, xr, yb = (float(np.interp(zn, zs_s, a)) for a in (xl_s, xr_s, yb_s))
    return X((xl + xr) / 2), X((xr - xl) / 2), Y(yb) - Y_FRONT   # centre x, demi-largeur, profondeur


def front_prism(poly, y0, y1):
    """Prisme d'un contour vu de face (x, z), entre y0 et y1 (y0 < y1)."""
    pts = [tuple(map(float, p)) for p in poly]
    if np.linalg.norm(np.array(pts[0]) - np.array(pts[-1])) < 1e-6:
        pts = pts[:-1]
    return (cq.Workplane("XY").polyline(pts).close().extrude(y1 - y0)
            .translate((0, 0, -y1)).rotate((0, 0, 0), (1, 0, 0), 90))


def poly_offset(poly, d):
    """Décalage 2D d'un contour (d > 0 vers l'extérieur) via le noyau OCC."""
    poly = np.asarray(poly, float)
    x, y = poly[:, 0], poly[:, 1]
    if 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y) < 0:        # sens trigo
        poly = poly[::-1]
    pts = [tuple(map(float, p)) for p in poly]
    if np.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-6:
        pts = pts[:-1]
    w = cq.Workplane("XY").polyline(pts).close().val()
    o = w.offset2D(d, "arc")[0]
    n = max(60, int(o.Length() / 1.0))
    pts = [o.positionAt(t, mode="length") for t in np.linspace(0, 1, n, endpoint=False)]
    pts = [(p.x, p.y) for p in pts]
    return resample(np.array(pts + [pts[0]]), 1.0)


def insert_boss(x, y, z_top, h, d=8.0):
    """Colonne avec trou pour insert M3 ouvert vers le bas."""
    return (cq.Workplane("XY").workplane(offset=z_top - h).center(x, y).circle(d / 2).extrude(h)
            .faces("<Z").workplane().hole(INSERT_D, INSERT_L))


def export(shape, name):
    shape = shape.val() if isinstance(shape, cq.Workplane) else shape
    print(f"{name:22s} valide={shape.isValid()}  bbox={[round(v, 1) for v in (shape.BoundingBox().xlen, shape.BoundingBox().ylen, shape.BoundingBox().zlen)]}")
    cq.exporters.export(shape, os.path.join(OUT, "stl", name + ".stl"), tolerance=0.05, angularTolerance=0.15)
    cq.exporters.export(shape, os.path.join(OUT, "step", name + ".step"))


# ============================================================== POSITIONS COMMUNES
c3, r1 = curve(C3), curve(R1)
opening = np.concatenate([c3, r1[1:]])
c1, c2 = curve(C1), curve(C2)
window = np.concatenate([c1, c2[::-1][1:]])

SPH_R = 28.0
sph_z = BASE_TOP + 16 + SPH_R + 12
sph_x = float((np.interp(sph_z, c3[:, 1], c3[:, 0]) + np.interp(sph_z, r1[::-1][:, 1], r1[::-1][:, 0])) / 2)
sph_y = Y_FRONT + SPH_R * 0.95

# vis niche -> base : 4 pattes plaquées contre la paroi intérieure de la niche
def inner_wall_point(theta, inset):
    xc, w, d = section(0.2)
    w, d = w - SHELL_T, d - SHELL_T
    p = np.array([xc + w * math.cos(theta), Y_FRONT + d * math.sin(theta)])
    n = np.array([math.cos(theta) / w, math.sin(theta) / d]); n /= np.linalg.norm(n)
    return p - n * inset


DOME_SCREWS = [tuple(inner_wall_point(t, 2.2)) for t in (math.radians(20), math.radians(70), math.radians(110))]
WING_HOLE = ((X(-0.36) + X(-0.285)) / 2, Y_FRONT + 5.0)          # passage câbles de la cavité LED
DOME_SCREWS.append((WING_HOLE[0] + 1.0, Y_FRONT + 13.0))

# ============================================================== 1. NICHE (coque + cadre + aile + cavité LED)
def d_wire(zn, off, front_ext=0.0, n=24):
    xc, w, d = section(zn)
    w, d = max(w - off, 0.8), max(d - off, 0.8)
    z = Z(zn)
    pts = [cq.Vector(xc + w * math.cos(math.pi * j / n), Y_FRONT + d * math.sin(math.pi * j / n), z) for j in range(n + 1)]
    edges = [cq.Edge.makeSpline(pts)]
    if front_ext:
        a, b = pts[-1], pts[0]
        a2, b2 = cq.Vector(a.x, a.y - front_ext, z), cq.Vector(b.x, b.y - front_ext, z)
        edges += [cq.Edge.makeLine(a, a2), cq.Edge.makeLine(a2, b2), cq.Edge.makeLine(b2, b)]
    else:
        edges.append(cq.Edge.makeLine(pts[-1], pts[0]))
    return cq.Wire.assembleEdges(edges)


def build_dome():
    zo = list(np.linspace(0.2, 0.985, 26))
    outer = cq.Solid.makeLoft([d_wire(z, 0) for z in zo], False)
    zi = [z for z in np.linspace(0.19, 0.97, 30) if section(z)[1] - SHELL_T > 2.5 and section(z)[2] - SHELL_T > 2.5]
    inner = cq.Solid.makeLoft([d_wire(z, SHELL_T, front_ext=2.0) for z in zi], False)
    dome = cq.Workplane("XY").add(outer).cut(cq.Workplane("XY").add(inner))

    # cadre avant (toute la silhouette), percé de l'ouverture et de la fenêtre ajourée
    left = np.stack([X(xl_s), Z(zs_s)], 1)
    right = np.stack([X(xr_s), Z(zs_s)], 1)
    outline = resample(np.concatenate([left, right[::-1]]), 1.2)
    frame = front_prism(outline, Y_FRONT - 7.0, Y_FRONT + 2.0)
    try:
        frame = frame.faces("<Y").edges().fillet(2.5)
    except Exception:
        pass
    dome = dome.union(frame)

    # aile épaisse : bloc derrière la fenêtre, avec cavité pour le ruban LED
    win_big = poly_offset(window, 3.0)
    wing = front_prism(win_big, Y_FRONT, Y_FRONT + 14.0)
    dome = dome.union(wing)

    # ouverture de la niche
    dome = dome.cut(front_prism(opening, Y_FRONT - 20, Y_FRONT + 3.0))
    # fenêtre : passage avant (panneau ajouré) puis feuillure de 1 mm, puis cavité LED
    win_small = poly_offset(window, -1.0)
    dome = dome.cut(front_prism(window, Y_FRONT - 20, Y_FRONT - 3.0))
    cav = np.concatenate([win_small, [[win_small[:, 0].min(), BASE_TOP - 5]]])
    cav_low = front_prism(np.array([[WING_HOLE[0] - 6, BASE_TOP - 5], [WING_HOLE[0] + 6, BASE_TOP - 5],
                                    [WING_HOLE[0] + 6, BASE_TOP + 15], [WING_HOLE[0] - 6, BASE_TOP + 15]]),
                          Y_FRONT - 3.0, Y_FRONT + 12.0)
    dome = dome.cut(front_prism(win_small, Y_FRONT - 3.5, Y_FRONT + 12.0)).cut(cav_low)

    # pattes de fixation (inserts M3 par-dessous)
    for (x, y) in DOME_SCREWS:
        dome = dome.union(cq.Workplane("XY").workplane(offset=BASE_TOP).center(x, y).circle(4.5).extrude(8))
        dome = dome.cut(cq.Workplane("XY").workplane(offset=BASE_TOP - 1).center(x, y).circle(INSERT_D / 2).extrude(INSERT_L + 1))

    # bossage au plafond pour le tube laiton de la sphère
    z_ceil = sph_z
    for zn in np.linspace(sph_z / H, 0.99, 400):
        xc, w, d = section(zn)
        w, d = w - SHELL_T, d - SHELL_T
        if w <= 0 or d <= 0 or ((sph_x - xc) / w) ** 2 + ((sph_y - Y_FRONT) / d) ** 2 > 1:
            break
        z_ceil = Z(zn)
    boss = (cq.Workplane("XY").workplane(offset=z_ceil - 12).center(sph_x, sph_y).circle(5.5).extrude(20)
            .intersect(cq.Workplane("XY").add(cq.Solid.makeLoft([d_wire(z, 0) for z in np.linspace(0.2, 0.985, 26)], False))))
    dome = dome.union(boss)
    dome = dome.cut(cq.Workplane("XY").workplane(offset=z_ceil - 13).center(sph_x, sph_y).circle((BRASS_D + 0.1) / 2).extrude(10))

    # tout ce qui dépasse sous le dessus de la base est coupé
    dome = dome.cut(cq.Workplane("XY").box(400, 400, 100).translate((0, 0, BASE_TOP - 50)))
    return dome, z_ceil


# ============================================================== 2. PANNEAU AJOURÉ (jali, à imprimer en or)
def star(cx, cz, r, k=0.62):
    return [(cx + (r if i % 2 == 0 else r * k) * math.cos(i * math.pi / 8),
             cz + (r if i % 2 == 0 else r * k) * math.sin(i * math.pi / 8)) for i in range(16)]


def inside(P, poly):
    x1, y1 = poly[:, 0], poly[:, 1]; x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
    x, y = P[:, 0:1], P[:, 1:2]
    return (((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)).sum(1) % 2 == 1


def build_jali():
    panel_poly = poly_offset(window, -FIT)
    keep = poly_offset(window, -2.0)
    jali = front_prism(panel_poly, Y_FRONT - 5.0, Y_FRONT - 3.0)
    S, RS, RD = 6.4, 2.55, 1.15
    cut = None
    for gx in np.arange(window[:, 0].min() - S, window[:, 0].max() + S, S):
        for gz in np.arange(window[:, 1].min() - S, window[:, 1].max() + S, S):
            for shape in (star(gx, gz, RS), [(gx + S / 2 + RD * math.cos(i * math.pi / 2), gz + S / 2 + RD * math.sin(i * math.pi / 2)) for i in range(4)]):
                if inside(np.array(shape), keep).all():
                    p = front_prism(np.array(shape), Y_FRONT - 6, Y_FRONT - 2)
                    cut = p if cut is None else cut.union(p)
    return jali.cut(cut)


# ============================================================== 3. COQUE DE LA BASE
def ellipse_y(x, a, b):
    return b * math.sqrt(max(0.0, 1 - (x / a) ** 2))


def facet_normal_point(x, z):
    """Point et normale sortante sur la paroi courbe (pour la molette)."""
    k = 1 - (1 - BASE_TAPER) * (z - PLATE_T) / (BASE_TOP - PLATE_T)
    a, b = BASE_A * k, BASE_B * k
    y = -ellipse_y(x, a, b)
    n = np.array([x / a ** 2, y / b ** 2]); n /= np.linalg.norm(n)
    return np.array([x, y]), n


KNOB_X, KNOB_Z = 46.0, 23.0
SCR_X, SCR_Z = 0.0, 23.0
SCREEN_BOSSES = [(-32.0, SCR_Z), (32.0, SCR_Z)]
PLATE_SCREWS = [(-57, -42), (57, -42), (-57, 42), (57, 42)]
ESP_POS = (18.0, 30.0)          # centre carte, axe long selon Y, USB vers l'arrière
AMP_POS = (-46.0, 4.0)
SD_POS = (-20.0, 38.0)          # axe long selon Y, fente carte vers l'arrière
SPK_POS = (-8.0, -26.0)
PED_POS = (sph_x, sph_y)


def base_solid(inset=0.0):
    h = BASE_TOP - PLATE_T
    bot = cq.Workplane("XY").workplane(offset=PLATE_T).ellipse(BASE_A - inset, BASE_B - inset)
    return bot.workplane(offset=h).ellipse(BASE_A * BASE_TAPER - inset, BASE_B * BASE_TAPER - inset).loft()


def build_base():
    body = base_solid()
    body = body.cut(cq.Workplane("XY").box(300, 50, 100).translate((0, FACET_Y - 25, 50)))   # face plate écran
    try:
        body = body.faces(">Z").edges().fillet(TOP_FILLET)
    except Exception:
        pass
    cavity = base_solid(WALL).cut(cq.Workplane("XY").box(300, 50, 100).translate((0, FACET_Y + WALL - 25 + 0.5, 50)))
    cavity = cavity.cut(cq.Workplane("XY").box(400, 400, 50).translate((0, 0, BASE_TOP - WALL + 25)))
    cavity = cavity.union(cq.Workplane("XY").box(400, 400, 2).translate((0, 0, PLATE_T)))  # ouverte en bas
    shell = body.cut(cavity)

    # --- face avant : logement du cadre noir (1,2 mm), fenêtre écran chanfreinée, renfort intérieur
    shell = shell.union(cq.Workplane("XZ", origin=(0, FACET_Y + WALL - 0.01, 0)).center(SCR_X, SCR_Z)
                        .rect(70, 30).extrude(-0.6))                                        # renfort -> paroi 3,1 mm
    pocket = cq.Workplane("XZ", origin=(0, FACET_Y - 1, 0)).center(SCR_X, SCR_Z).rect(64 + FIT * 2, 26 + FIT * 2).extrude(-2.2)
    shell = shell.cut(pocket)
    shell = shell.cut(cq.Workplane("XZ", origin=(0, FACET_Y - 5, 0)).center(SCR_X, SCR_Z)
                      .rect(*SCR_ACTIVE).extrude(-15))
    for (x, z) in SCREEN_BOSSES:                                                            # inserts support écran
        b = (cq.Workplane("XZ", origin=(0, FACET_Y + WALL, 0)).center(x, z).circle(4.0).extrude(-9)
             .faces(">Y").workplane().hole(INSERT_D, INSERT_L))
        shell = shell.union(b)

    # --- molette EC11 : lamage plat Ø18 + trou du canon
    p, n = facet_normal_point(KNOB_X, KNOB_Z)
    ax = cq.Vector(float(n[0]), float(n[1]), 0)
    org = cq.Vector(float(p[0]), float(p[1]), KNOB_Z)
    plane = cq.Plane(origin=org - ax * 0.6, xDir=cq.Vector(0, 0, 1), normal=ax)
    shell = shell.cut(cq.Workplane(plane).circle(9.0).extrude(10))
    shell = shell.cut(cq.Workplane(plane).circle(ENC_HOLE / 2).extrude(-10))

    # --- arrière : accès USB-C (les 2 ports de la carte) et fente microSD
    yb = ellipse_y(ESP_POS[0], BASE_A, BASE_B)
    shell = shell.cut(cq.Workplane("XY").box(26, 20, 2 * (PLATE_T + ESP_POST_H + 5)).translate((ESP_POS[0], yb, PLATE_T)))
    ys = ellipse_y(SD_POS[0], BASE_A, BASE_B)
    shell = shell.cut(cq.Workplane("XY").box(16, 20, 5).translate((SD_POS[0], ys, PLATE_T + 4 + 1.6 + 1.5)))

    # --- dessus : passages et vis de la niche
    for (x, y) in DOME_SCREWS:
        shell = shell.cut(cq.Workplane("XY").center(x, y).circle(CLEAR_D / 2).extrude(100))
    shell = shell.cut(cq.Workplane("XY").center(*WING_HOLE).circle(5.5).extrude(100))       # câbles cavité LED
    shell = shell.cut(cq.Workplane("XY").center(*PED_POS).circle(8.5).extrude(100))         # LED sous la sphère
    shell = shell.cut(cq.Workplane("XY").center(PED_POS[0] + 30, PED_POS[1]).circle(1.6).extrude(100))  # pions socle
    shell = shell.cut(cq.Workplane("XY").center(PED_POS[0] - 30, PED_POS[1]).circle(1.6).extrude(100))

    # --- colonnes pour les vis du fond
    for (x, y) in PLATE_SCREWS:
        shell = shell.union(insert_boss(x, y, BASE_TOP - WALL + 0.5, BASE_TOP - WALL - PLATE_T + 0.5, d=8.5))
    return shell


# ============================================================== 4. FOND DÉMONTABLE (porte l'électronique)
def build_plate():
    plate = cq.Workplane("XY").ellipse(BASE_A, BASE_B).extrude(PLATE_T)
    # bourrelet de centrage dans la coque
    ring = (cq.Workplane("XY").workplane(offset=PLATE_T).ellipse(BASE_A - WALL - FIT, BASE_B - WALL - FIT).extrude(2.0)
            .cut(cq.Workplane("XY").workplane(offset=PLATE_T).ellipse(BASE_A - WALL - 2.0, BASE_B - WALL - 2.0).extrude(2.0)))
    plate = plate.union(ring)
    plate = plate.cut(cq.Workplane("XY").box(300, 50, 20).translate((0, FACET_Y + WALL - 25 + 2.0, 10)).intersect(ring))
    for (x, y) in PLATE_SCREWS:                                   # dégagement autour des colonnes
        plate = plate.cut(cq.Workplane("XY").workplane(offset=PLATE_T).center(x, y).circle(5.5).extrude(2.0))

    # vis fraisées M3 vers les colonnes de la coque
    for (x, y) in PLATE_SCREWS:
        plate = plate.cut(cq.Workplane("XY").center(x, y).circle(CLEAR_D / 2).extrude(PLATE_T))
        plate = plate.cut(cq.Workplane("XY").center(x, y).circle(3.2).workplane(offset=1.4).circle(1.7).loft())
    # emplacements des patins silicone Ø10
    for (x, y) in ((-55, -35), (55, -35), (-55, 35), (55, 35)):
        plate = plate.cut(cq.Workplane("XY").center(x, y).circle(5.2).extrude(0.6))

    # haut-parleur : grille + logement + 3 colonnes de bride
    sx, sy = SPK_POS
    holes = cq.Workplane("XY")
    for i in range(-6, 7):
        for j in range(-6, 7):
            hx, hy = sx + i * 4.2 + (j % 2) * 2.1, sy + j * 3.64
            if math.hypot(hx - sx, hy - sy) < SPK_D / 2 - 5:
                holes = holes.union(cq.Workplane("XY").center(hx, hy).polygon(6, 3.2).extrude(PLATE_T))
    plate = plate.cut(holes)
    plate = plate.union(cq.Workplane("XY").workplane(offset=PLATE_T).center(sx, sy).circle(SPK_D / 2 + 2.5).extrude(SPK_FLANGE)
                        .cut(cq.Workplane("XY").workplane(offset=PLATE_T).center(sx, sy).circle(SPK_D / 2 + FIT * 2).extrude(SPK_FLANGE)))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        plate = plate.union(insert_boss(sx + (SPK_D / 2 + 6) * math.cos(a), sy + (SPK_D / 2 + 6) * math.sin(a),
                                        PLATE_T + SPK_FLANGE, SPK_FLANGE, d=8).mirror("XY", basePointVector=(0, 0, (PLATE_T * 2 + SPK_FLANGE) / 2)))

    # ESP32 : 4 plots aux extrémités (sans broches), murets de guidage, 2 inserts pour la barrette
    ex, ey = ESP_POS
    for dx in (-ESP_W / 2 + 3, ESP_W / 2 - 3):
        for dy in (-ESP_L / 2 + 3, ESP_L / 2 - 3):
            plate = plate.union(cq.Workplane("XY").workplane(offset=PLATE_T).center(ex + dx, ey + dy).rect(4, 4).extrude(ESP_POST_H))
    for side in (-1, 1):
        plate = plate.union(cq.Workplane("XY").workplane(offset=PLATE_T).center(ex + side * (ESP_W / 2 + FIT + 1), ey - 5)
                            .rect(2, ESP_L - 20).extrude(ESP_POST_H + 3))
        plate = plate.union(insert_boss(ex + side * (ESP_W / 2 + 6), ey - ESP_L / 2 + 8, PLATE_T + 14, 14, d=7)
                            .mirror("XY", basePointVector=(0, 0, PLATE_T + 7)))

    # MAX98357A et module microSD : bacs à murets (emboîtement serré)
    for (cx, cy), (L, W), h in ((AMP_POS, (AMP_L, AMP_W), 4), (SD_POS, (SD_W, SD_L), 4)):
        tray = (cq.Workplane("XY").workplane(offset=PLATE_T).center(cx, cy).rect(L + 2 * FIT + 3, W + 2 * FIT + 3).extrude(h)
                .cut(cq.Workplane("XY").workplane(offset=PLATE_T).center(cx, cy).rect(L + 2 * FIT, W + 2 * FIT).extrude(h))
                .cut(cq.Workplane("XY").workplane(offset=PLATE_T).center(cx, cy).rect(L - 6, W + 10).extrude(h)))
        plate = plate.union(tray)
    return plate


def build_esp_strap():
    L = ESP_W + 12 + 8
    s = cq.Workplane("XY").rect(L, 8).extrude(3).edges("|Z").fillet(2)
    s = s.faces(">Z").workplane().pushPoints([(-(ESP_W / 2 + 6), 0), (ESP_W / 2 + 6, 0)]).hole(CLEAR_D)
    return s.union(cq.Workplane("XY").rect(ESP_W - 8, 8).extrude(-1.5))


def build_speaker_ring():
    r = cq.Workplane("XY").circle(SPK_D / 2 + 2).circle(SPK_D / 2 - 4).extrude(2.5)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        x, y = (SPK_D / 2 + 6) * math.cos(a), (SPK_D / 2 + 6) * math.sin(a)
        r = r.union(cq.Workplane("XY").center(x, y).circle(5).extrude(2.5)
                    .union(cq.Workplane("XY").center(x / 2, y / 2).rect(8, 8).extrude(2.5).rotate((0, 0, 0), (0, 0, 1), 0)))
        r = r.cut(cq.Workplane("XY").center(x, y).circle(CLEAR_D / 2).extrude(3))
    return r.cut(cq.Workplane("XY").circle(SPK_D / 2 - 4).extrude(3))


# ============================================================== 5. PETITES PIÈCES
def build_bezel():
    """Cadre noir de la face avant : fenêtre écran + pictogrammes tactiles gravés."""
    b = cq.Workplane("XY").rect(64, 26).extrude(1.2).edges("|Z").fillet(3)
    b = b.cut(cq.Workplane("XY").rect(*SCR_ACTIVE).extrude(1.2))
    b = b.faces(">Z").edges("not(<X or >X or <Y or >Y)").chamfer(0.6) if False else b
    for sx_, flip in ((-26.5, -1), (26.5, 1)):
        tri = [(sx_ + flip * 2.2, 0), (sx_ - flip * 1.8, 2.6), (sx_ - flip * 1.8, -2.6)]
        bar = cq.Workplane("XY").center(sx_ + flip * 2.9, 0).rect(0.9, 5.2).extrude(0.5).translate((0, 0, 0.7))
        b = b.cut(cq.Workplane("XY").polyline(tri).close().extrude(0.5).translate((0, 0, 0.7))).cut(bar)
    return b


def build_screen_bracket():
    W, Hh = 72.0, 30.0
    br = cq.Workplane("XY").rect(W, Hh).extrude(3.0)
    br = br.union(cq.Workplane("XY").rect(SCR_PCB[0] + 2 * 2.5, SCR_PCB[1] + 2 * 2.5).extrude(-SCR_PCB[2]))
    br = br.cut(cq.Workplane("XY").rect(SCR_PCB[0] + 2 * FIT, SCR_PCB[1] + 2 * FIT).extrude(-SCR_PCB[2]))
    br = br.cut(cq.Workplane("XY").center(0, -SCR_PCB[1] / 2).rect(20, 8).extrude(5, both=True))  # nappe / fils
    br = br.faces(">Z").workplane().pushPoints([(-32, 0), (32, 0)]).hole(CLEAR_D)
    return br


def build_knob():
    """Molette Ø24 cannelée pour axe EC11 en D ; la jupe cache l'écrou du canon."""
    k = cq.Workplane("XY").circle(12).extrude(14).faces(">Z").edges().fillet(1.5)
    flutes = None
    for i in range(48):
        a = 2 * math.pi * i / 48
        f = cq.Workplane("XY").center(12 * math.cos(a), 12 * math.sin(a)).circle(0.55).extrude(9).translate((0, 0, 2.5))
        flutes = f if flutes is None else flutes.union(f)
    k = k.cut(flutes)
    k = k.cut(cq.Workplane("XY").circle(9.5).extrude(5))                              # jupe : cache l'écrou
    shaft = cq.Workplane("XY").circle((SHAFT_D + 0.15) / 2).extrude(12).translate((0, 0, 1))
    flat = cq.Workplane("XY").center(SHAFT_FLAT + 0.1 - SHAFT_D / 2 + 5, 0).rect(10, 10).extrude(12).translate((0, 0, 1))
    return k.cut(shaft.cut(flat))


def build_pedestal():
    p = cq.Workplane("XY").circle(36).extrude(4).faces(">Z").edges().fillet(1.2)
    p = p.cut(cq.Workplane("XY").workplane(offset=3.2).circle(31).extrude(1))      # creux pour le disque décoré
    p = p.cut(cq.Workplane("XY").circle(8.2).extrude(4))                             # fenêtre lumière
    p = p.cut(cq.Workplane("XY").workplane(offset=2.2).circle(9.5).extrude(2))      # feuillure diffuseur
    for x in (30, -30):
        p = p.union(cq.Workplane("XY").center(x, 0).circle(1.45).extrude(-5))       # pions de centrage
    return p


def build_diffuser():
    return cq.Workplane("XY").circle(9.5 - FIT).extrude(1.0)


def build_sphere():
    """Deux demi-sphères translucides, motif d'étoiles en épaisseur (effet lithophanie)."""
    R, T, T_THIN = SPH_R, 1.6, 0.6
    ball = cq.Workplane("XY").sphere(R)
    shell = ball.cut(cq.Workplane("XY").sphere(R - T))
    cutters = None
    for ring, (lat, n) in enumerate(((-35, 10), (-12, 14), (12, 14), (35, 10), (56, 6))):
        for i in range(n):
            lon = 360 * i / n + (ring % 2) * 180 / n
            s = (cq.Workplane("XY").polyline(star(0, 0, 4.2 if abs(lat) < 40 else 3.4)).close().extrude(R + 2)
                 .rotate((0, 0, 0), (0, 1, 0), 90 - lat).rotate((0, 0, 0), (0, 0, 1), lon))
            cutters = s if cutters is None else cutters.union(s)
    shell = shell.cut(cutters.intersect(cq.Workplane("XY").sphere(R - T_THIN)))
    shell = shell.cut(cq.Workplane("XY").circle(10).extrude(-R - 1))               # ouverture basse (lumière)
    top = (cq.Workplane("XY").workplane(offset=R - 8).circle(6).extrude(8).intersect(ball)
           .cut(cq.Workplane("XY").workplane(offset=R - 9).circle((BRASS_D + 0.1) / 2).extrude(10)))
    shell = shell.union(top)
    upper = shell.intersect(cq.Workplane("XY").box(80, 80, 40).translate((0, 0, 20)))
    lower = shell.intersect(cq.Workplane("XY").box(80, 80, 40).translate((0, 0, -20)))
    lip = (cq.Workplane("XY").circle(R - T + 0.01).circle(R - T - 1.2).extrude(3))   # emboîtement
    lower = lower.union(lip)
    upper = upper.cut(cq.Workplane("XY").circle(R - T + FIT).circle(R - T - 1.4).extrude(3.2))
    return upper, lower


# ============================================================== EXPORT
if __name__ == "__main__":
    dome, z_ceil = build_dome()
    export(dome, "01_niche_coque")
    export(build_jali(), "02_panneau_ajoure_OR")
    export(build_base(), "03_base_coque")
    export(build_plate(), "04_fond_electronique")
    export(build_speaker_ring(), "05_bride_haut_parleur")
    export(build_esp_strap(), "06_barrette_esp32")
    export(build_screen_bracket(), "07_support_ecran")
    export(build_bezel(), "08_cadre_ecran_NOIR")
    export(build_knob(), "09_molette_OR")
    export(build_pedestal(), "10_socle_OR")
    export(build_diffuser(), "11_diffuseur_BLANC")
    up, lo = build_sphere()
    export(up, "12_sphere_haut_BLANC")
    export(lo, "13_sphere_bas_BLANC")
    print(f"Tube laiton : longueur ≈ {z_ceil - 13 + 10 - (sph_z + SPH_R - 8) + 8:.0f} mm "
          f"(plafond z={z_ceil:.1f}, sphère z={sph_z:.1f})")
