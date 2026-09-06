#!/usr/bin/env python3
from __future__ import annotations

import asyncio

from playwright.async_api import Browser, Page, async_playwright

from browser_smoke import computed, find_browser, new_page


BASE_HTML = (
    '<html><head></head><body class="rufus-docked-left" '
    'style="padding-left:320px; --total-rufus-panel-full-width:320px">'
    '<main id="normal">normal content</main>'
    '<div id="candidate" class="rufus-panel" '
    'style="display:flex; width:123px; opacity:.7">rufus</div>'
    '</body></html>'
)


async def set_enabled(page: Page, enabled: bool) -> None:
    await page.evaluate("enabled => chrome.storage.local.set({ enabled })", enabled)


async def broadcast_enabled(pages: list[Page], enabled: bool) -> None:
    for page in pages:
        await set_enabled(page, enabled)


async def body_state(page: Page) -> dict:
    return await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, pad: element.style.paddingLeft, "
        "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )


async def assert_suppressed(page: Page) -> None:
    assert await computed(page, "#candidate", "display") == "none"
    assert await computed(page, "#normal", "display") == "block"
    state = await body_state(page)
    assert "rufus-docked-left" not in state["cls"]
    assert state["pad"] == ""
    assert state["prop"] == ""
    assert await page.locator("#aas-soft-hide-style").count() == 1
    assert await page.locator("#aas-hard-hide-style").count() == 1


async def assert_restored(page: Page, display: str = "flex", width_prefix: str = "123") -> None:
    assert await computed(page, "#candidate", "display") == display
    assert (await computed(page, "#candidate", "width")).startswith(width_prefix)
    assert await computed(page, "#normal", "display") == "block"
    assert await page.locator('style[id^="aas-"]').count() == 0
    state = await body_state(page)
    assert "rufus-docked-left" in state["cls"]
    assert state["pad"] == "320px"
    assert state["prop"] == "320px"


async def assert_rapid_toggle_storm(browser: Browser) -> None:
    page = await new_page(browser, BASE_HTML, "/dp/example", storage_enabled=True)
    await page.wait_for_timeout(140)
    await assert_suppressed(page)

    # Hammer the preference much faster than the production fallback interval.
    await page.evaluate(
        """
        async () => {
          for (let i = 0; i < 60; i += 1) {
            await chrome.storage.local.set({ enabled: i % 2 === 0 });
          }
          await chrome.storage.local.set({ enabled: false });
        }
        """
    )
    await page.wait_for_timeout(100)
    await assert_restored(page)

    await page.evaluate(
        """
        async () => {
          for (let i = 0; i < 60; i += 1) {
            await chrome.storage.local.set({ enabled: i % 2 !== 0 });
          }
          await chrome.storage.local.set({ enabled: true });
        }
        """
    )
    await page.wait_for_timeout(160)
    await assert_suppressed(page)
    await page.close()


async def assert_multiple_open_tabs(browser: Browser) -> None:
    page_a = await new_page(browser, BASE_HTML, "/dp/a", storage_enabled=True)
    page_b = await new_page(browser, BASE_HTML.replace("normal content", "second tab"), "/dp/b", storage_enabled=True)
    pages = [page_a, page_b]
    await page_a.wait_for_timeout(150)
    await assert_suppressed(page_a)
    await assert_suppressed(page_b)

    # This mirrors chrome.storage.onChanged being delivered to every open tab.
    await broadcast_enabled(pages, False)
    await page_a.wait_for_timeout(80)
    await assert_restored(page_a)
    await assert_restored(page_b)

    await broadcast_enabled(pages, True)
    await page_a.wait_for_timeout(160)
    await assert_suppressed(page_a)
    await assert_suppressed(page_b)

    await page_a.close()
    await page_b.close()


async def assert_checkout_toggle_interleaving(browser: Browser) -> None:
    page = await new_page(browser, BASE_HTML, "/dp/example", storage_enabled=True)
    await page.wait_for_timeout(140)
    await assert_suppressed(page)

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/checkout/pay'; "
        "window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(60)
    await assert_restored(page)

    # Toggle repeatedly while transaction-sensitive UI is active. Even a final
    # saved On state must not reactivate suppression until the route is safe.
    for enabled in (False, True, False, True, False, True):
        await set_enabled(page, enabled)
    await page.wait_for_timeout(120)
    await assert_restored(page)

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/dp/example'; "
        "window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(160)
    await assert_suppressed(page)

    # Repeat with final state Off: returning to a safe page must stay untouched.
    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/hz/returns/start'; "
        "window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(60)
    await assert_restored(page)
    await set_enabled(page, False)
    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/dp/example'; "
        "window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(160)
    await assert_restored(page)
    await page.close()


async def assert_style_rewrite_during_toggle(browser: Browser) -> None:
    page = await new_page(browser, BASE_HTML, "/dp/example", storage_enabled=True)
    await page.wait_for_timeout(140)
    await assert_suppressed(page)

    # Amazon repeatedly fights the managed style while suppression is active.
    for _ in range(12):
        await page.eval_on_selector(
            "#candidate",
            "element => { element.style.setProperty('display', 'block', 'important'); "
            "element.style.setProperty('opacity', '1', 'important'); }",
        )
        await page.wait_for_timeout(15)
        assert await computed(page, "#candidate", "display") == "none"

    # Turning Off must restore the pre-suppression values, not Amazon's attempts
    # to overwrite the extension-managed values while it was active.
    await set_enabled(page, False)
    await page.wait_for_timeout(80)
    await assert_restored(page)
    assert await computed(page, "#candidate", "opacity") == "0.7"

    # Amazon is now free to establish a new baseline while the extension is Off.
    await page.eval_on_selector(
        "#candidate",
        "element => { element.style.setProperty('display', 'grid'); "
        "element.style.setProperty('width', '222px'); "
        "element.style.setProperty('opacity', '.4'); }",
    )
    await set_enabled(page, True)
    await page.wait_for_timeout(150)
    await assert_suppressed(page)

    # Fight the new suppression again, then disable. The new Off-state baseline
    # must be restored exactly rather than the old 123px/flex baseline.
    await page.eval_on_selector(
        "#candidate",
        "element => element.style.setProperty('display', 'block', 'important')",
    )
    await page.wait_for_timeout(40)
    assert await computed(page, "#candidate", "display") == "none"
    await set_enabled(page, False)
    await page.wait_for_timeout(80)
    assert await computed(page, "#candidate", "display") == "grid"
    assert (await computed(page, "#candidate", "width")).startswith("222")
    assert await computed(page, "#candidate", "opacity") == "0.4"
    await page.close()


async def assert_long_lived_mutation_churn(browser: Browser) -> None:
    page = await new_page(browser, BASE_HTML, "/dp/example", storage_enabled=True)
    await page.wait_for_timeout(140)
    await assert_suppressed(page)

    # Run many accelerated fallback/observer cycles while Amazon-like code keeps
    # injecting/replacing Rufus panels and occasionally reasserting dock state.
    for index in range(40):
        await page.evaluate(
            """
            index => {
              const previous = document.querySelector('[data-dynamic-rufus]');
              if (previous) previous.remove();
              const node = document.createElement('div');
              node.dataset.dynamicRufus = String(index);
              node.className = 'rufus-panel';
              node.style.cssText = `display:flex;width:${140 + index}px;opacity:.8`;
              node.textContent = `dynamic-${index}`;
              document.body.appendChild(node);
              if (index % 5 === 0) {
                document.body.classList.add('rufus-docked-left');
                document.body.style.setProperty('padding-left', '340px');
                document.body.style.setProperty('--total-rufus-panel-full-width', '340px');
              }
            }
            """,
            index,
        )
        await page.wait_for_timeout(25)
        assert await computed(page, '[data-dynamic-rufus]', 'display') == "none"
        assert await computed(page, "#normal", "display") == "block"

    # Let another group of fallback scans run and verify state does not drift,
    # duplicate styles, or resurrect the sidecar gutter.
    await page.wait_for_timeout(750)
    assert await computed(page, '[data-dynamic-rufus]', 'display') == "none"
    await assert_suppressed(page)
    assert await page.locator('[id="aas-soft-hide-style"]').count() == 1
    assert await page.locator('[id="aas-hard-hide-style"]').count() == 1
    await page.close()


async def run() -> None:
    browser_path = find_browser()
    checks = [
        ("rapid On/Off toggle storm converges cleanly", assert_rapid_toggle_storm),
        ("multiple already-open tabs follow toggle state", assert_multiple_open_tabs),
        ("checkout/returns remain inert during toggle changes", assert_checkout_toggle_interleaving),
        ("Amazon style rewrites remain reversible across toggles", assert_style_rewrite_during_toggle),
        ("long-lived mutation/fallback churn stays stable", assert_long_lived_mutation_churn),
    ]

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=browser_path, headless=True)
        try:
            for label, check in checks:
                await check(browser)
                print(f"PASS: {label}")
        finally:
            await browser.close()

    print(f"PASS: {len(checks)} adversarial Chromium regression checks")


if __name__ == "__main__":
    asyncio.run(run())
