#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{label}: expected source block not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


content = ROOT / "content.js"
replace_once(
    content,
    """  const SENSITIVE_PATH_PATTERNS = Object.freeze([\n    /^\\/gp\\/buy(?:\\/|$)/i,\n    /^\\/checkout(?:\\/|$)/i,\n    /^\\/hz\\/checkout(?:\\/|$)/i,\n    /^\\/spr\\/returns(?:\\/|$)/i,\n    /^\\/hz\\/returns(?:\\/|$)/i,\n    /^\\/gp\\/your-account\\/returns(?:\\/|$)/i,\n  ]);\n""",
    """  // Post-purchase confirmation pages are no longer transaction-sensitive.\n  // They may still host Rufus and can retain the same dock gutter as normal shopping pages.\n  const POST_PURCHASE_SAFE_PATH_PATTERNS = Object.freeze([\n    /^\\/gp\\/buy\\/thankyou(?:\\/|$)/i,\n    /^\\/checkout\\/thankyou(?:\\/|$)/i,\n    /^\\/hz\\/checkout\\/thankyou(?:\\/|$)/i,\n    /^\\/checkout\\/order-confirmation(?:\\/|$)/i,\n    /^\\/hz\\/checkout\\/order-confirmation(?:\\/|$)/i,\n  ]);\n\n  const SENSITIVE_PATH_PATTERNS = Object.freeze([\n    /^\\/gp\\/buy(?:\\/|$)/i,\n    /^\\/checkout(?:\\/|$)/i,\n    /^\\/hz\\/checkout(?:\\/|$)/i,\n    /^\\/spr\\/returns(?:\\/|$)/i,\n    /^\\/hz\\/returns(?:\\/|$)/i,\n    /^\\/gp\\/your-account\\/returns(?:\\/|$)/i,\n  ]);\n""",
    "content.js route policy",
)
replace_once(
    content,
    """  function isSensitiveFlow() {\n    const path = String(location.pathname || '/');\n    return SENSITIVE_PATH_PATTERNS.some((pattern) => pattern.test(path));\n  }\n""",
    """  function isSensitiveFlow() {\n    const path = String(location.pathname || '/');\n    if (POST_PURCHASE_SAFE_PATH_PATTERNS.some((pattern) => pattern.test(path))) return false;\n    return SENSITIVE_PATH_PATTERNS.some((pattern) => pattern.test(path));\n  }\n""",
    "content.js sensitivity function",
)

browser_smoke = ROOT / "scripts" / "browser_smoke.py"
addition = r'''

async def assert_post_purchase_confirmation_active(browser: Browser) -> None:
    confirmation_paths = [
        "/gp/buy/thankyou/handlers/display.html",
        "/checkout/thankyou",
        "/hz/checkout/thankyou",
        "/checkout/order-confirmation",
        "/hz/checkout/order-confirmation",
    ]
    for path in confirmation_paths:
        page = await new_page(
            browser,
            '<html><head></head><body class="rufus-docked-left" style="padding-left:320px; '
            '--total-rufus-panel-full-width:320px"><div id="candidate" class="rufus-panel" '
            'style="display:flex; width:123px">x</div></body></html>',
            path,
        )
        await page.wait_for_timeout(130)
        assert await computed(page, "#candidate", "display") == "none", path
        state = await page.eval_on_selector(
            "body",
            "element => ({cls: element.className, pad: element.style.paddingLeft, "
            "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
        )
        assert "rufus-docked-left" not in state["cls"], path
        assert state["pad"] == "", path
        assert state["prop"] == "", path
        await page.close()

    page = await new_page(
        browser,
        '<html><head></head><body class="rufus-docked-left" style="padding-left:320px; '
        '--total-rufus-panel-full-width:320px"><div id="candidate" class="rufus-panel" '
        'style="display:flex; width:123px">x</div></body></html>',
        "/checkout/pay",
    )
    await page.wait_for_timeout(80)
    assert await computed(page, "#candidate", "display") == "flex"
    assert await page.locator('style[id^="aas-"]').count() == 0

    await page.evaluate(
        "() => { window.__AAS_TEST_PATH__ = '/gp/buy/thankyou/handlers/display.html'; "
        "window.dispatchEvent(new PopStateEvent('popstate')); }"
    )
    await page.wait_for_timeout(130)
    assert await computed(page, "#candidate", "display") == "none"
    resumed = await page.eval_on_selector(
        "body",
        "element => ({cls: element.className, pad: element.style.paddingLeft, "
        "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
    )
    assert "rufus-docked-left" not in resumed["cls"]
    assert resumed["pad"] == ""
    assert resumed["prop"] == ""
    await page.close()
'''
replace_once(
    browser_smoke,
    "\n\nasync def assert_sensitive_transition_restore_and_resume(browser: Browser) -> None:\n",
    addition + "\n\nasync def assert_sensitive_transition_restore_and_resume(browser: Browser) -> None:\n",
    "browser_smoke post-purchase test insertion",
)
replace_once(
    browser_smoke,
    '        ("sensitive-route inactivity", assert_sensitive_routes_inactive),\n',
    '        ("sensitive-route inactivity", assert_sensitive_routes_inactive),\n'
    '        ("post-purchase confirmation resumes suppression", assert_post_purchase_confirmation_active),\n',
    "browser_smoke check registration",
)

validate = ROOT / "scripts" / "validate.py"
replace_once(
    validate,
    '    "SENSITIVE_PATH_PATTERNS",\n',
    '    "SENSITIVE_PATH_PATTERNS",\n    "POST_PURCHASE_SAFE_PATH_PATTERNS",\n',
    "validator marker",
)

changelog = ROOT / "CHANGELOG.md"
replace_once(
    changelog,
    "- Includes sensitive checkout/returns fail-open behavior and restoration across same-document navigation.\n",
    "- Includes sensitive checkout/returns fail-open behavior and restoration across same-document navigation.\n"
    "- Fixes the post-purchase order-confirmation regression: known thank-you/order-confirmation routes resume Rufus suppression and dock-gutter repair after payment while active checkout remains untouched.\n",
    "changelog",
)

readme = ROOT / "README.md"
replace_once(
    readme,
    "The safeguard favors false negatives over modifying transaction-sensitive pages.\n",
    "The safeguard favors false negatives over modifying transaction-sensitive pages.\n\n"
    "Post-purchase thank-you/order-confirmation routes are explicitly treated as non-sensitive so Rufus suppression and dock-gutter repair resume after an order is already placed.\n",
    "README",
)

print("Patched order-confirmation routing, regression coverage, validation marker, and docs.")
