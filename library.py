"""Projects shipped with Mini Studio, copied into the user's folder before editing."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from i18n import _

LIBRARY_DIR = Path(__file__).resolve().parent / "library"


@dataclass(frozen=True)
class Entry:
    slug: str  # folder in library/ and in the user's folder
    title: str
    kind: str
    origin: str


def entries() -> tuple[Entry, ...]:
    """Called at display time so kinds follow the active translation."""
    return (
        Entry("imperial-march", "Imperial March", _("Melody"), "Star Wars"),
        Entry(
            "deep-space-nine",
            "Deep Space Nine",
            _("Melody"),
            "Star Trek: Deep Space Nine",
        ),
    )


def user_copy(entry: Entry, folder: Path) -> tuple[Path, bool]:
    """Copy the entry into folder unless a copy exists; True if it was copied."""
    target = folder / entry.slug
    if target.exists():
        return target, False
    shutil.copytree(
        LIBRARY_DIR / entry.slug,
        target,
        ignore=shutil.ignore_patterns("built", ".pxt", "node_modules"),
    )
    return target, True
