# Mini Studio

Linux editor for MakeCode TypeScript on the Calliope mini V3. The example plays
the main theme of the Imperial March on start (melody only, taken from the
trumpet line of an orchestral MIDI) and blinks the 5×5 LED matrix in time.
Button A plays the melody again.

## Start

Requires Python 3, PyGObject/GTK 3, Node.js and the official
[MakeCode CLI `mkc`](https://github.com/microsoft/pxt-mkc):

```sh
npm install -g makecode
make debug
```

`make flash` builds `main.ts` and copies the HEX to a mounted Calliope mini V3
without the editor; `make install` puts the editor into `~/.local`.

Edit `main.ts` in the editor and click **Build + flash**.
On the first build `mkc` downloads the Calliope compiler from
`https://makecode.calliope.cc/`, so an internet connection is needed.
The app only writes to the `MINI` drive if its DAPLink info file identifies
a Calliope mini V3. Alternatively, an already compiled `.hex` file can be
flashed with **Flash HEX**.

The code is MakeCode TypeScript; `mkc` cannot compile plain JavaScript or
MicroPython in this project.

## Translations

The interface is English, with German as the second language. Source strings
live in the code, translations in `po/<language>.po`: `make pot` extracts new
strings and merges them, `make locale` compiles them, and `make lint` fails on
any untranslated string. The language follows `LANGUAGE`/`LANG`; console output
of `make flash` stays English.

## Licence

MIT, see `LICENSE`. `midi/imperial-march.mid` is the source of the melody in
`main.ts`; the Imperial March is a composition by John Williams.
