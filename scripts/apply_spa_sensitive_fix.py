#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "content.js",
    "        deactivate('sensitive flow detected');",
    "        deactivate('sensitive flow detected', true);",
)
replace_once(
    "content.js",
    "      deactivate(`${eventName}: sensitive flow`);",
    "      deactivate(`${eventName}: sensitive flow`, true);",
)
replace_once(
    "content.js",
    "    window.addEventListener('popstate', () => onNavigationSignal('popstate'));",
    """    window.addEventListener('popstate', () => onNavigationSignal('popstate'));
    if (window.navigation && typeof window.navigation.addEventListener === 'function') {
      window.navigation.addEventListener('currententrychange', () => onNavigationSignal('navigation'));
    }""",
)
replace_once(
    "content.js",
    "    try { deactivate('fatal initialization error'); } catch { /* best effort */ }",
    "    try { deactivate('fatal initialization error', true); } catch { /* best effort */ }",
)

old_transition = '''async def assert_sensitive_transition_restore_and_resume(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body><div id="candidate" class="rufus-panel" '
        'style="display:flex; width:123px">x</div></body></html>',
        "/dp/example",
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/checkout/pay'; window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(40)
    assert await computed(page, "#candidate", "display") == "flex"
    assert (await computed(page, "#candidate", "width")).startswith("123")
    assert await page.locator('style[id^="aas-"]').count() == 0

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/dp/example'; window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    assert await page.locator('style[id^="aas-"]').count() >= 1
    await page.close()
'''

new_transition = '''async def assert_sensitive_transition_restore_and_resume(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body class="rufus-docked-left" style="padding-left:320px; '
        '--total-rufus-panel-full-width:320px"><div id="candidate" class="rufus-panel" '
        'style="display:flex; width:123px">x</div></body></html>',
        "/dp/example",
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    assert "rufus-docked-left" not in await page.eval_on_selector("body", "element => element.className")

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/checkout/pay'; window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(40)
    assert await computed(page, "#candidate", "display") == "flex"
    assert (await computed(page, "#candidate", "width")).startswith("123")
    assert await page.locator('style[id^="aas-"]').count() == 0
    restored = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, pad: element.style.paddingLeft, "
        "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )
    assert "rufus-docked-left" in restored["cls"]
    assert restored["pad"] == "320px"
    assert restored["prop"] == "320px"

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/dp/example'; window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    assert await page.locator('style[id^="aas-"]').count() >= 1
    repaired = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, pad: element.style.paddingLeft, "
        "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )
    assert "rufus-docked-left" not in repaired["cls"]
    assert repaired["pad"] == ""
    assert repaired["prop"] == ""
    await page.close()


async def assert_navigation_api_sensitive_transition(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body class="rufus-docked-left" style="padding-left:320px; '
        '--total-rufus-panel-full-width:320px"><div id="candidate" class="rufus-panel" '
        'style="display:flex; width:123px">x</div></body></html>',
        "/dp/example",
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    assert await page.evaluate("() => Boolean(window.navigation && window.navigation.dispatchEvent)")

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/checkout/pay'; "
        "window.navigation.dispatchEvent(new Event('currententrychange')); }"
    )
    await page.wait_for_timeout(40)
    assert await computed(page, "#candidate", "display") == "flex"
    restored = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, pad: element.style.paddingLeft, "
        "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )
    assert "rufus-docked-left" in restored["cls"]
    assert restored["pad"] == "320px"
    assert restored["prop"] == "320px"

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/dp/example'; "
        "window.navigation.dispatchEvent(new Event('currententrychange')); }"
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    repaired = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, pad: element.style.paddingLeft, "
        "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )
    assert "rufus-docked-left" not in repaired["cls"]
    assert repaired["pad"] == ""
    assert repaired["prop"] == ""
    await page.close()
'''
replace_once("scripts/browser_smoke.py", old_transition, new_transition)
replace_once(
    "scripts/browser_smoke.py",
    '        ("safe/sensitive transition restore + resume", assert_sensitive_transition_restore_and_resume),\n',
    '        ("safe/sensitive transition restore + resume", assert_sensitive_transition_restore_and_resume),\n'
    '        ("Navigation API same-document sensitive transition", assert_navigation_api_sensitive_transition),\n',
)
replace_once(
    "scripts/validate.py",
    '    "disabled by user",\n',
    '    "disabled by user",\n    "currententrychange",\n',
)

manifest_path = Path("manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("version") != "0.3.1":
    raise SystemExit(f"unexpected manifest version: {manifest.get('version')!r}")
manifest["version"] = "0.3.2"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

changelog = Path("CHANGELOG.md")
text = changelog.read_text(encoding="utf-8")
marker = "# Changelog\n\n"
if not text.startswith(marker):
    raise SystemExit("unexpected CHANGELOG header")
entry = '''## 0.3.2 — 2026-09-06

Sensitive-flow restoration and same-document navigation hardening.

- Restores recorded Rufus dock classes, width variables, and associated body padding when a running suppressor transitions into checkout or returns instead of leaving layout changes behind.
- Restores dock state on fatal deactivation as part of the fail-open path.
- Watches Chromium's Navigation API `currententrychange` event so `history.pushState()` / `replaceState()` transitions into sensitive routes deactivate immediately and transitions back to normal Amazon pages resume suppression without a reload.
- Strengthened synthetic Chromium coverage to assert dock restoration/resuppression across both `popstate` and Navigation API same-document transitions.
- Independently exercised all 46 exact bare/www Amazon HTTPS host patterns with the real unpacked extension; unlisted hosts remained untouched.

'''
changelog.write_text(marker + entry + text[len(marker):], encoding="utf-8")

for doc in ("README.md", "docs/TEST_PLAN.md"):
    p = Path(doc)
    t = p.read_text(encoding="utf-8")
    if "0.3.1" not in t:
        raise SystemExit(f"{doc}: expected 0.3.1 reference")
    p.write_text(t.replace("0.3.1", "0.3.2"), encoding="utf-8")

replace_once(
    "docs/STORE_SUBMISSION.md",
    "- [x] Recognized checkout/returns routes are intentionally inactive\n",
    "- [x] Recognized checkout/returns routes are intentionally inactive\n"
    "- [x] Sensitive-route deactivation restores recorded Rufus dock state\n"
    "- [x] Same-document pushState/replaceState route changes are observed through the Chromium Navigation API\n",
)
