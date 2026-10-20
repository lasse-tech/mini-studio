"""Build MakeCode projects and deploy verified HEX images to DAPLink."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from i18n import _


class CalliopeError(RuntimeError):
    pass


def find_device() -> Path | None:
    """Only accept a mounted Calliope mini V3 interface, never an arbitrary MINI drive."""
    candidates = []
    for base in (Path("/media"), Path("/run/media")):
        if base.exists():
            candidates.extend(base.glob("*/MINI"))
    for mount in candidates:
        if is_calliope_v3(mount):
            return mount
    return None


def is_calliope_v3(mount: Path) -> bool:
    details = mount / "DETAILS.TXT"
    try:
        info = details.read_text(errors="replace")
    except OSError:
        return False
    return "DAPLink Firmware" in info and "HIC ID: 6e052820" in info


def build(project: Path) -> tuple[Path, str]:
    if not (project / "pxt.json").is_file() or not (project / "main.ts").is_file():
        raise CalliopeError(_("The project needs pxt.json and main.ts."))
    if not shutil.which("mkc"):
        raise CalliopeError(
            _("mkc is missing. Install it with: npm install -g makecode")
        )
    try:
        result = subprocess.run(
            ["mkc", "build"],
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CalliopeError(_("mkc did not respond within three minutes.")) from exc
    if result.returncode:
        raise CalliopeError(
            _("mkc build failed:\n{output}").format(output=result.stdout)
        )
    built = project / "built"
    hex_files = (
        sorted(
            built.rglob("*.hex"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if built.exists()
        else []
    )
    if not hex_files:
        raise CalliopeError(
            _("mkc produced no HEX file.\n{output}").format(output=result.stdout)
        )
    image = hex_files[0]
    if not image.read_bytes().startswith(b":"):
        raise CalliopeError(_("Invalid Intel HEX format: {path}").format(path=image))
    return image, result.stdout


def flash(image: Path, mount: Path | None = None) -> Path:
    mount = mount or find_device()
    if mount is None:
        raise CalliopeError(_("No mounted Calliope mini V3 found."))
    if not is_calliope_v3(mount):
        raise CalliopeError(
            _("{path} is not a verified Calliope mini V3.").format(path=mount)
        )
    if not image.is_file() or image.suffix.lower() != ".hex":
        raise CalliopeError(_("Choose an existing .hex file."))
    if not image.read_bytes().startswith(b":"):
        raise CalliopeError(_("The file is not an Intel HEX file."))
    destination = mount / "CALLIOPE.HEX"
    try:
        with image.open("rb") as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target, length=64 * 1024)
            target.flush()
            os.fsync(target.fileno())
    except OSError as exc:
        raise CalliopeError(_("Transfer failed: {error}").format(error=exc)) from exc
    failure = mount / "FAIL.TXT"
    if failure.is_file():
        raise CalliopeError(
            _("DAPLink reports an error: {error}").format(
                error=failure.read_text(errors="replace")
            )
        )
    return destination
