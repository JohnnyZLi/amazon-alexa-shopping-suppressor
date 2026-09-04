#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def local_popup_assets(popup_path: str) -> set[str]:
    popup = ROOT / popup_path
    if not popup.is_file():
        raise SystemExit(f"Missing popup file: {popup_path}")

    files = {popup_path}
    html = popup.read_text(encoding="utf-8")
    for reference in re.findall(r"(?:src|href)=[\"']([^\"']+)[\"']", html, flags=re.I):
        parsed = urlparse(reference)
        if parsed.scheme or parsed.netloc or reference.startswith(("#", "data:")):
            continue
        resolved = (Path(popup_path).parent / parsed.path).as_posix()
        files.add(resolved)
    return files


def runtime_files(manifest: dict) -> list[str]:
    files = {"manifest.json"}
    for entry in manifest.get("content_scripts", []):
        files.update(entry.get("js", []))
        files.update(entry.get("css", []))
    files.update((manifest.get("icons") or {}).values())

    action = manifest.get("action") or {}
    popup = action.get("default_popup")
    if popup:
        files.update(local_popup_assets(popup))

    return sorted(files)


def write_deterministic_zip(output: Path, files: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in files:
            path = ROOT / relative
            if not path.is_file():
                raise SystemExit(f"Missing runtime file: {relative}")
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic Chrome extension ZIP")
    parser.add_argument("--output", type=Path, help="Output ZIP path")
    args = parser.parse_args()

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    output = args.output or ROOT / "dist" / f"amazon-alexa-shopping-suppressor-v{version}.zip"
    if not output.is_absolute():
        output = ROOT / output

    files = runtime_files(manifest)
    write_deterministic_zip(output, files)

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_suffix(output.suffix + ".sha256")
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8")

    print(output)
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
