#!/usr/bin/env python3
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
    """    // Treat each newly observed explicit Rufus dock state as authoritative.
    // Amazon can switch docking sides or width modes while suppression is active;
    // retaining every previously removed class/style would restore contradictory
    // stale states when the user turns the suppressor Off.
    if (hasExplicitDockEvidence) clearDockingState();

    let changed = false;
""",
    """    prepareDockingSnapshot(body, hasExplicitDockEvidence);

    let changed = false;
""",
)
replace_once(
    "content.js",
    """  function repairDocking() {
""",
    """  function getRecordedDockSide() {
    const left = removedDockClasses.has('rufus-docked-left') || removedDockStyles.has('padding-left');
    const right = removedDockClasses.has('rufus-docked-right') || removedDockStyles.has('padding-right');
    if (left === right) return null;
    return left ? 'left' : 'right';
  }

  function getCurrentDockSide(body, hasExplicitDockEvidence) {
    if (body.classList.contains('rufus-docked-left')) return 'left';
    if (body.classList.contains('rufus-docked-right')) return 'right';
    if (!hasExplicitDockEvidence) return null;
    const left = isLargeDockPadding(body.style.getPropertyValue('padding-left'));
    const right = isLargeDockPadding(body.style.getPropertyValue('padding-right'));
    if (left === right) return null;
    return left ? 'left' : 'right';
  }

  function prepareDockingSnapshot(body, hasExplicitDockEvidence) {
    if (!hasExplicitDockEvidence) return;

    const currentSide = getCurrentDockSide(body, hasExplicitDockEvidence);
    const recordedSide = getRecordedDockSide();
    if (currentSide && recordedSide && currentSide !== recordedSide) clearDockingState();

    const hasLeftClass = body.classList.contains('rufus-docked-left');
    const hasRightClass = body.classList.contains('rufus-docked-right');
    if (hasLeftClass || hasRightClass) {
      removedDockClasses.delete('rufus-docked-left');
      removedDockClasses.delete('rufus-docked-right');
    }

    const hasOpening = body.classList.contains('rufus-docked-opening-transition');
    const hasClosing = body.classList.contains('rufus-docked-closing-transition');
    if (hasOpening || hasClosing) {
      removedDockClasses.delete('rufus-docked-opening-transition');
      removedDockClasses.delete('rufus-docked-closing-transition');
    }

    const hasFullWidth = Boolean(body.style.getPropertyValue('--total-rufus-panel-full-width'));
    const hasHalfWidth = Boolean(body.style.getPropertyValue('--total-rufus-panel-half-width'));
    if (hasFullWidth || hasHalfWidth) {
      removedDockStyles.delete('--total-rufus-panel-full-width');
      removedDockStyles.delete('--total-rufus-panel-half-width');
    }

    if (currentSide === 'left') removedDockStyles.delete('padding-right');
    if (currentSide === 'right') removedDockStyles.delete('padding-left');
  }

  function repairDocking() {
""",
)

replace_once(
    "scripts/browser_smoke.py",
    """async def assert_popup_toggle(browser: Browser) -> None:
""",
    """async def assert_partial_dock_update_preserves_compatible_snapshot(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body class="rufus-docked-left" style="padding-left:320px; '
        '--total-rufus-panel-full-width:320px"><div id="candidate" class="rufus-panel" '
        'style="display:flex; width:123px">x</div></body></html>',
        "/dp/example",
        storage_enabled=True,
    )
    await page.wait_for_timeout(130)
    await page.eval_on_selector(
        "body",
        "element => element.style.setProperty('--total-rufus-panel-full-width', '350px')",
    )
    await page.wait_for_timeout(80)
    await page.evaluate("() => chrome.storage.local.set({ enabled: false })")
    await page.wait_for_timeout(50)
    restored = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, left: element.style.paddingLeft, "
        "full: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )
    assert "rufus-docked-left" in restored["cls"]
    assert restored["left"] == "320px"
    assert restored["full"] == "350px"
    await page.close()


async def assert_popup_toggle(browser: Browser) -> None:
""",
)
replace_once(
    "scripts/browser_smoke.py",
    '        ("dynamic dock snapshot replaces stale side", assert_dynamic_dock_snapshot_replacement),\n',
    '        ("dynamic dock snapshot replaces stale side", assert_dynamic_dock_snapshot_replacement),\n'
    '        ("partial dock update preserves compatible snapshot", assert_partial_dock_update_preserves_compatible_snapshot),\n',
)
replace_once(
    "scripts/validate.py",
    '    "if (hasExplicitDockEvidence) clearDockingState();",\n',
    '    "prepareDockingSnapshot",\n    "getRecordedDockSide",\n    "getCurrentDockSide",\n',
)
replace_once(
    "CHANGELOG.md",
    "- Each newly observed explicit Rufus dock state now replaces the previously recorded restoration snapshot instead of accumulating stale, contradictory state.\n- Added a synthetic Chromium regression that switches from a left/full-width dock to a right/half-width dock while active, then verifies Off restores only the latest right-side state.\n",
    "- Newly observed dock evidence now reconciles the restoration snapshot: incompatible side or width-mode state is replaced, while compatible partial updates preserve the rest of the last known dock state.\n- Added synthetic Chromium regressions for both a left/full-width → right/half-width side switch and a width-only update while the same left dock remains logically active.\n",
)
replace_once(
    "docs/STORE_SUBMISSION.md",
    "- [x] Newly observed explicit dock state replaces stale restoration snapshots\n",
    "- [x] Dynamic dock snapshots replace incompatible stale state while preserving compatible partial updates\n",
)
