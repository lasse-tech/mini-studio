"""gettext for the user interface; untranslated English until setup() runs."""

from __future__ import annotations

import gettext
from pathlib import Path

DOMAIN = "mini-studio"
LOCALE_DIR = Path(__file__).resolve().parent / "locale"

_translation: gettext.NullTranslations = gettext.NullTranslations()


def setup() -> None:
    """Pick the translation from LANGUAGE, LC_ALL, LC_MESSAGES and LANG."""
    global _translation
    _translation = gettext.translation(DOMAIN, LOCALE_DIR, fallback=True)


def _(message: str) -> str:
    return _translation.gettext(message)
