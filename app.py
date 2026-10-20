#!/usr/bin/env python3
"""Small GTK editor for MakeCode Calliope mini projects."""

from __future__ import annotations

import re
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gdk, GLib, Gtk, Pango, PangoCairo

import i18n
import library
import matrix
from calliope_backend import CalliopeError, build, find_device, flash
from i18n import _

HERE = Path(__file__).resolve().parent
LEFT = Gtk.TextWindowType.LEFT

# Later entries win where they overlap, so comments and strings come last
SYNTAX = (
    ("function", re.compile(r"\b[A-Za-z_]\w*(?=\()"), "#f3efe8"),
    (
        "keyword",
        re.compile(
            r"\b(?:break|const|continue|else|false|for|function|if|let|new|return|true|while)\b"
        ),
        "#ff8a6b",
    ),
    ("number", re.compile(r"\b\d+(?:\.\d+)?\b"), "#ffb347"),
    ("string", re.compile(r"`[^`]*`|\"[^\"\n]*\"|'[^'\n]*'"), "#f7cf8d"),
    ("comment", re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL), "#6c717c"),
)
BUTTON_HANDLER = re.compile(r"onButtonPressed\(\s*Button\.(AB|A|B)\b")


def apply_theme() -> None:
    """Use Adwaita dark plus our stylesheet instead of the desktop theme."""
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-theme-name", "Adwaita")
    settings.set_property("gtk-application-prefer-dark-theme", True)
    provider = Gtk.CssProvider()
    provider.load_from_path(str(HERE / "mini-studio.css"))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1
    )


def styled(widget: Gtk.Widget, *classes: str) -> Gtk.Widget:
    for name in classes:
        widget.get_style_context().add_class(name)
    return widget


def section(text: str) -> Gtk.Label:
    label = Gtk.Label(xalign=0)
    label.set_markup(
        f'<span letter_spacing="1800">{GLib.markup_escape_text(text)}</span>'
    )
    return styled(label, "section")


class CalliopeApp(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Mini Studio")
        self.project: Path | None = None
        self.busy = False
        self.highlight_pending = False
        self.set_default_size(1040, 720)
        self.set_icon(matrix.mark_pixbuf(128))
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self.on_key)

        header = Gtk.HeaderBar(show_close_button=True)
        header.set_custom_title(Gtk.Box())
        self.set_titlebar(header)
        brand = Gtk.Box(spacing=9, margin_start=4, margin_end=14)
        brand.pack_start(matrix.Mark(24), False, False, 0)
        brand.pack_start(matrix.Wordmark(), False, False, 0)
        header.pack_start(brand)
        self.task_buttons = []
        for icon, label, tip, callback, task in (
            (
                "open",
                _("Open"),
                _("Open a MakeCode project folder"),
                self.open_project,
                False,
            ),
            ("save", _("Save"), _("Save main.ts (Ctrl+S)"), self.save, False),
            ("build", _("Build"), _("Build main.ts with mkc"), self.do_build, True),
            (
                "hex",
                _("Flash HEX"),
                _("Flash a compiled .hex file"),
                self.choose_hex,
                True,
            ),
        ):
            button = self.action_button(icon, label, tip, callback)
            header.pack_start(button)
            if task:
                self.task_buttons.append(button)
            if icon == "open":
                header.pack_start(self.library_button())
        primary = self.action_button(
            "flash",
            _("Build + Flash"),
            _("Build and copy the HEX to the mini"),
            self.do_build_flash,
        )
        header.pack_end(styled(primary, "primary"))
        self.task_buttons.append(primary)
        header.pack_end(
            self.action_button("about", None, _("About Mini Studio"), self.show_about)
        )

        body = Gtk.Box()
        self.add(body)
        body.pack_start(self.sidebar(), False, False, 0)
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body.pack_start(main, True, True, 0)

        self.tab = styled(
            Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE), "tab"
        )
        main.pack_start(self.tab, False, False, 0)
        editor_scroll = Gtk.ScrolledWindow()
        main.pack_start(editor_scroll, True, True, 0)
        self.editor = Gtk.TextView(
            monospace=True,
            wrap_mode=Gtk.WrapMode.NONE,
            left_margin=14,
            right_margin=12,
            top_margin=10,
            bottom_margin=10,
        )
        self.editor.set_border_window_size(LEFT, 44)
        self.editor.connect_after("draw", self.draw_line_numbers)
        editor_scroll.add(self.editor)
        self.buffer = self.editor.get_buffer()
        for name, _pattern, colour in SYNTAX:
            self.buffer.create_tag(
                name,
                foreground=colour,
                weight=Pango.Weight.SEMIBOLD
                if name == "function"
                else Pango.Weight.NORMAL,
            )
        self.buffer.connect("changed", self.on_changed)
        self.buffer.connect("mark-set", self.on_mark_set)

        log_box = styled(
            Gtk.Box(orientation=Gtk.Orientation.VERTICAL), "output", "output-frame"
        )
        main.pack_start(log_box, False, False, 0)
        log_label = section(_("OUTPUT"))
        log_label.set_margin_start(16)
        log_label.set_margin_top(8)
        log_box.pack_start(log_label, False, False, 0)
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_size_request(-1, 150)
        log_box.pack_start(log_scroll, True, True, 0)
        self.log_view = styled(
            Gtk.TextView(
                editable=False,
                cursor_visible=False,
                monospace=True,
                wrap_mode=Gtk.WrapMode.WORD_CHAR,
                left_margin=16,
                right_margin=16,
                top_margin=4,
                bottom_margin=10,
            ),
            "output",
        )
        log_scroll.add(self.log_view)
        log_buffer = self.log_view.get_buffer()
        log_buffer.create_tag("ok", foreground="#ffb347")
        log_buffer.create_tag("error", foreground=matrix.LED)

        self.open_entry(library.entries()[0])
        self.update_device()
        GLib.timeout_add_seconds(2, self.update_device)

    def action_button(
        self, icon: str, label: str | None, tip: str, callback
    ) -> Gtk.Button:
        button = Gtk.Button(tooltip_text=tip)
        content = Gtk.Box(spacing=7)
        content.pack_start(matrix.PixelIcon(icon), False, False, 0)
        if label:
            content.pack_start(Gtk.Label(label=label), False, False, 0)
        button.add(content)
        button.connect("clicked", callback)
        return button

    def library_button(self) -> Gtk.MenuButton:
        button = Gtk.MenuButton(tooltip_text=_("Open a project from the library"))
        content = Gtk.Box(spacing=7)
        content.pack_start(matrix.PixelIcon("library"), False, False, 0)
        content.pack_start(Gtk.Label(label=_("Library")), False, False, 0)
        button.add(content)
        popover = styled(Gtk.Popover(), "library")
        rows = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE, margin=6)
        popover.add(rows)
        for entry in library.entries():
            row = Gtk.ListBoxRow()
            row.entry = entry
            line = Gtk.Box(spacing=12, margin=8)
            line.pack_start(matrix.PixelIcon("melody"), False, False, 0)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title = Gtk.Label(xalign=0)
            title.set_markup(f"<b>{GLib.markup_escape_text(entry.title)}</b>")
            text.pack_start(title, False, False, 0)
            text.pack_start(
                styled(
                    Gtk.Label(label=f"{entry.kind} · {entry.origin}", xalign=0), "hint"
                ),
                False,
                False,
                0,
            )
            line.pack_start(text, True, True, 0)
            row.add(line)
            rows.add(row)
        rows.show_all()

        def activated(_rows, row) -> None:
            popover.popdown()
            self.open_entry(row.entry)

        rows.connect("row-activated", activated)
        button.set_popover(popover)
        return button

    def open_entry(self, entry: library.Entry) -> None:
        documents = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
        folder = Path(documents or GLib.get_home_dir()) / "Mini Studio"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            path, copied = library.user_copy(entry, folder)
        except OSError as exc:
            self.log(_("Error: {error}").format(error=exc), "error")
            return
        if copied:
            self.log(
                _("Copied {title} from the library to {path}").format(
                    title=entry.title, path=path
                )
            )
        self.load_project(path)

    def sidebar(self) -> Gtk.Widget:
        frame = styled(Gtk.Box(), "sidebar")
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=16)
        side.set_size_request(182, -1)
        frame.pack_start(side, True, True, 0)
        side.pack_start(section(_("LED PREVIEW")), False, False, 0)
        board = styled(Gtk.Box(border_width=16), "board")
        self.leds = matrix.LedMatrix(132)
        board.set_center_widget(self.leds)
        side.pack_start(board, False, False, 0)
        side.pack_start(
            styled(Gtk.Label(label=_("showLeds at the cursor"), xalign=0), "hint"),
            False,
            False,
            0,
        )
        chips = Gtk.Box(spacing=8, homogeneous=True, margin_bottom=10)
        self.chips = {}
        for name in "AB":
            chip = styled(Gtk.Label(label=_("Button {name}").format(name=name)), "chip")
            self.chips[name] = chip
            chips.pack_start(chip, True, True, 0)
        side.pack_start(chips, False, False, 0)

        side.pack_start(section(_("DEVICE")), False, False, 0)
        device = Gtk.Box(spacing=8)
        self.device_led = matrix.StatusLed()
        device.pack_start(self.device_led, False, False, 0)
        device.pack_start(
            styled(Gtk.Label(label="Calliope mini V3", xalign=0), "device"),
            False,
            False,
            0,
        )
        side.pack_start(device, False, False, 0)
        self.device_label = styled(
            Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE), "hint"
        )
        side.pack_start(self.device_label, False, False, 0)
        return frame

    def log(self, message: str, kind: str | None = None) -> None:
        buffer = self.log_view.get_buffer()
        text = message.rstrip() + "\n"
        if kind:
            buffer.insert_with_tags_by_name(buffer.get_end_iter(), text, kind)
        else:
            buffer.insert(buffer.get_end_iter(), text)
        self.log_view.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)

    def update_device(self) -> bool:
        mount = find_device()
        self.device_led.set_active(mount is not None)
        self.device_label.set_text(
            _("connected · {mount}").format(mount=mount)
            if mount
            else _("not connected")
        )
        return True

    def source(self) -> str:
        start, end = self.buffer.get_bounds()
        return self.buffer.get_text(start, end, True)

    def on_changed(self, _buffer) -> None:
        if not self.highlight_pending:
            self.highlight_pending = True
            GLib.idle_add(self.refresh)

    def on_mark_set(self, _buffer, _location, mark) -> None:
        if mark == self.buffer.get_insert():
            self.update_preview(self.source())

    def refresh(self) -> bool:
        self.highlight_pending = False
        source = self.source()
        start, end = self.buffer.get_bounds()
        self.buffer.remove_all_tags(start, end)
        for name, pattern, _colour in SYNTAX:
            for match in pattern.finditer(source):
                self.buffer.apply_tag_by_name(
                    name,
                    self.buffer.get_iter_at_offset(match.start()),
                    self.buffer.get_iter_at_offset(match.end()),
                )
        used = set("".join(BUTTON_HANDLER.findall(source)))
        for name, chip in self.chips.items():
            context = chip.get_style_context()
            if name in used:
                context.add_class("used")
                chip.set_tooltip_text(
                    _("The program reacts to button {name}").format(name=name)
                )
            else:
                context.remove_class("used")
                chip.set_tooltip_text(
                    _("The program does not use button {name}").format(name=name)
                )
        self.update_preview(source)
        return False

    def update_preview(self, source: str) -> None:
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert()).get_offset()
        self.leds.set_pattern(matrix.led_pattern(source, cursor))

    def draw_line_numbers(self, view, cr) -> bool:
        window = view.get_window(LEFT)
        if window is None or not Gtk.cairo_should_draw_window(cr, window):
            return False
        Gtk.cairo_transform_to_window(cr, view, window)
        visible = view.get_visible_rect()
        width = window.get_width()
        layout = view.create_pango_layout("")
        cr.set_source_rgba(*matrix.rgba("#4b4f59"))
        line, _top = view.get_line_at_y(visible.y)
        while True:
            y, _height = view.get_line_yrange(line)
            if y > visible.y + visible.height:
                break
            _x, top = view.buffer_to_window_coords(LEFT, 0, y)
            layout.set_text(str(line.get_line() + 1), -1)
            text_width, _text_height = layout.get_pixel_size()
            cr.move_to(width - text_width - 10, top)
            PangoCairo.show_layout(cr, layout)
            if not line.forward_line():
                break
        return False

    def load_project(self, path: Path) -> None:
        source = path / "main.ts"
        config = path / "pxt.json"
        if not source.is_file() or not config.is_file():
            self.log(_("A project needs main.ts and pxt.json."), "error")
            return
        if self.project and self.buffer.get_modified():
            self.save()
        self.project = path
        self.buffer.set_text(source.read_text(encoding="utf-8"))
        self.buffer.place_cursor(self.buffer.get_start_iter())
        self.buffer.set_modified(False)
        self.set_title(f"Mini Studio — {path}")
        self.tab.set_markup(
            "<b>main.ts</b> · MakeCode TypeScript · "
            + GLib.markup_escape_text(str(path))
        )
        self.log(_("Opened project: {path}").format(path=path))

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
        if self.project is None:
            return
        (self.project / "main.ts").write_text(self.source(), encoding="utf-8")
        self.buffer.set_modified(False)
        self.log(_("Saved main.ts."))

    def on_key(self, _widget, event) -> bool:
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval == Gdk.KEY_s:
            self.save()
            return True
        return False

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        for button in self.task_buttons:
            button.set_sensitive(not busy)

    def run_task(self, task, heading: str) -> None:
        if self.busy:
            self.log(_("A task is already running."))
            return
        self.set_busy(True)
        self.log(heading)

        def worker() -> None:
            try:
                output, summary = task()
                if output.strip():
                    GLib.idle_add(self.log, output)
                GLib.idle_add(self.log, summary, "ok")
            except (CalliopeError, OSError, TimeoutError) as exc:
                GLib.idle_add(self.log, _("Error: {error}").format(error=exc), "error")
            finally:
                GLib.idle_add(self.finish_task)

        threading.Thread(target=worker, daemon=True).start()

    def finish_task(self) -> bool:
        self.set_busy(False)
        self.update_device()
        return False

    def do_build(self, *_args) -> None:
        if self.project is None:
            return
        self.save()

        def task() -> tuple[str, str]:
            image, output = build(self.project)
            return output, _("Done: {image}").format(image=image)

        self.run_task(task, _("Building with mkc …"))

    def do_build_flash(self, *_args) -> None:
        if self.project is None:
            return
        self.save()

        def task() -> tuple[str, str]:
            image, output = build(self.project)
            destination = flash(image)
            return output, _("Flashed: {destination}").format(destination=destination)

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
                lambda: (
                    "",
                    _("Flashed: {destination}").format(destination=flash(image)),
                ),
                _("Flashing HEX …"),
            )
        dialog.destroy()

    def show_about(self, *_args) -> None:
        dialog = styled(
            Gtk.Dialog(
                title=_("About Mini Studio"),
                transient_for=self,
                modal=True,
                use_header_bar=True,
            ),
            "about",
        )
        box = dialog.get_content_area()
        box.set_spacing(12)
        box.set_border_width(32)
        box.pack_start(matrix.Mark(96), False, False, 0)
        wordmark = matrix.Wordmark(dot=4)
        wordmark.set_margin_top(8)
        box.pack_start(wordmark, False, False, 0)
        tagline = Gtk.Label(
            label=_(
                "Editor and flasher for MakeCode TypeScript on the Calliope mini V3."
            ),
            wrap=True,
            justify=Gtk.Justification.CENTER,
            max_width_chars=40,
        )
        box.pack_start(styled(tagline, "tagline"), False, False, 0)
        box.pack_start(Gtk.Label(label="© 2026 Lars Gossard"), False, False, 0)
        box.pack_start(
            styled(Gtk.Label(label=_("Released under the MIT licence.")), "hint"),
            False,
            False,
            0,
        )
        box.pack_start(
            Gtk.LinkButton(
                uri="https://www.lars-gossard.de", label="www.lars-gossard.de"
            ),
            False,
            False,
            0,
        )
        heart = f'<span foreground="{matrix.LED}">♥</span>'
        chip = Gtk.Label(halign=Gtk.Align.CENTER)
        chip.set_markup(_("Made with {heart} in Europe").format(heart=heart))
        box.pack_start(styled(chip, "chip"), False, False, 0)
        dialog.show_all()
        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    i18n.setup()
    GLib.set_prgname("mini-studio")
    apply_theme()
    window = CalliopeApp()
    window.show_all()
    Gtk.main()
