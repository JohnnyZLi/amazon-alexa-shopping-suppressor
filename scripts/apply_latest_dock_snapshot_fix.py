#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:140]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "content.js",
    """    const hasExplicitDockEvidence = hadDockClass || hadDockProperty;

    let changed = false;
""",
    """    const hasExplicitDockEvidence = hadDockClass || hadDockProperty;

    // Treat each newly observed explicit Rufus dock state as authoritative.
    // Amazon can switch docking sides or width modes while suppression is active;
    // retaining every previously removed class/style would restore contradictory
    // stale states when the user turns the suppressor Off.
    if (hasExplicitDockEvidence) clearDockingState();

    let changed = false;
""",
)

marker = """async def assert_popup_toggle(browser: Browser) -> None:
"""
insert = """async def assert_dynamic_dock_snapshot_replacement(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body class="rufus-docked-left" style="padding-left:320px; '
        '--total-rufus-panel-full-width:320px"><div id="candidate" class="rufus-panel" '
        'style="display:flex; width:123px">x</div></body></html>',
        "/dp/example",
        storage_enabled=True,
    )
    await page.wait_for_timeout(130)
    initial = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, left: element.style.paddingLeft, "
        "full: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )
    assert "rufus-docked-left" not in initial["cls"]
    assert initial["left"] == ""
    assert initial["full"] == ""

    await page.eval_on_selector(
        "body",
        "element => { element.className = 'rufus-docked-right'; "
        "element.style.cssText = 'padding-right:390px; --total-rufus-panel-half-width:390px'; }",
    )
    await page.wait_for_timeout(80)
    repaired = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, right: element.style.paddingRight, "
        "half: element.style.getPropertyValue('--total-rufus-panel-half-width')})",
    )
    assert "rufus-docked-right" not in repaired["cls"]
    assert repaired["right"] == ""
    assert repaired["half"] == ""

    await page.evaluate("() => chrome.storage.local.set({ enabled: false })")
    await page.wait_for_timeout(50)
    restored = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, left: element.style.paddingLeft, "
        "right: element.style.paddingRight, full: element.style.getPropertyValue('--total-rufus-panel-full-width'), "
        "half: element.style.getPropertyValue('--total-rufus-panel-half-width')})",
    )
    assert "rufus-docked-right" in restored["cls"]
    assert "rufus-docked-left" not in restored["cls"]
    assert restored["left"] == ""
    assert restored["right"] == "390px"
    assert restored["full"] == ""
    assert restored["half"] == "390px"
    await page.close()


async def assert_popup_toggle(browser: Browser) -> None:
"""
replace_once("scripts/browser_smoke.py", marker, insert)
replace_once(
    "scripts/browser_smoke.py",
    '        ("live off/on toggle restores + resumes", assert_live_toggle_restore_and_resume),\n',
    '        ("live off/on toggle restores + resumes", assert_live_toggle_restore_and_resume),\n'
    '        ("dynamic dock snapshot replaces stale side", assert_dynamic_dock_snapshot_replacement),\n',
)
replace_once(
    "scripts/validate.py",
    '    "currententrychange",\n',
    '    "currententrychange",\n    "if (hasExplicitDockEvidence) clearDockingState();",\n',
)

manifest_path = Path("manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("version") != "0.3.2":
    raise SystemExit(f"unexpected manifest version: {manifest.get('version')!r}")
manifest["version"] = "0.3.3"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

changelog = Path("CHANGELOG.md")
text = changelog.read_text(encoding="utf-8")
marker = "# Changelog\n\n"
if not text.startswith(marker):
    raise SystemExit("unexpected CHANGELOG header")
entry = '''## 0.3.3 — 2026-09-06

Dynamic dock-state snapshot correction.

- Fixed a real-extension edge case where Amazon switching Rufus from one docking state to another while suppression was active caused Off to restore both the old and new dock classes/styles simultaneously.
- Each newly observed explicit Rufus dock state now replaces the previously recorded restoration snapshot instead of accumulating stale, contradictory state.
- Added a synthetic Chromium regression that switches from a left/full-width dock to a right/half-width dock while active, then verifies Off restores only the latest right-side state.
- Re-ran persistent-profile, multi-tab, sensitive-route, same-document navigation, style-restoration, and repeated-toggle integration tests against the actual unpacked extension.

'''
changelog.write_text(marker + entry + text[len(marker):], encoding="utf-8")

for doc in ("README.md", "docs/TEST_PLAN.md"):
    p = Path(doc)
    t = p.read_text(encoding="utf-8")
    if "0.3.2" not in t:
        raise SystemExit(f"{doc}: expected 0.3.2 reference")
    p.write_text(t.replace("0.3.2", "0.3.3"), encoding="utf-8")

replace_once(
    "README.md",
    "If a browser navigation signal reaches one of these paths in the same document, the extension deactivates, disconnects observers/timers, removes its injected styles, and restores tracked inline styles on managed elements.",
    "If a browser navigation signal reaches one of these paths in the same document, the extension deactivates, disconnects observers/timers, removes its injected styles, restores tracked inline styles on managed elements, and restores the latest recorded Rufus dock state.",
)
replace_once(
    "docs/STORE_SUBMISSION.md",
    "- [x] Dock-padding repair requires explicit Rufus dock evidence\n",
    "- [x] Dock-padding repair requires explicit Rufus dock evidence\n- [x] Newly observed explicit dock state replaces stale restoration snapshots\n",
)
