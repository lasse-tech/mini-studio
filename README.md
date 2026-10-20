# Mini Studio

Linux editor for MakeCode TypeScript on the Calliope mini V3. The example plays
the main theme of the Imperial March on start (melody only, taken from the
trumpet line of an orchestral MIDI) and blinks the 5×5 LED matrix in time.
Button A plays the melody again.

## Start

Requires Python 3, PyGObject/GTK 3 with pycairo (Debian/Ubuntu: `python3-gi`,
`python3-gi-cairo`, `gir1.2-gtk-3.0`), Node.js and the official
[MakeCode CLI `mkc`](https://github.com/microsoft/pxt-mkc):

```sh
npm install -g makecode
make debug
```

`make flash` builds `main.ts` and copies the HEX to a mounted Calliope mini V3
without the editor; `make install` puts the editor into `~/.local`, together
with a desktop entry and the app icon.

Edit `main.ts` in the editor and click **Build + Flash**.
On the first build `mkc` downloads the Calliope compiler from
`https://makecode.calliope.cc/`, so an internet connection is needed.
The app only writes to the `MINI` drive if its DAPLink info file identifies
a Calliope mini V3. Alternatively, an already compiled `.hex` file can be
flashed with **Flash HEX**.

The code is MakeCode TypeScript; `mkc` cannot compile plain JavaScript or
MicroPython in this project.

## Look

Mini Studio brings its own dark “Matrix” theme (`mini-studio.css` on top of
Adwaita) instead of the desktop theme. Mark, wordmark and icons are 5×5 LED
patterns drawn in `matrix.py`; `mini-studio.svg` is the app icon. The sidebar
previews the `showLeds` image at the cursor and shows whether the program uses
buttons A and B. Fonts: Atkinson Hyperlegible and JetBrains Mono if installed,
otherwise the usual fallbacks.

## Translations

The interface is English, with German as the second language. Source strings
live in the code, translations in `po/<language>.po`: `make pot` extracts new
strings and merges them, `make locale` compiles them, and `make lint` fails on
any untranslated string. The language follows `LANGUAGE`/`LANG`; console output
of `make flash` stays English.

## Licence

MIT, see `LICENSE`. `midi/imperial-march.mid` is the source of the melody in
`main.ts`; the Imperial March is a composition by John Williams.
