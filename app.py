#!/usr/bin/env python3
"""Small GTK editor for MakeCode Calliope mini projects."""

from __future__ import annotations

import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

import i18n
from calliope_backend import CalliopeError, build, find_device, flash
from i18n import _


class CalliopeApp(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Mini Studio")
        self.project = Path(__file__).resolve().parent
        self.busy = False
        self.set_default_size(940, 720)
        self.set_border_width(12)
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self.on_key)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        self.add(root)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        root.pack_start(toolbar, False, False, 0)
        for label, callback in (
            (_("Open project"), self.open_project),
            (_("Save"), self.save),
            (_("Build"), self.do_build),
            (_("Build + flash"), self.do_build_flash),
            (_("Flash HEX"), self.choose_hex),
        ):
            button = Gtk.Button(label=label)
            button.connect("clicked", callback)
            toolbar.pack_start(button, False, False, 0)

        self.device_label = Gtk.Label(xalign=0)
        root.pack_start(self.device_label, False, False, 0)

        editor_frame = Gtk.Frame(label="main.ts · MakeCode TypeScript")
        root.pack_start(editor_frame, True, True, 0)
        editor_scroll = Gtk.ScrolledWindow()
        editor_frame.add(editor_scroll)
        self.editor = Gtk.TextView()
        self.editor.set_monospace(True)
        self.editor.set_wrap_mode(Gtk.WrapMode.NONE)
        self.editor.set_left_margin(12)
        self.editor.set_right_margin(12)
        editor_scroll.add(self.editor)
        self.buffer = self.editor.get_buffer()

        log_frame = Gtk.Frame(label=_("Output"))
        root.pack_start(log_frame, False, False, 0)
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_size_request(-1, 170)
        log_frame.add(log_scroll)
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_monospace(True)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        log_scroll.add(self.log_view)

        self.load_project(self.project)
        self.update_device()
        GLib.timeout_add_seconds(2, self.update_device)

    def log(self, message: str) -> None:
        buffer = self.log_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), message.rstrip() + "\n")
        self.log_view.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)

    def update_device(self) -> bool:
        mount = find_device()
        self.device_label.set_text(
            _("● Calliope mini V3 connected: {path}").format(path=mount)
            if mount
            else _("○ No Calliope mini V3 mounted")
        )
        return True

    def load_project(self, path: Path) -> None:
        source = path / "main.ts"
        config = path / "pxt.json"
        if not source.is_file() or not config.is_file():
            self.log(_("The project needs pxt.json and main.ts."))
            return
        self.project = path
        self.buffer.set_text(source.read_text(encoding="utf-8"))
        self.buffer.set_modified(False)
        self.set_title(f"Mini Studio — {path}")
        self.log(_("Project opened: {path}").format(path=path))

    def open_project(self, *_args) -> None:
        dialog = Gtk.FileChooserDialog(
            title=_("Choose a MakeCode project"),
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL, _("Open"), Gtk.ResponseType.OK
        )
        if dialog.run() == Gtk.ResponseType.OK:
            self.load_project(Path(dialog.get_filename()))
        dialog.destroy()

    def save(self, *_args) -> None:
        start, end = self.buffer.get_bounds()
        (self.project / "main.ts").write_text(
            self.buffer.get_text(start, end, True), encoding="utf-8"
        )
        self.buffer.set_modified(False)
        self.log(_("main.ts saved."))

    def on_key(self, _widget, event) -> bool:
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval == Gdk.KEY_s:
            self.save()
            return True
        return False

    def run_task(self, task, heading: str) -> None:
        if self.busy:
            self.log(_("A task is already running."))
            return
        self.busy = True
        self.log(heading)

        def worker() -> None:
            try:
                result = task()
                GLib.idle_add(self.log, result)
            except (CalliopeError, OSError, TimeoutError) as exc:
                GLib.idle_add(self.log, _("Error: {error}").format(error=exc))
            finally:
                GLib.idle_add(self.finish_task)

        threading.Thread(target=worker, daemon=True).start()

    def finish_task(self) -> bool:
        self.busy = False
        self.update_device()
        return False

    def do_build(self, *_args) -> None:
        self.save()

        def task() -> str:
            image, output = build(self.project)
            return output + "\n" + _("Done: {path}").format(path=image)

        self.run_task(task, _("Building with mkc …"))

    def do_build_flash(self, *_args) -> None:
        self.save()

        def task() -> str:
            image, output = build(self.project)
            destination = flash(image)
            return output + "\n" + _("Flashed: {path}").format(path=destination)

        self.run_task(task, _("Building and flashing …"))

    def choose_hex(self, *_args) -> None:
        dialog = Gtk.FileChooserDialog(
            title=_("Choose a HEX file"),
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL, _("Flash"), Gtk.ResponseType.OK
        )
        filter_hex = Gtk.FileFilter()
        filter_hex.set_name("Intel HEX (*.hex)")
        filter_hex.add_pattern("*.hex")
        dialog.add_filter(filter_hex)
        if dialog.run() == Gtk.ResponseType.OK:
            image = Path(dialog.get_filename())
            self.run_task(
                lambda: _("Flashed: {path}").format(path=flash(image)),
                _("Flashing HEX …"),
            )
        dialog.destroy()


if __name__ == "__main__":
    i18n.setup()
    window = CalliopeApp()
    window.show_all()
    Gtk.main()
