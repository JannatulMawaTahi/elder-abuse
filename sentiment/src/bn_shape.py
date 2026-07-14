# -*- coding: utf-8 -*-
"""
Proper Bengali (Indic) text rendering for matplotlib.

matplotlib has no complex-text shaping engine, so Bangla conjuncts (যুক্তাক্ষর)
and vowel-sign reordering (ই-কার ি) render wrong. This module shapes a string
with HarfBuzz (uharfbuzz), pulls the real glyph outlines with fontTools, and
returns either a matplotlib Path or a rasterised RGBA image of the shaped line.

Use BnFont.render_image(text, size_pt) -> RGBA array, then place it on an axis
with OffsetImage/AnnotationBbox (zoom = 72/dpi).
"""
from __future__ import annotations
import io
from functools import lru_cache

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch


class _MplPen(BasePen):
    """fontTools pen that records a matplotlib Path (handles composites)."""
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.verts: list = []
        self.codes: list = []

    def _moveTo(self, p):
        self.verts.append(p); self.codes.append(MPath.MOVETO)

    def _lineTo(self, p):
        self.verts.append(p); self.codes.append(MPath.LINETO)

    def _qCurveToOne(self, c, p):
        self.verts.extend([c, p]); self.codes.extend([MPath.CURVE3, MPath.CURVE3])

    def _curveToOne(self, c1, c2, p):
        self.verts.extend([c1, c2, p]); self.codes.extend([MPath.CURVE4] * 3)

    def _closePath(self):
        self.verts.append((0, 0)); self.codes.append(MPath.CLOSEPOLY)


class BnFont:
    def __init__(self, font_path: str):
        self.font_path = str(font_path)
        blob = hb.Blob.from_file_path(self.font_path)
        face = hb.Face(blob)
        self.hbfont = hb.Font(face)
        self.tt = TTFont(self.font_path)
        self.gs = self.tt.getGlyphSet()
        self.upem = self.tt["head"].unitsPerEm
        self.asc = self.tt["hhea"].ascent
        self.desc = self.tt["hhea"].descent

    def shape_path(self, text: str, size_pt: float):
        """Return (matplotlib Path in point units, width_pt)."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf)
        s = size_pt / self.upem
        verts: list = []
        codes: list = []
        penx = 0.0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = self.tt.getGlyphName(info.codepoint)
            pen = _MplPen(self.gs)
            self.gs[name].draw(pen)
            ox = (penx + pos.x_offset) * s
            oy = pos.y_offset * s
            for (x, y), code in zip(pen.verts, pen.codes):
                verts.append((x * s + ox, y * s + oy)); codes.append(code)
            penx += pos.x_advance
        if not verts:                      # empty / all-space
            return MPath([(0, 0)], [MPath.MOVETO]), penx * s
        return MPath(verts, codes), penx * s

    @lru_cache(maxsize=512)
    def render_image(self, text: str, size_pt: float = 15.0,
                     color: str = "#222222", dpi: int = 220, pad_pt: float = 2.0):
        """Rasterise a shaped line to an RGBA array (transparent background).
        Place with OffsetImage(img, zoom=72/dpi) for size_pt-accurate height."""
        path, width = self.shape_path(text, size_pt)
        asc = self.asc * size_pt / self.upem
        desc = self.desc * size_pt / self.upem
        W = max(width, 1.0) + 2 * pad_pt
        H = (asc - desc) + 2 * pad_pt
        fig = plt.figure(figsize=(W / 72.0, H / 72.0), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-pad_pt, width + pad_pt)
        ax.set_ylim(desc - pad_pt, asc + pad_pt)
        ax.axis("off")
        ax.add_patch(PathPatch(path, facecolor=color, edgecolor="none"))
        buf = io.BytesIO()
        fig.savefig(buf, dpi=dpi, transparent=True, format="png")
        plt.close(fig)
        buf.seek(0)
        return plt.imread(buf)


# zoom factor to pass to OffsetImage so the image renders at its true point size
def zoom_for(dpi: int = 220) -> float:
    return 72.0 / dpi
