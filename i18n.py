"""English user interface with German as the second language."""

from __future__ import annotations

import os

GERMAN = {
    # Window
    "Open": "Öffnen",
    "Save": "Speichern",
    "Build": "Übersetzen",
    "Flash HEX": "HEX übertragen",
    "Build + Flash": "Übersetzen + übertragen",
    "Open a MakeCode project folder": "MakeCode-Projektordner öffnen",
    "Save main.ts (Ctrl+S)": "main.ts speichern (Strg+S)",
    "Build main.ts with mkc": "main.ts mit mkc übersetzen",
    "Flash a compiled .hex file": "Eine fertige .hex-Datei übertragen",
    "Build and copy the HEX to the mini": "Übersetzen und die HEX auf den mini kopieren",
    "About Mini Studio": "Über Mini Studio",
    "LED PREVIEW": "LED-VORSCHAU",
    "showLeds at the cursor": "showLeds an der Schreibmarke",
    "Button {name}": "Taste {name}",
    "The program reacts to button {name}": "Das Programm reagiert auf Taste {name}",
    "The program does not use button {name}": "Das Programm nutzt Taste {name} nicht",
    "DEVICE": "GERÄT",
    "connected · {mount}": "verbunden · {mount}",
    "not connected": "nicht eingebunden",
    "OUTPUT": "AUSGABE",
    # Messages
    "A project needs main.ts and pxt.json.": "Projekt braucht main.ts und pxt.json.",
    "Opened project: {path}": "Projekt geöffnet: {path}",
    "Choose a MakeCode project": "MakeCode-Projekt wählen",
    "Cancel": "Abbrechen",
    "Saved main.ts.": "main.ts gespeichert.",
    "A task is already running.": "Ein Vorgang läuft bereits.",
    "Error: {error}": "Fehler: {error}",
    "Done: {image}": "Fertig: {image}",
    "Flashed: {destination}": "Übertragen: {destination}",
    "Building with mkc …": "Übersetze mit mkc …",
    "Building and flashing …": "Übersetze und übertrage …",
    "Choose a HEX file": "HEX-Datei wählen",
    "Flash": "Übertragen",
    "Flashing HEX …": "Übertrage HEX …",
    # Backend
    "mkc is missing. Install it with: npm install -g makecode": (
        "mkc fehlt. Installiere es mit: npm install -g makecode"
    ),
    "mkc did not answer within three minutes.": "mkc hat nach drei Minuten nicht geantwortet.",
    "mkc build failed:\n{output}": "mkc build fehlgeschlagen:\n{output}",
    "mkc did not produce a HEX file.\n{output}": "mkc hat keine HEX-Datei erzeugt.\n{output}",
    "Invalid Intel HEX format: {image}": "Ungültiges Intel-HEX-Format: {image}",
    "No mounted Calliope mini V3 found.": "Kein eingebundener Calliope mini V3 gefunden.",
    "{mount} is not a verified Calliope mini V3.": "{mount} ist kein verifizierter Calliope mini V3.",
    "Please choose an existing .hex file.": "Bitte eine vorhandene .hex-Datei auswählen.",
    "The file is not an Intel HEX file.": "Die Datei ist keine Intel-HEX-Datei.",
    "Flashing failed: {error}": "Übertragung fehlgeschlagen: {error}",
    "DAPLink reports an error: {details}": "DAPLink meldet einen Fehler: {details}",
    # About
    "Editor and flasher for MakeCode TypeScript on the Calliope mini V3.": (
        "Editor und Flasher für MakeCode-TypeScript auf dem Calliope mini V3."
    ),
    "Released under the MIT licence.": "Veröffentlicht unter der MIT-Lizenz.",
}


def wants_german() -> bool:
    """Follow the first locale variable that is set, as gettext does."""
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable)
        if value:
            return value.split(":")[0].startswith("de")
    return False


USE_GERMAN = wants_german()


def _(text: str) -> str:
    return GERMAN.get(text, text) if USE_GERMAN else text
