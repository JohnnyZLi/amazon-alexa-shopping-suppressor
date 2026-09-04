#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
CONTENT = ROOT / "content.js"
POPUP_HTML = ROOT / "popup.html"
POPUP_JS = ROOT / "popup.js"
POPUP_CSS = ROOT / "popup.css"

DOMAINS = [
    "amazon.com", "amazon.ca", "amazon.com.mx", "amazon.com.br", "amazon.co.uk",
    "amazon.de", "amazon.fr", "amazon.it", "amazon.es", "amazon.nl", "amazon.com.be",
    "amazon.se", "amazon.pl", "amazon.ie", "amazon.com.tr", "amazon.ae", "amazon.sa",
    "amazon.eg", "amazon.co.za", "amazon.co.jp", "amazon.in", "amazon.sg", "amazon.com.au",
]
EXPECTED_MATCHES = {
    pattern
    for domain in DOMAINS
    for pattern in (f"https://{domain}/*", f"https://www.{domain}/*")
}
EXPECTED_PERMISSIONS = ["storage"]
EXPECTED_POPUP = "popup.html"

FORBIDDEN_MANIFEST_KEYS = {
    "optional_permissions",
    "host_permissions",
    "optional_host_permissions",
    "background",
    "externally_connectable",
    "web_accessible_resources",
}

FORBIDDEN_SOURCE_PATTERNS = {
    "network fetch": r"\bfetch\s*\(",
    "XMLHttpRequest": r"\bXMLHttpRequest\b",
    "WebSocket": r"\bWebSocket\b",
    "EventSource": r"\bEventSource\b",
    "sendBeacon": r"\bsendBeacon\b",
    "browser extension API": r"\bbrowser\s*\.",
    "localStorage": r"\blocalStorage\b",
    "sessionStorage": r"\bsessionStorage\b",
    "IndexedDB": r"\bindexedDB\b",
    "cookie access": r"\bdocument\s*\.\s*cookie\b",
    "eval": r"\beval\s*\(",
    "Function constructor": r"\bnew\s+Function\b",
    "dynamic import": r"\bimport\s*\(",
}

EXPECTED_ICONS = {
    "16": "icons/icon-16.png",
    "32": "icons/icon-32.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png",
}

REQUIRED_SOURCE_MARKERS = [
    "STATIC_SAFE_SELECTORS",
    "GUARDED_SELECTORS",
    "SENSITIVE_PATH_PATTERNS",
    "restoreManagedElement",
    "restoreUnsafeManagedElements",
    "hasExplicitDockEvidence",
    "STORAGE_KEY",
    "readEnabledPreference",
    "startPreferenceObserver",
    "restoreDockingState",
    "disabled by user",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail(f"invalid PNG file: {path.relative_to(ROOT)}")
    return struct.unpack(">II", data[16:24])


def check_javascript(path: Path) -> None:
    try:
        subprocess.run(["node", "--check", str(path)], check=True)
    except FileNotFoundError:
        fail("node is required to syntax-check JavaScript")
    except subprocess.CalledProcessError as exc:
        fail(f"{path.name} syntax check failed with exit code {exc.returncode}")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    content_source = CONTENT.read_text(encoding="utf-8")
    popup_source = POPUP_JS.read_text(encoding="utf-8")
    combined_source = content_source + "\n" + popup_source

    if manifest.get("manifest_version") != 3:
        fail("manifest_version must be 3")

    version = manifest.get("version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"version must be x.y.z, got {version!r}")

    present_forbidden = FORBIDDEN_MANIFEST_KEYS.intersection(manifest)
    if present_forbidden:
        fail(f"forbidden manifest keys present: {sorted(present_forbidden)}")

    if manifest.get("permissions") != EXPECTED_PERMISSIONS:
        fail(f"permissions must be exactly {EXPECTED_PERMISSIONS}")

    action = manifest.get("action")
    if not isinstance(action, dict):
        fail("manifest action is required for the on/off popup")
    if action.get("default_popup") != EXPECTED_POPUP:
        fail(f"action.default_popup must be {EXPECTED_POPUP!r}")
    unexpected_action_keys = set(action) - {"default_title", "default_popup"}
    if unexpected_action_keys:
        fail(f"unexpected action keys: {sorted(unexpected_action_keys)}")

    scripts = manifest.get("content_scripts")
    if not isinstance(scripts, list) or len(scripts) != 1:
        fail("expected exactly one content_scripts entry")

    script = scripts[0]
    matches = set(script.get("matches", []))
    if matches != EXPECTED_MATCHES:
        missing = sorted(EXPECTED_MATCHES - matches)
        extra = sorted(matches - EXPECTED_MATCHES)
        fail(f"Amazon host scope mismatch; missing={missing}, extra={extra}")

    if any(not item.startswith("https://") for item in matches):
        fail("all match patterns must use HTTPS")
    if any("*.*amazon" in item or "://*" in item for item in matches):
        fail("wildcard Amazon subdomains are not allowed")

    if script.get("js") != ["content.js"]:
        fail("content script must load only content.js")
    if script.get("run_at") != "document_start":
        fail("content script must run at document_start")
    if script.get("all_frames") is not False:
        fail("all_frames must be false")
    if script.get("world") != "ISOLATED":
        fail("content script must run in ISOLATED world")

    icons = manifest.get("icons")
    if icons != EXPECTED_ICONS:
        fail(f"manifest icons must exactly match {EXPECTED_ICONS}")

    for size_text, relative in EXPECTED_ICONS.items():
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing extension icon: {relative}")
        expected = int(size_text)
        width, height = png_dimensions(path)
        if (width, height) != (expected, expected):
            fail(f"{relative} must be {expected}x{expected}, got {width}x{height}")

    for runtime_file in (POPUP_HTML, POPUP_JS, POPUP_CSS):
        if not runtime_file.is_file():
            fail(f"missing popup runtime file: {runtime_file.name}")

    popup_html = POPUP_HTML.read_text(encoding="utf-8")
    if '<script src="popup.js"></script>' not in popup_html:
        fail("popup.html must load popup.js as an external script")
    if '<link rel="stylesheet" href="popup.css">' not in popup_html:
        fail("popup.html must load popup.css")
    if re.search(r"<script(?![^>]*\bsrc=)[^>]*>", popup_html, flags=re.I):
        fail("inline popup scripts are not allowed")
    if re.search(r"(?:src|href)=[\"']https?://", popup_html, flags=re.I):
        fail("popup must not load remote assets")

    for label, pattern in FORBIDDEN_SOURCE_PATTERNS.items():
        if re.search(pattern, combined_source):
            fail(f"forbidden source capability detected: {label}")

    if re.search(r"\bchrome\s*\.(?!storage\b)", combined_source):
        fail("Chrome APIs other than chrome.storage are not allowed")
    if re.search(r"\bchrome\.storage\.(?:sync|managed|session)\b", combined_source):
        fail("only chrome.storage.local plus storage change events are allowed")

    if "chrome.storage.local.get" not in combined_source:
        fail("toggle must read its local enabled preference")
    if "chrome.storage.local.set" not in popup_source:
        fail("popup must write its local enabled preference")
    if "chrome.storage.onChanged.addListener" not in content_source:
        fail("content script must react to preference changes immediately")

    for marker in REQUIRED_SOURCE_MARKERS:
        if marker not in content_source:
            fail(f"required hardening marker missing: {marker}")

    static_block = re.search(
        r"const STATIC_SAFE_SELECTORS = Object\.freeze\(\[(.*?)\]\);",
        content_source,
        flags=re.S,
    )
    if not static_block:
        fail("could not locate STATIC_SAFE_SELECTORS")
    for selector in (".rufus-container", ".rufus-container-main-view", ".rufus-sidebar", ".rufus-panel", ".rufus-wrapper"):
        if re.search(rf"['\"]{re.escape(selector)}['\"]", static_block.group(1)):
            fail(f"broad selector leaked into unconditional CSS: {selector}")

    check_javascript(CONTENT)
    check_javascript(POPUP_JS)

    print(
        f"PASS: Manifest v3 scope, storage-only toggle permission, popup assets, "
        f"icons, and JavaScript security checks ({version})"
    )


if __name__ == "__main__":
    main()
