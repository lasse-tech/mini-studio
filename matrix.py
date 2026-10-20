"""Matrix look of Mini Studio: palette, 5×5 patterns and the widgets that draw them."""

from __future__ import annotations

import math
import re

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk

# Keep in step with mini-studio.css and mini-studio.svg
LED = "#ff5a3c"
UNLIT = "#2e3139"
TILE = "#1d2027"
MUTED = "#8b8f99"

# Rows of five cells, "1" is a lit LED
MARK = ("10001", "11011", "10101", "10001", "10001")
ICONS = {
    "open": ("11000", "11111", "10001", "10001", "11111"),
    "save": ("00100", "10101", "01110", "00100", "11111"),
    "build": ("00000", "00001", "00010", "10100", "01000"),
    "flash": ("00110", "01100", "11111", "00110", "01100"),
    "hex": ("01010", "11111", "01010", "11111", "01010"),
    "about": ("00100", "00000", "00100", "00100", "00100"),
    "library": ("10000", "10100", "10101", "10101", "11111"),
    "melody": ("00110", "00101", "00100", "11100", "11100"),
}

# Lowercase dot-matrix letters for the wordmark: two ascender rows, five x-height rows
GLYPHS = {
    "m": ("00000", "00000", "11110", "10101", "10101", "10101", "10101"),
    "i": ("1", "0", "1", "1", "1", "1", "1"),
    "n": ("0000", "0000", "1110", "1001", "1001", "1001", "1001"),
    "s": ("0000", "0000", "0111", "1000", "0110", "0001", "1110"),
    "t": ("010", "010", "111", "010", "010", "010", "001"),
    "u": ("0000", "0000", "1001", "1001", "1001", "1001", "0111"),
    "d": ("0001", "0001", "0111", "1001", "1001", "1001", "0111"),
    "o": ("0000", "0000", "0110", "1001", "1001", "1001", "0110"),
}

SHOW_LEDS = re.compile(r"showLeds\(\s*`([^`]*)`")


def rgba(color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    value = int(color.lstrip("#"), 16)
    return (value >> 16) / 255, (value >> 8 & 255) / 255, (value & 255) / 255, alpha


def rounded_rect(cr, x: float, y: float, width: float, height: float, radius: float):
    cr.new_sub_path()
    cr.arc(x + width - radius, y + radius, radius, -math.pi / 2, 0)
    cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
    cr.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
    cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
    cr.close_path()


def draw_cells(cr, rows, x, y, cell, step, lit, unlit, glow=None) -> None:
    """Draw a pattern; glow paints a soft halo behind each lit cell."""
    for row, line in enumerate(rows):
        for column, value in enumerate(line):
            left, top = x + column * step, y + row * step
            if value == "1" and glow:
                spread = cell * 0.28
                cr.set_source_rgba(*glow)
                rounded_rect(
                    cr,
                    left - spread,
                    top - spread,
                    cell + 2 * spread,
                    cell + 2 * spread,
                    cell * 0.5,
                )
                cr.fill()
            colour = lit if value == "1" else unlit
            if colour is None:
                continue
            cr.set_source_rgba(*colour)
            rounded_rect(cr, left, top, cell, cell, cell * 0.25)
            cr.fill()


def draw_mark(cr, size: float) -> None:
    cr.set_source_rgba(*rgba(TILE))
    rounded_rect(cr, 0, 0, size, size, size * 0.22)
    cr.fill()
    draw_cells(
        cr,
        MARK,
        size * 0.11,
        size * 0.11,
        size * 0.12,
        size * 0.165,
        rgba(LED),
        rgba(UNLIT),
        rgba(LED, 0.22) if size >= 32 else None,
    )


def mark_pixbuf(size: int):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    draw_mark(cairo.Context(surface), size)
    return Gdk.pixbuf_get_from_surface(surface, 0, 0, size, size)


def led_pattern(source: str, offset: int) -> tuple[str, ...] | None:
    """The showLeds image at or before offset, else the first one in source."""
    found = None
    for match in SHOW_LEDS.finditer(source):
        if found is not None and match.start() > offset:
            break
        found = match
    if found is None:
        return None
    rows = tuple(
        "".join("1" if token == "#" else "0" for token in line.split())
        for line in found.group(1).splitlines()
        if line.strip()
    )
    if len(rows) != 5 or any(len(row) != 5 for row in rows):
        return None
    return rows


class Mark(Gtk.DrawingArea):
    def __init__(self, size: int) -> None:
        super().__init__(valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
        self.size = size
        self.set_size_request(size, size)
        self.connect("draw", lambda _widget, cr: draw_mark(cr, self.size))


class Wordmark(Gtk.DrawingArea):
    """“mini” lit, “studio” dark, in the dot-matrix letters above."""

    def __init__(self, dot: float = 2.6) -> None:
        super().__init__(valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
        self.dot = dot
        self.words = (("mini", rgba(LED)), ("studio", rgba(MUTED)))
        columns = (
            sum(len(GLYPHS[c][0]) + 1 for word, _colour in self.words for c in word) - 1
        )
        self.set_size_request(math.ceil(columns * dot * 1.3), math.ceil(7 * dot * 1.3))
        self.connect("draw", self.on_draw)

    def on_draw(self, _widget, cr) -> bool:
        step = self.dot * 1.3
        x = 0.0
        for word, colour in self.words:
            for letter in word:
                glyph = GLYPHS[letter]
                draw_cells(cr, glyph, x, 0, self.dot, step, colour, None)
                x += (len(glyph[0]) + 1) * step
        return False


class PixelIcon(Gtk.DrawingArea):
    """A 5×5 icon in the widget's text colour, unlit cells faint."""

    def __init__(self, name: str, size: int = 16) -> None:
        super().__init__(valign=Gtk.Align.CENTER)
        self.rows = ICONS[name]
        self.set_size_request(size, size)
        self.connect("draw", self.on_draw)

    def on_draw(self, widget, cr) -> bool:
        colour = widget.get_style_context().get_color(widget.get_state_flags())
        size = min(widget.get_allocated_width(), widget.get_allocated_height())
        step = size / 5
        draw_cells(
            cr,
            self.rows,
            step * 0.1,
            step * 0.1,
            step * 0.8,
            step,
            (colour.red, colour.green, colour.blue, colour.alpha),
            (colour.red, colour.green, colour.blue, colour.alpha * 0.16),
        )
        return False


class LedMatrix(Gtk.DrawingArea):
    """Preview of the 5×5 LED matrix of the Calliope mini."""

    def __init__(self, size: int) -> None:
        super().__init__(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
        self.rows: tuple[str, ...] = ("00000",) * 5
        self.set_size_request(size, size)
        self.connect("draw", self.on_draw)

    def set_pattern(self, rows: tuple[str, ...] | None) -> None:
        rows = rows or ("00000",) * 5
        if rows != self.rows:
            self.rows = rows
            self.queue_draw()

    def on_draw(self, widget, cr) -> bool:
        size = min(widget.get_allocated_width(), widget.get_allocated_height())
        step = size / 5
        draw_cells(
            cr,
            self.rows,
            step * 0.12,
            step * 0.12,
            step * 0.76,
            step,
            rgba(LED),
            rgba("#2a2d34"),
            rgba(LED, 0.2),
        )
        return False


class StatusLed(Gtk.DrawingArea):
    def __init__(self) -> None:
        super().__init__(valign=Gtk.Align.CENTER)
        self.active = False
        self.set_size_request(12, 12)
        self.connect("draw", self.on_draw)

    def set_active(self, active: bool) -> None:
        if active != self.active:
            self.active = active
            self.queue_draw()

    def on_draw(self, _widget, cr) -> bool:
        if self.active:
            cr.set_source_rgba(*rgba(LED, 0.3))
            cr.arc(6, 6, 6, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgba(*rgba(LED))
            cr.arc(6, 6, 3.5, 0, 2 * math.pi)
            cr.fill()
        else:
            cr.set_source_rgba(*rgba(MUTED))
            cr.set_line_width(1.2)
            cr.arc(6, 6, 3.2, 0, 2 * math.pi)
            cr.stroke()
        return False
