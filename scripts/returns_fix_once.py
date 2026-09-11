from pathlib import Path


def replace_required(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'missing expected text in {path}: {old[:120]!r}')
    p.write_text(text.replace(old, new), encoding='utf-8')


replace_required(
    'content.js',
    '   * - Stay entirely inactive on sensitive checkout/returns flows.\n',
    '   * - Stay entirely inactive on active checkout flows; returns keep normal Rufus suppression.\n',
)
replace_required(
    'content.js',
    "  const SENSITIVE_PATH_PATTERNS = Object.freeze([\n    /^\\/gp\\/buy(?:\\/|$)/i,\n    /^\\/checkout(?:\\/|$)/i,\n    /^\\/hz\\/checkout(?:\\/|$)/i,\n    /^\\/spr\\/returns(?:\\/|$)/i,\n    /^\\/hz\\/returns(?:\\/|$)/i,\n    /^\\/gp\\/your-account\\/returns(?:\\/|$)/i,\n  ]);",
    "  // Only active checkout is fail-open. Returns pages can suffer the same Rufus\n  // dock-gutter bug, so suppression remains active there while selector safety protects\n  // the return workflow itself.\n  const SENSITIVE_PATH_PATTERNS = Object.freeze([\n    /^\\/gp\\/buy(?:\\/|$)/i,\n    /^\\/checkout(?:\\/|$)/i,\n    /^\\/hz\\/checkout(?:\\/|$)/i,\n  ]);",
)

replace_required(
    'scripts/browser_smoke.py',
    '    sensitive = [\n        "/gp/buy/spc/handlers/display.html",\n        "/checkout/pay",\n        "/hz/checkout/init",\n        "/spr/returns/start",\n        "/hz/returns/label",\n        "/gp/your-account/returns/home",\n    ]',
    '    sensitive = [\n        "/gp/buy/spc/handlers/display.html",\n        "/checkout/pay",\n        "/hz/checkout/init",\n    ]',
)

marker = '\n\nasync def assert_post_purchase_confirmation_active(browser: Browser) -> None:\n'
new_test = r'''

async def assert_return_routes_active(browser: Browser) -> None:
    return_paths = [
        "/spr/returns/start",
        "/hz/returns/label",
        "/gp/your-account/returns/home",
    ]
    for path in return_paths:
        page = await new_page(
            browser,
            '<html><head></head><body class="rufus-docked-left" style="padding-left:320px; '
            '--total-rufus-panel-full-width:320px"><main id="return-content">'
            '<h1>Return reason</h1><button id="return-control">Damaged</button></main>'
            '<div id="candidate" class="rufus-panel" style="display:flex; width:123px">rufus</div></body></html>',
            path,
        )
        await page.wait_for_timeout(130)
        assert await computed(page, "#candidate", "display") == "none", path
        assert await computed(page, "#return-content", "display") == "block", path
        assert await computed(page, "#return-control", "display") == "inline-block", path
        assert await page.locator('style[id^="aas-"]').count() >= 1, path
        state = await page.eval_on_selector(
            "body",
            "element => ({cls: element.className, pad: element.style.paddingLeft, "
            "prop: element.style.getPropertyValue('--total-rufus-panel-full-width')})",
        )
        assert "rufus-docked-left" not in state["cls"], path
        assert state["pad"] == "", path
        assert state["prop"] == "", path
        await page.close()
'''
p = Path('scripts/browser_smoke.py')
text = p.read_text(encoding='utf-8')
if marker not in text:
    raise SystemExit('browser_smoke insertion marker missing')
text = text.replace(marker, new_test + marker, 1)
old_checks = '        ("sensitive-route inactivity", assert_sensitive_routes_inactive),\n        ("post-purchase confirmation resumes suppression", assert_post_purchase_confirmation_active),'
new_checks = '        ("checkout-route inactivity", assert_sensitive_routes_inactive),\n        ("returns keep suppression + return controls intact", assert_return_routes_active),\n        ("post-purchase confirmation resumes suppression", assert_post_purchase_confirmation_active),'
if old_checks not in text:
    raise SystemExit('browser_smoke check-list marker missing')
text = text.replace(old_checks, new_checks, 1)
p.write_text(text, encoding='utf-8')

replace_required(
    'scripts/adversarial_smoke.py',
    "    # Repeat with final state Off: returning to a safe page must stay untouched.\n    await page.evaluate(\n        \"() => { window.__AAS_TEST_PATH__ = '/hz/returns/start'; \"\n        \"window.dispatchEvent(new PopStateEvent('popstate')); }\"\n    )",
    "    # Repeat with final state Off: returning from checkout to a safe page must stay untouched.\n    await page.evaluate(\n        \"() => { window.__AAS_TEST_PATH__ = '/checkout/review'; \"\n        \"window.dispatchEvent(new PopStateEvent('popstate')); }\"\n    )",
)
replace_required(
    'scripts/adversarial_smoke.py',
    '("checkout/returns remain inert during toggle changes", assert_checkout_toggle_interleaving),',
    '("checkout remains inert during toggle changes", assert_checkout_toggle_interleaving),',
)

for path, old, new in [
    ('PRIVACY.md',
     'The extension is intentionally inactive on recognized Amazon checkout and returns routes. Known post-purchase thank-you/order-confirmation routes are treated as non-sensitive so normal Alexa/Rufus suppression and dock-gutter repair can resume after a transaction has completed.',
     'The extension is intentionally inactive on recognized active Amazon checkout routes. Known post-purchase thank-you/order-confirmation routes and Amazon return-workflow routes use normal Alexa/Rufus suppression so the sidebar gutter can be repaired after purchase and during returns; non-Rufus return controls are left untouched by the extension.'),
    ('README.md',
     '- Checkout and recognized returns routes remain untouched regardless of the toggle state.',
     '- Active checkout routes remain untouched regardless of the toggle state. Return-workflow pages keep normal Rufus suppression so the sidebar gutter is repaired while non-Rufus return controls remain untouched.'),
    ('README.md',
     'The extension intentionally remains inactive when the Amazon path matches a recognized checkout or returns route, including the common `/gp/buy/`, `/checkout/`, `/hz/checkout/`, `/spr/returns/`, `/hz/returns/`, and `/gp/your-account/returns/` families.',
     'The extension intentionally remains inactive when the Amazon path matches a recognized active checkout route, including the common `/gp/buy/`, `/checkout/`, and `/hz/checkout/` families. Return routes are intentionally active because live testing showed Rufus can leave the same large dock gutter inside the Returns workflow.'),
    ('README.md',
     '| Returns — authenticated | ➖ | Suppressor must remain inactive; signed-in acceptance required |',
     '| Returns — authenticated | ⬜ | Rufus suppression/gutter repair active; return controls must remain intact |'),
    ('CHANGELOG.md',
     '- Includes sensitive checkout/returns fail-open behavior and restoration across same-document navigation.',
     '- Keeps active checkout fail-open behavior and restoration across same-document navigation. Return workflows remain suppressor-active so Rufus and its blank dock gutter are removed without modifying non-Rufus return controls.'),
]:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old in text:
        p.write_text(text.replace(old, new), encoding='utf-8')
    else:
        print(f'optional documentation replacement not found: {path}: {old[:80]}')

Path('docs/RETURNS_REGRESSION.md').write_text('''# Amazon Returns regression — pre-1.0.0\n\nDuring signed-in Amazon US acceptance, the publisher reproduced the same Rufus dock-gutter failure inside the Returns Center: Alexa for Shopping remained present and the return workflow was shifted by a large blank left gutter.\n\nRoot cause: the pre-release safety policy treated the entire `/spr/returns/`, `/hz/returns/`, and `/gp/your-account/returns/` route families as sensitive and deliberately disabled the suppressor there. That policy prevented the extension from repairing Rufus even though the return controls themselves are unrelated to Rufus.\n\nThe 1.0.0 release line now keeps **active checkout** fail-open/inactive, but allows normal Rufus suppression and dock repair on return-workflow routes. Existing selector/page-shell protections still prevent non-Rufus return controls from being managed.\n\nPermanent Chromium regression coverage verifies all three return-route families with a Rufus panel plus dock gutter present: the Rufus candidate is suppressed, the gutter is repaired, and representative return content/control elements remain visible and usable.\n\nThe signed-in screenshot that exposed this regression contains account/location/order information and is intentionally not committed to the repository.\n''', encoding='utf-8')

print('returns fix patch applied')
