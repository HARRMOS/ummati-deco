"""Calligraphie arabe -> polygones Shapely (mise en forme HarfBuzz + contours fontTools)."""
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity


class FlattenPen(BasePen):
    def __init__(self, glyphset, steps=10):
        super().__init__(glyphset)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def _glyph_geom(contours):
    polys = [Polygon(c).buffer(0) for c in contours if len(c) > 2]
    signed = [(p, Polygon(c).exterior.is_ccw) for p, c in zip(polys, contours) if not p.is_empty]
    if not signed:
        return None
    outer_ccw = max(signed, key=lambda t: t[0].area)[1]
    outers = unary_union([p for p, ccw in signed if ccw == outer_ccw])
    holes = unary_union([p for p, ccw in signed if ccw != outer_ccw])
    return outers.difference(holes)


def text_shape(text, font_path, font_index=0, width=None, height=None, center=(0, 0), thicken=0.0):
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob, font_index)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"liga": True, "calt": True})
    tt = TTFont(font_path, fontNumber=font_index)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    x = 0
    geoms = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = FlattenPen(gs)
        gs[order[info.codepoint]].draw(pen)
        g = _glyph_geom(pen.contours)
        if g is not None:
            geoms.append(affinity.translate(g, x + pos.x_offset, pos.y_offset))
        x += pos.x_advance
    shape = unary_union(geoms)
    minx, miny, maxx, maxy = shape.bounds
    s = min((width / (maxx - minx)) if width else 1e9, (height / (maxy - miny)) if height else 1e9)
    shape = affinity.scale(shape, s, s, origin=(0, 0))
    minx, miny, maxx, maxy = shape.bounds
    shape = affinity.translate(shape, center[0] - (minx + maxx) / 2, center[1] - (miny + maxy) / 2)
    if thicken:
        shape = shape.buffer(thicken, quad_segs=4)
    return shape


def trace_png(png_path, width=None, height=None, center=(0, 0), thicken=0.0, smooth_px=1.2):
    """Vectorise une image (texte noir sur fond blanc) -> MultiPolygon Shapely en mm."""
    import cv2
    import numpy as np
    from shapely.geometry import Polygon
    img = cv2.imread(png_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    _, bw = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV)
    contours, hier = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    for i, c in enumerate(contours):
        if hier[0][i][3] != -1 or len(c) < 8:
            continue                                           # trous traités avec leur parent
        outer = cv2.approxPolyDP(c, smooth_px, True)[:, 0, :].astype(float)
        holes = []
        j = hier[0][i][2]
        while j != -1:
            if len(contours[j]) >= 8:
                holes.append(cv2.approxPolyDP(contours[j], smooth_px, True)[:, 0, :].astype(float))
            j = hier[0][j][0]
        if len(outer) >= 3:
            p = Polygon(outer, [h for h in holes if len(h) >= 3]).buffer(0)
            if p.area > 4:
                polys.append(p)
    shape = unary_union(polys)
    shape = affinity.scale(shape, 1, -1, origin=(0, 0))       # axe image vers le bas -> z vers le haut
    minx, miny, maxx, maxy = shape.bounds
    s = min((width / (maxx - minx)) if width else 1e9, (height / (maxy - miny)) if height else 1e9)
    shape = affinity.scale(shape, s, s, origin=(0, 0))
    minx, miny, maxx, maxy = shape.bounds
    shape = affinity.translate(shape, center[0] - (minx + maxx) / 2, center[1] - (miny + maxy) / 2)
    return shape.buffer(thicken, quad_segs=4) if thicken else shape
