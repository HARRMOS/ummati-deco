"""
AYAH « Radio » by INOMA — pièces imprimables (CadQuery + Shapely).
    ../.venv-cad/bin/python ayah_radio.py        -> stl/  step/

Repère : x = largeur (gauche -> droite), z = hauteur, y = profondeur (0 = face avant, D = dos).
Cotes en mm. Les cotes « À VÉRIFIER » dépendent des composants achetés.
"""
import math, os
import numpy as np
import cadquery as cq
from shapely.geometry import Point, Polygon, MultiPolygon, box, LineString
from shapely.ops import unary_union
from shapely import affinity
from shapely.geometry.polygon import orient

OUT = os.path.dirname(os.path.abspath(__file__))
for d in ("stl", "step"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

# ============================================================== PARAMÈTRES
W, R_TOP, Z_BOT, Z_SPRING = 170.0, 85.0, 6.0, 65.0      # largeur, rayon de l'arche, bas du corps, naissance de l'arche
D = 72.0                                                 # profondeur
WALL, FRONT_T = 2.4, 3.0
CORNER = 10.0                                            # arrondi des coins bas
FIT = 0.15

O_R, O_BOT = 68.0, 56.0                                  # ouverture de la grille
FLANGE = 4.0                                             # rebord de la grille derrière la façade
BAFFLE_Y = 12.0                                          # face avant du baffle (porte HP)
BAFFLE_T = 2.5

INSERT_D, INSERT_L, CLEAR_D = 4.0, 6.0, 3.4              # inserts M3
PILOT_D = 2.0                                            # vis à plastique Ø2,2 (petites pièces)

# --- composants (À VÉRIFIER)
SPK_D, SPK_T = 40.0, 2.0                                 # 2 × haut-parleurs Ø40, épaisseur du rebord
SPK_POS = [(-46.0, 92.0), (46.0, 92.0)]
CALLI_PNG = os.path.join(OUT, "calligraphie", "texte.png")   # « القرآن الكريم » (Diwan Thuluth, rendu par Chrome)
CALLI_BOX, CALLI_C = (40.0, 21.0), (0.0, 79.0)
PLAQUE_FACE = 1.2                                        # retrait de la plaque derrière la façade
LETTER_H = 1.0                                           # relief des lettres
ESP_L, ESP_W, ESP_POST = 64.0, 28.5, 5.0                 # ESP32-S3 DevKitC
AMP_L, AMP_W = 19.5, 18.5                                # MAX98357A
SD_L, SD_W = 42.0, 24.5                                  # module microSD
USBC_CUT, USBC_EARS = (12.5, 6.5), 28.0                  # prise USB-C de façade (rallonge à visser)
ENC_HOLE, SHAFT_D, SHAFT_FLAT = 7.3, 6.0, 4.5            # EC11

BAND_Z = 28.0
TOUCH = [(-48.0, 16.0, "prev"), (-18.0, 22.0, "play"), (12.0, 16.0, "next")]
KNOB_X, KNOB_D = 56.0, 30.0

# ============================================================== GÉOMÉTRIE 2D (vue de face, coordonnées x, z)
Q = 24  # résolution des arcs


def arch(half_w, z_bot, z_spring, r):
    a = box(-half_w, z_bot, half_w, z_spring).union(Point(0, z_spring).buffer(r, quad_segs=Q))
    return a.intersection(box(-500, z_bot, 500, 500))


PROFILE = arch(W / 2, Z_BOT, Z_SPRING, R_TOP).buffer(-CORNER, quad_segs=Q).buffer(CORNER, quad_segs=Q)
INNER = PROFILE.buffer(-WALL, quad_segs=Q)
OPEN = arch(O_R, O_BOT, Z_SPRING, O_R).buffer(-3, quad_segs=Q).buffer(3, quad_segs=Q)
H_TOTAL = Z_SPRING + R_TOP


def catmull(pts, n=12):
    P = [np.array(p, float) for p in pts]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1:i + 3]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


# cartouche en forme de mihrab (bas rectangulaire = calligraphie, haut en bulbe = coupole)
_half = catmull([(23, 66), (23, 92), (26, 100), (21, 109), (11, 115.5), (0, 122)])
CARTOUCHE = Polygon(_half + [(-x, z) for x, z in reversed(_half[:-1])])


def polar(r, deg, c=(0, Z_SPRING)):
    return (c[0] + r * math.cos(math.radians(deg)), c[1] + r * math.sin(math.radians(deg)))


BAFFLE_BOSSES = [(-78.5, 60.0), (78.5, 60.0), polar(78.5, 140), polar(78.5, 40)]
BACK_COLUMNS = [(-74.0, 16.0), (74.0, 16.0), polar(78.5, 105), polar(78.5, 75)]


# ============================================================== 2D -> 3D
def _faces(geom):
    polys = [geom] if isinstance(geom, Polygon) else list(getattr(geom, "geoms", []))
    for p in polys:
        if p.is_empty or p.area < 1e-3:
            continue
        p = orient(p.simplify(0.02).buffer(0), 1.0)
        if p.geom_type != "Polygon":
            yield from _faces(p)
            continue
        outer = cq.Wire.makePolygon([cq.Vector(x, z, 0) for x, z in p.exterior.coords[:-1]], close=True)
        holes = [cq.Wire.makePolygon([cq.Vector(x, z, 0) for x, z in r.coords[:-1]], close=True) for r in p.interiors]
        f = cq.Face.makeFromWires(outer, holes)
        yield f if f.isValid() else f.fix()


def front(geom, y0, y1):
    """Extrude une forme 2D (x, z) entre les profondeurs y0 < y1."""
    sols = [cq.Solid.extrudeLinear(f, cq.Vector(0, 0, y1 - y0)) for f in _faces(geom)]
    wp = cq.Workplane("XY").add(cq.Compound.makeCompound(sols)) if len(sols) > 1 else cq.Workplane("XY").add(sols[0])
    if len(sols) > 1:
        wp = cq.Workplane("XY").add(sols[0])
        for s in sols[1:]:
            wp = wp.union(cq.Workplane("XY").add(s))
    # local (x, z_local=hauteur, e=extrusion) -> monde (x, y, z) : y = y0 + e, z = hauteur
    return wp.rotate((0, 0, 0), (1, 0, 0), 90).mirror("XZ").translate((0, y0, 0))


def col_y(x, z, d, y0, y1):
    """Colonne parallèle à Y."""
    return front(Point(x, z).buffer(d / 2, quad_segs=16), y0, y1)


def hole_y(x, z, d, y0, y1):
    return col_y(x, z, d, y0, y1)


def export(shape, name):
    v = shape.val() if isinstance(shape, cq.Workplane) else shape
    bb = v.BoundingBox()
    print(f"{name:26s} valide={v.isValid()}  {bb.xlen:6.1f} × {bb.ylen:5.1f} × {bb.zlen:6.1f} mm", flush=True)
    cq.exporters.export(v, os.path.join(OUT, "stl", name + ".stl"), tolerance=0.03, angularTolerance=0.1)
    cq.exporters.export(v, os.path.join(OUT, "step", name + ".step"))


# ============================================================== 1. CORPS
def build_body():
    body = front(PROFILE, 0, D)
    try:
        body = body.faces("<Y").edges().fillet(4.0)
    except Exception:
        body = body.faces("<Y").edges().chamfer(1.5)
    body = body.cut(front(INNER, FRONT_T, D + 1))
    body = body.cut(front(OPEN, -1, FRONT_T + 1))                                     # ouverture grille

    # bandeau : touches tactiles, molette, arc gravé autour de la molette
    for x, d, _ in TOUCH:
        body = body.cut(hole_y(x, BAND_Z, d + 2 * FIT, -1, FRONT_T + 1))
    body = body.cut(hole_y(KNOB_X, BAND_Z, ENC_HOLE, -1, FRONT_T + 1))
    arc = LineString([(KNOB_X + 19.5 * math.cos(math.radians(a)), BAND_Z + 19.5 * math.sin(math.radians(a)))
                      for a in np.linspace(-40, 220, 80)]).buffer(0.5, quad_segs=8)
    body = body.cut(front(arc, -1, 0.6))

    # colonnes : baffle (inserts côté arrière) et dos (pleine profondeur)
    for x, z in BAFFLE_BOSSES:
        body = body.union(col_y(x, z, 9, FRONT_T - 0.5, BAFFLE_Y))
        body = body.cut(hole_y(x, z, INSERT_D, BAFFLE_Y - INSERT_L, BAFFLE_Y + 0.1))
    for x, z in BACK_COLUMNS:
        body = body.union(col_y(x, z, 9, FRONT_T - 0.5, D - 3.0))
        body = body.cut(hole_y(x, z, INSERT_D, D - 3.0 - INSERT_L, D))
    # on recoupe ce qui dépasserait du profil extérieur
    body = body.intersect(front(PROFILE, -1, D + 1).union(front(PROFILE.buffer(-0.01), 0, D)))

    # plancher : 2 vis vers le socle doré
    for x in (-45, 45):
        body = body.cut(cq.Workplane("XY").center(x, D / 2).circle(CLEAR_D / 2).extrude(Z_BOT + WALL + 1))
    return body


# ============================================================== 2. GRILLE DORÉE (treillis + cartouche)
def lattice(region, S=15.0, bar=1.7):
    a = 0.42 * S
    lines = []
    xs = np.arange(-O_R - S, O_R + S, S)
    zs = np.arange(O_BOT - S, Z_SPRING + O_R + S, S)
    for i, x in enumerate(xs):
        for z in zs:
            for rot in (0, 45):
                sq = affinity.rotate(box(x - a, z - a, x + a, z + a), rot, origin=(x, z))
                lines.append(sq.exterior)
    bars = unary_union([l.buffer(bar / 2, quad_segs=4, join_style=2) for l in lines])
    return bars.intersection(region)


def build_grille():
    G = OPEN.buffer(-FIT, quad_segs=Q)
    inner = G.buffer(-2.5, quad_segs=Q)
    cart_frame = CARTOUCHE.buffer(3.0, quad_segs=Q)
    face = unary_union([G.difference(inner),
                        lattice(inner.difference(cart_frame)),
                        cart_frame.difference(CARTOUCHE)])
    grille = front(face, 0, FRONT_T)
    flange = OPEN.buffer(FLANGE, quad_segs=Q).difference(inner)
    grille = grille.union(front(flange, FRONT_T, FRONT_T + 1.5))
    return grille


def ornament():
    """Petite coupole et deux minarets dans le bulbe du cartouche."""
    dome = Point(0, 101).buffer(6.5, quad_segs=Q).intersection(box(-7, 101, 7, 120))
    finial = box(-0.45, 107, 0.45, 111.5).union(Point(0, 112).buffer(0.9))
    base = box(-14, 99.6, 14, 101)
    mins = []
    for sx in (-1, 1):
        x = sx * 11.5
        mins.append(Polygon([(x - 0.9, 101), (x + 0.9, 101), (x + 0.9, 108), (x, 110.5), (x - 0.9, 108)]))
    return unary_union([dome, finial, base] + mins)


def build_plaque():
    """Plaque du cartouche (sombre) + calligraphie et coupole en relief.
    À imprimer face vers le haut, avec changement de filament (OR) à la hauteur du relief."""
    from arabic_text import trace_png
    text = trace_png(CALLI_PNG, width=CALLI_BOX[0], height=CALLI_BOX[1], center=CALLI_C, thicken=0.08)
    relief = unary_union([text, ornament()]).intersection(CARTOUCHE.buffer(-1.5, quad_segs=Q))
    plaque = front(CARTOUCHE.buffer(-FIT, quad_segs=Q), PLAQUE_FACE, FRONT_T)
    plaque = plaque.union(front(CARTOUCHE.buffer(2.5, quad_segs=Q), FRONT_T, FRONT_T + 1.5))
    return plaque.union(front(relief, PLAQUE_FACE - LETTER_H, PLAQUE_FACE + 0.01))


# ============================================================== 3. BAFFLE (porte HP, plaque l'écran et la grille)
def build_baffle():
    plate2d = OPEN.buffer(5, quad_segs=Q).union(unary_union([Point(x, z).buffer(4.5) for x, z in BAFFLE_BOSSES]).buffer(2).buffer(-2))
    plate2d = unary_union([plate2d] + [LineString([(x, z), polar(70, math.degrees(math.atan2(z - Z_SPRING, x)))]).buffer(4)
                                       for x, z in BAFFLE_BOSSES])
    for x, z in SPK_POS:
        plate2d = plate2d.difference(Point(x, z).buffer(SPK_D / 2 - 3, quad_segs=Q))
    for x, z in BAFFLE_BOSSES:
        plate2d = plate2d.difference(Point(x, z).buffer(CLEAR_D / 2))
    baffle = front(plate2d, BAFFLE_Y, BAFFLE_Y + BAFFLE_T)
    # rebord qui plaque la grille contre la façade
    baffle = baffle.union(front(OPEN.buffer(5, quad_segs=Q).difference(OPEN.buffer(3, quad_segs=Q)), FRONT_T + 1.5, BAFFLE_Y))
    # rebord qui plaque la plaque calligraphiée contre le cadre du cartouche
    baffle = baffle.union(front(CARTOUCHE.buffer(2.5, quad_segs=Q).difference(CARTOUCHE.buffer(0.5, quad_segs=Q)),
                                FRONT_T + 1.5, BAFFLE_Y))
    # bossages des bagues de haut-parleur (vis à plastique)
    for x, z in SPK_POS:
        for k in range(3):
            bx, bz = x + 26 * math.cos(math.radians(90 + 120 * k)), z + 26 * math.sin(math.radians(90 + 120 * k))
            baffle = baffle.union(col_y(bx, bz, 7, BAFFLE_Y + BAFFLE_T - 0.1, BAFFLE_Y + BAFFLE_T + SPK_T + 3.5))
            baffle = baffle.cut(hole_y(bx, bz, PILOT_D, BAFFLE_Y + 1, BAFFLE_Y + 20))
    return baffle


def build_speaker_ring():
    """Bague qui plaque un HP Ø40 contre le baffle (3 vis à plastique Ø2,2)."""
    y0 = 0.0
    ring = cq.Workplane("XY").circle(SPK_D / 2 + 1).circle(16).extrude(2.0)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        x, y = 26 * math.cos(a), 26 * math.sin(a)
        ring = ring.union(cq.Workplane("XY").center(x, y).circle(4.5).extrude(2.0).translate((0, 0, 3.5)))
        ring = ring.union(cq.Workplane("XY").center((x * 0.85), (y * 0.85)).rect(7, 7).extrude(5.5)
                          .rotate((0, 0, 0), (0, 0, 1), 0))
        ring = ring.cut(cq.Workplane("XY").center(x, y).circle(1.3).extrude(10))
    return ring.cut(cq.Workplane("XY").circle(16).extrude(10))


# ============================================================== 4. DOS (porte l'électronique)
def build_back():
    p2d = INNER.buffer(-FIT, quad_segs=Q)
    for x, z in BACK_COLUMNS:
        p2d = p2d.difference(Point(x, z).buffer(CLEAR_D / 2))
    usb = box(-USBC_CUT[0] / 2, -USBC_CUT[1] / 2, USBC_CUT[0] / 2, USBC_CUT[1] / 2).buffer(-2).buffer(2)
    usb = affinity.translate(usb, 45, 22)
    p2d = p2d.difference(usb).difference(Point(45 - USBC_EARS / 2, 22).buffer(1.6)).difference(Point(45 + USBC_EARS / 2, 22).buffer(1.6))
    # grille d'aération discrète (motif de fentes)
    for i in range(-3, 4):
        p2d = p2d.difference(box(i * 8 - 1.2, 115, i * 8 + 1.2, 135).buffer(1.2))
    back = front(p2d, D - 3.0, D)
    for x, z in BACK_COLUMNS:                                                         # fraisages côté extérieur
        back = back.cut(cq.Workplane("XZ", origin=(0, D + 0.01, 0)).center(x, z).circle(3.1).workplane(offset=1.6).circle(1.7).loft())

    yin = D - 3.0                                                                      # face intérieure
    def tray(cx, cz, L, Wd, h=4.0):
        outer = box(cx - L / 2 - 1.5 - FIT, cz - Wd / 2 - 1.5 - FIT, cx + L / 2 + 1.5 + FIT, cz + Wd / 2 + 1.5 + FIT)
        inner = box(cx - L / 2 - FIT, cz - Wd / 2 - FIT, cx + L / 2 + FIT, cz + Wd / 2 + FIT)
        gaps = box(cx - L / 2 + 4, cz - 100, cx + L / 2 - 4, cz + 100)
        return front(outer.difference(inner).difference(gaps), yin - h, yin + 0.01)

    # ESP32 : 4 plots aux extrémités + guides + 2 bossages pour la barrette
    ex, ez = 0.0, 32.0
    posts = unary_union([box(ex + sx * (ESP_L / 2 - 4) - 2, ez + sz * (ESP_W / 2 - 3) - 2,
                             ex + sx * (ESP_L / 2 - 4) + 2, ez + sz * (ESP_W / 2 - 3) + 2) for sx in (-1, 1) for sz in (-1, 1)])
    back = back.union(front(posts, yin - ESP_POST, yin + 0.01))
    back = back.union(tray(ex, ez, ESP_L, ESP_W, h=ESP_POST + 2.5))
    for sz in (-1, 1):
        bx, bz = ex + ESP_L / 2 - 10, ez + sz * (ESP_W / 2 + 6)
        back = back.union(col_y(bx, bz, 7, yin - 14, yin + 0.01)).cut(hole_y(bx, bz, PILOT_D, yin - 15, yin - 2))
    back = back.union(tray(-50, 62, AMP_L, AMP_W))
    back = back.union(tray(48, 72, SD_W, SD_L))
    return back


def build_esp_strap():
    L = ESP_W + 12 + 8
    s = cq.Workplane("XY").rect(8, L).extrude(3).edges("|Z").fillet(2)
    s = s.faces(">Z").workplane().pushPoints([(0, -(ESP_W / 2 + 6)), (0, ESP_W / 2 + 6)]).hole(2.6)
    return s.union(cq.Workplane("XY").rect(8, ESP_W - 8).extrude(-1.5))


# ============================================================== 5. SOCLE, MOLETTE, TOUCHES
def build_plinth():
    plan = box(-W / 2 - 3, -3, W / 2 + 3, D + 3).buffer(-12, quad_segs=Q).buffer(12, quad_segs=Q)
    pts = [cq.Vector(x, y, 0) for x, y in plan.exterior.coords[:-1]]
    p = cq.Workplane("XY").add(cq.Solid.extrudeLinear(cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)), cq.Vector(0, 0, Z_BOT)))
    try:
        p = p.faces(">Z").edges().fillet(1.5)
    except Exception:
        pass
    for x in (-45, 45):
        p = p.cut(cq.Workplane("XY").workplane(offset=Z_BOT - INSERT_L).center(x, D / 2).circle(INSERT_D / 2).extrude(INSERT_L + 1))
    for x, y in ((-70, 8), (70, 8), (-70, D - 8), (70, D - 8)):
        p = p.cut(cq.Workplane("XY").center(x, y).circle(5.2).extrude(0.6))          # patins silicone
    return p


def build_knob():
    d = KNOB_D
    k = cq.Workplane("XY").circle(d / 2).extrude(16).faces(">Z").edges().fillet(1.5)
    flutes = None
    for i in range(60):
        a = 2 * math.pi * i / 60
        f = cq.Workplane("XY").center(d / 2 * math.cos(a), d / 2 * math.sin(a)).circle(0.6).extrude(7).translate((0, 0, 0))
        flutes = f if flutes is None else flutes.union(f)
    k = k.cut(flutes)                                                                  # moletage sur la partie arrière
    k = k.cut(cq.Workplane("XY").workplane(offset=15.6).circle(d / 2 - 3).extrude(1))  # face avant légèrement creusée
    k = k.cut(cq.Workplane("XY").circle(9.5).extrude(4))                              # jupe : cache l'écrou
    shaft = cq.Workplane("XY").circle((SHAFT_D + 0.15) / 2).extrude(13)
    flat = cq.Workplane("XY").center(SHAFT_FLAT + 0.1 - SHAFT_D / 2 + 5, 0).rect(10, 10).extrude(13)
    return k.cut(shaft.cut(flat))


def build_touch(d, kind):
    """Touche dorée fixe (tactile) : ruban cuivre collé dans la coupelle arrière."""
    cap = cq.Workplane("XY").circle(d / 2 + 2).extrude(2.5).faces(">Z").edges().fillet(1.0)
    cap = cap.union(cq.Workplane("XY").circle(d / 2).extrude(-FRONT_T))               # tenon dans la façade
    cap = cap.cut(cq.Workplane("XY").workplane(offset=-FRONT_T).circle(d / 2 - 1.6).extrude(FRONT_T + 1.3))  # coupelle cuivre
    s = d * 0.22
    if kind == "play":
        icon = [cq.Workplane("XY").polyline([(-s * 1.1, -s), (-s * 1.1, s), (s * 0.4, 0)]).close().extrude(0.6),
                cq.Workplane("XY").center(s * 0.75, 0).rect(s * 0.28, 2 * s).extrude(0.6),
                cq.Workplane("XY").center(s * 1.25, 0).rect(s * 0.28, 2 * s).extrude(0.6)]
    else:
        f = -1 if kind == "prev" else 1
        icon = [cq.Workplane("XY").polyline([(f * -s * 0.2, -s), (f * -s * 0.2, s), (f * s * 0.9, 0)]).close().extrude(0.6),
                cq.Workplane("XY").polyline([(f * -s * 1.2, -s), (f * -s * 1.2, s), (f * -s * 0.1, 0)]).close().extrude(0.6),
                cq.Workplane("XY").center(f * s * 1.05, 0).rect(s * 0.25, 2 * s).extrude(0.6)]
    for ic in icon:
        cap = cap.cut(ic.translate((0, 0, 2.5 - 0.6)))
    cap = cap.cut(cq.Workplane("XY").workplane(offset=-FRONT_T - 1).circle(0.9).extrude(FRONT_T + 2))  # passage du fil
    return cap


# ============================================================== EXPORT
if __name__ == "__main__":
    import sys
    only = set(sys.argv[1:])
    jobs = [
        ("01_corps", build_body),
        ("02_grille_OR", build_grille),
        ("03_plaque_calligraphie_NOIR+OR", build_plaque),
        ("04_baffle", build_baffle),
        ("05_bague_HP_x2", build_speaker_ring),
        ("06_dos_electronique", build_back),
        ("07_barrette_esp32", build_esp_strap),
        ("08_socle_OR", build_plinth),
        ("09_molette_OR", build_knob),
        ("10_touche_precedent_OR", lambda: build_touch(16.0, "prev")),
        ("11_touche_lecture_OR", lambda: build_touch(22.0, "play")),
        ("12_touche_suivant_OR", lambda: build_touch(16.0, "next")),
    ]
    for name, fn in jobs:
        if only and not any(o in name for o in only):
            continue
        export(fn(), name)
