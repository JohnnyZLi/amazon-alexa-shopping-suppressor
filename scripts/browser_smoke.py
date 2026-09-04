#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content.js"

# Execute the production content script inside a real Chromium DOM, but shorten
# timers and inject a test-only pathname hook so CI does not wait for production
# safety windows. The runtime source shipped in the extension is never modified.
SOURCE = CONTENT.read_text(encoding="utf-8")
SOURCE = (
    SOURCE.replace("INIT_POLL_MS: 100", "INIT_POLL_MS: 10")
    .replace("MIN_SOFT_HIDE_MS: 3000", "MIN_SOFT_HIDE_MS: 30")
    .replace("MAX_SOFT_HIDE_MS: 8000", "MAX_SOFT_HIDE_MS: 80")
    .replace("FALLBACK_SCAN_MS: 5000", "FALLBACK_SCAN_MS: 50")
    .replace("SCAN_DEBOUNCE_MS: 80", "SCAN_DEBOUNCE_MS: 5")
    .replace(
        "const path = String(location.pathname || '/');",
        "const path = String(window.__AAS_TEST_PATH__ || location.pathname || '/');",
    )
)

EXPECTED_REPLACEMENTS = {
    "INIT_POLL_MS: 10",
    "MIN_SOFT_HIDE_MS: 30",
    "MAX_SOFT_HIDE_MS: 80",
    "FALLBACK_SCAN_MS: 50",
    "SCAN_DEBOUNCE_MS: 5",
    "window.__AAS_TEST_PATH__ || location.pathname",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def find_browser() -> str:
    for candidate in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        path = shutil.which(candidate)
        if path:
            return path
    fail("Chromium/Chrome executable not found")
    raise AssertionError("unreachable")


async def new_page(browser: Browser, html: str, path: str = "/") -> Page:
    page = await browser.new_page()
    await page.set_content(html)
    await page.evaluate("path => { window.__AAS_TEST_PATH__ = path; }", path)
    await page.add_script_tag(content=SOURCE)
    return page


async def computed(page: Page, selector: str, prop: str) -> str:
    return await page.eval_on_selector(
        selector,
        "(element, prop) => getComputedStyle(element).getPropertyValue(prop)",
        prop,
    )


async def assert_static_suppression(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body><div id="nav-rufus-disco">rufus</div><div id="normal">normal</div></body></html>',
    )
    await page.wait_for_timeout(10)
    assert await computed(page, "#nav-rufus-disco", "opacity") == "0"
    assert await computed(page, "#normal", "display") == "block"
    await page.wait_for_timeout(100)
    assert await computed(page, "#nav-rufus-disco", "display") == "none"
    await page.close()


async def assert_guarded_candidate_and_shell_protection(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body><div id="candidate" class="rufus-panel" style="display:block">x</div>'
        '<div id="search" class="rufus-panel" style="display:block">search</div></body></html>',
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    assert await computed(page, "#search", "display") == "block"
    await page.close()


async def assert_dynamic_identity_restoration(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body><div id="candidate" class="rufus-panel" '
        'style="display:flex; width:123px; opacity:.7">x</div></body></html>',
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    await page.eval_on_selector("#candidate", "element => { element.className = 'ordinary-widget'; }")
    await page.wait_for_timeout(80)
    assert await computed(page, "#candidate", "display") == "flex"
    assert (await computed(page, "#candidate", "width")).startswith("123")
    await page.close()


async def assert_style_rewrite_resuppression(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body><div id="candidate" class="rufus-panel" style="display:block">x</div></body></html>',
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    await page.eval_on_selector(
        "#candidate",
        "element => element.style.setProperty('display', 'block', 'important')",
    )
    await page.wait_for_timeout(80)
    assert await computed(page, "#candidate", "display") == "none"
    await page.close()


async def assert_explicit_dock_repair(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body class="rufus-docked-left" '
        'style="padding-left:320px; --total-rufus-panel-full-width:320px"><div>page</div></body></html>',
    )
    await page.wait_for_timeout(40)
    state = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, pad: element.style.paddingLeft, "
        "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )
    assert "rufus-docked-left" not in state["cls"]
    assert state["pad"] == ""
    assert state["prop"] == ""
    await page.close()


async def assert_unrelated_padding_preserved(browser: Browser) -> None:
    page = await new_page(
        browser,
        '<html><head></head><body style="padding-left:320px"><div class="rufus-sidebar">candidate</div>'
        '<div>page</div></body></html>',
    )
    await page.wait_for_timeout(130)
    assert await page.eval_on_selector("body", "element => element.style.paddingLeft") == "320px"
    await page.close()


async def assert_sensitive_routes_inactive(browser: Browser) -> None:
    sensitive = [
        "/gp/buy/spc/handlers/display.html",
        "/checkout/pay",
        "/hz/checkout/init",
        "/spr/returns/start",
        "/hz/returns/label",
        "/gp/your-account/returns/home",
    ]
    for path in sensitive:
        page = await new_page(
            browser,
            '<html><head></head><body><div id="candidate" class="rufus-panel" style="display:flex">x</div></body></html>',
            path,
        )
        await page.wait_for_timeout(130)
        assert await computed(page, "#candidate", "display") == "flex", path
        assert await page.locator('style[id^="aas-"]').count() == 0, path
        await page.close()


async def assert_sensitive_transition_restore_and_resume(browser: Browser) -> None:
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


async def run() -> None:
    missing = sorted(item for item in EXPECTED_REPLACEMENTS if item not in SOURCE)
    if missing:
        fail(f"test instrumentation no longer matches content.js: {missing}")

    browser_path = find_browser()
    checks = [
        ("static soft/hard suppression", assert_static_suppression),
        ("guarded candidate + shell protection", assert_guarded_candidate_and_shell_protection),
        ("dynamic identity restoration", assert_dynamic_identity_restoration),
        ("style rewrite re-suppression", assert_style_rewrite_resuppression),
        ("explicit dock repair", assert_explicit_dock_repair),
        ("unrelated body padding preservation", assert_unrelated_padding_preserved),
        ("sensitive-route inactivity", assert_sensitive_routes_inactive),
        ("safe/sensitive transition restore + resume", assert_sensitive_transition_restore_and_resume),
    ]

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=browser_path, headless=True)
        try:
            for label, check in checks:
                await check(browser)
                print(f"PASS: {label}")
        finally:
            await browser.close()

    print(f"PASS: {len(checks)} synthetic Chromium regression checks")


if __name__ == "__main__":
    asyncio.run(run())
