"""Save a PNG of the app window: PYTHONPATH=<app dir> screenshot.py <out.png>."""

from __future__ import annotations

import sys

import app
import i18n

# GTK as app loads it, after gi.require_version
Gdk, GLib, Gtk = app.Gdk, app.GLib, app.Gtk


def capture(window: Gtk.Window) -> bool:
    gdk_window = window.get_window()
    pixbuf = Gdk.pixbuf_get_from_window(
        gdk_window, 0, 0, gdk_window.get_width(), gdk_window.get_height()
    )
    pixbuf.savev(sys.argv[1], "png", [], [])
    Gtk.main_quit()
    return False


i18n.setup()
GLib.set_prgname("mini-studio")
app.apply_theme()
window = app.CalliopeApp()
window.show_all()
# Cursor inside the first showLeds image so the LED preview lights up
window.buffer.place_cursor(window.buffer.get_iter_at_line(33))
GLib.timeout_add(2000, capture, window)
Gtk.main()
