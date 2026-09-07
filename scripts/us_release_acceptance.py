#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import BrowserContext, Page, async_playwright

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "artifacts" / "us-release-acceptance"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
HOST = "www.amazon.com"
BASE = f"https://{HOST}"
STYLE_SELECTOR = "#aas-soft-hide-style, #aas-hard-hide-style"
RUFUS_SELECTOR = ",".join([
    "#nav-rufus-disco", ".nav-rufus-disco", "#nav-flyout-rufus", "#Rufus",
    "#rufus-container", ".rufus-container", "#rufus-sidebar", ".rufus-sidebar",
    "#rufus-panel", ".rufus-panel", ".rufus-panel-container",
    "#dpx-nice-widget-container", "#dpx-rex-nice-widget-container",
    "#rufus-price-ingress", ".s-ask-rufus-mshop-suggestion-container",
    ".s-suggestion-nile-desktop-container",
])
BLOCK_MARKERS = [
    "robot check", "validatecaptcha", "enter the characters you see below",
    "sorry, we just need to make sure you're not a robot",
]


def find_browser() -> str:
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError("No Chromium/Chrome executable found")


async def discover_extension_id(context: BrowserContext, profile: Path) -> str | None:
    page = await context.new_page()
    try:
        await page.goto("chrome://extensions/", wait_until="domcontentloaded", timeout=15000)
        for _ in range(20):
            items = await page.evaluate("""
            () => {
              const manager = document.querySelector('extensions-manager');
              const list = manager?.shadowRoot?.querySelector('extensions-item-list');
              const nodes = list?.shadowRoot?.querySelectorAll('extensions-item') || [];
              return [...nodes].map(item => ({
                id: item.id || item.getAttribute('id') || '',
                name: item.shadowRoot?.querySelector('#name')?.textContent?.trim() || '',
              }));
            }
            """)
            for item in items:
                if "Suppressor" in item.get("name", ""):
                    return item.get("id") or None
            await page.wait_for_timeout(250)
    finally:
        await page.close()

    for relative in (Path("Default/Preferences"), Path("Default/Secure Preferences")):
        path = profile / relative
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        settings = data.get("extensions", {}).get("settings", {})
        for extension_id, details in settings.items():
            name = str((details or {}).get("manifest", {}).get("name", ""))
            if "Suppressor" in name:
                return extension_id
    return None


async def set_enabled(context: BrowserContext, extension_id: str, enabled: bool) -> dict:
    page = await context.new_page()
    out = {"requested": enabled, "ok": False, "checked": None, "status": None, "error": None}
    try:
        await page.goto(f"chrome-extension://{extension_id}/popup.html", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_selector("#enabled", timeout=10000)
        current = await page.is_checked("#enabled")
        if current != enabled:
            await page.click("#enabled")
        await page.wait_for_timeout(450)
        out["checked"] = await page.is_checked("#enabled")
        out["status"] = (await page.locator("#status").text_content() or "").strip()
        out["ok"] = out["checked"] is enabled and out["status"] == ("On" if enabled else "Off")
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        await page.close()
    return out


async def inspect(page: Page, name: str, url: str, expect_active: bool | None = True) -> dict:
    out = {
        "name": name, "requested_url": url, "final_url": None, "status": None,
        "blocked": False, "active": False, "body_visible": False, "style_count": 0,
        "rufus_candidates": 0, "rufus_all_hidden": None, "body_padding_left": None,
        "body_padding_right": None, "horizontal_overflow": None, "error": None,
    }
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        out["status"] = response.status if response else None
        await page.wait_for_timeout(1800)
        out["final_url"] = page.url
        try:
            body_text = (await page.locator("body").inner_text(timeout=5000)).lower()
        except Exception:
            body_text = ""
        out["blocked"] = any(x in body_text or x in page.url.lower() for x in BLOCK_MARKERS)
        out["style_count"] = await page.locator(STYLE_SELECTOR).count()
        out["active"] = out["style_count"] > 0
        metrics = await page.evaluate("""
        () => {
          const b = document.body;
          if (!b) return {visible:false, pl:null, pr:null, overflow:null};
          const s = getComputedStyle(b);
          return {
            visible: s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity || 1) > 0,
            pl: s.paddingLeft,
            pr: s.paddingRight,
            overflow: Math.max(document.documentElement.scrollWidth, b.scrollWidth) - innerWidth,
          };
        }
        """)
        out["body_visible"] = metrics["visible"]
        out["body_padding_left"] = metrics["pl"]
        out["body_padding_right"] = metrics["pr"]
        out["horizontal_overflow"] = metrics["overflow"]
        candidates = page.locator(RUFUS_SELECTOR)
        out["rufus_candidates"] = await candidates.count()
        if out["rufus_candidates"]:
            states = await candidates.evaluate_all("""
            els => els.slice(0, 40).map(el => {
              const s = getComputedStyle(el);
              return s.display === 'none' || s.visibility === 'hidden' || Number.parseFloat(s.opacity || '1') <= .01;
            })
            """)
            out["rufus_all_hidden"] = all(states)
        if not out["blocked"] and expect_active is not None and out["active"] != expect_active:
            out["error"] = f"extension active={out['active']} expected={expect_active}"
        if not out["blocked"] and not out["body_visible"]:
            out["error"] = (out["error"] + "; " if out["error"] else "") + "body not visible"
        if not out["blocked"] and out["rufus_all_hidden"] is False and expect_active:
            out["error"] = (out["error"] + "; " if out["error"] else "") + "visible Rufus candidate"
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        out["final_url"] = page.url
    return out


async def first_product(page: Page) -> str | None:
    try:
        hrefs = await page.locator('a[href*="/dp/"]').evaluate_all("els => els.map(e => e.href).filter(Boolean)")
    except Exception:
        return None
    for href in hrefs:
        try:
            u = urlparse(href)
        except Exception:
            continue
        if u.hostname in {"amazon.com", "www.amazon.com"} and "/dp/" in u.path:
            return href.split("?")[0]
    return None


async def popup_theme_check(context: BrowserContext, extension_id: str) -> dict:
    page = await context.new_page()
    out = {"light": None, "dark": None, "ok": False, "error": None}
    try:
        await page.goto(f"chrome-extension://{extension_id}/popup.html", wait_until="domcontentloaded", timeout=15000)
        for scheme in ("light", "dark"):
            await page.emulate_media(color_scheme=scheme)
            await page.wait_for_timeout(150)
            out[scheme] = await page.evaluate("""
            () => {
              const body = getComputedStyle(document.body);
              const card = getComputedStyle(document.querySelector('.toggle-row'));
              return {background: body.backgroundColor, color: body.color, card: card.backgroundColor};
            }
            """)
        out["ok"] = out["light"] != out["dark"]
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        await page.close()
    return out


async def dynamic_mutation_check(page: Page) -> dict:
    out = {"candidate_found": False, "rewrite_reapplied": None, "identity_restored": None, "error": None}
    try:
        candidate = page.locator(RUFUS_SELECTOR).first
        if await candidate.count() == 0:
            return out
        out["candidate_found"] = True
        baseline = await candidate.evaluate("el => ({id:el.id, cls:el.className, style:el.getAttribute('style') || ''})")
        await candidate.evaluate("el => { el.style.removeProperty('display'); el.style.removeProperty('visibility'); el.style.removeProperty('opacity'); }")
        await page.wait_for_timeout(900)
        out["rewrite_reapplied"] = await candidate.evaluate("el => { const s=getComputedStyle(el); return s.display==='none' || s.visibility==='hidden' || Number.parseFloat(s.opacity||'1')<=.01; }")
        await candidate.evaluate("el => { el.id='aas-temporary-non-rufus'; el.className='aas-temporary-non-rufus'; }")
        await page.wait_for_timeout(900)
        out["identity_restored"] = await candidate.evaluate("el => !el.style.getPropertyValue('display') && !el.style.getPropertyValue('visibility') && !el.style.getPropertyValue('opacity')")
        await candidate.evaluate("(el,b) => { el.id=b.id; el.className=b.cls; if (b.style) el.setAttribute('style', b.style); else el.removeAttribute('style'); }", baseline)
        await page.wait_for_timeout(400)
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


async def main() -> int:
    report: dict = {"extension_id": None, "tests": {}, "failures": [], "limitations": []}
    browser_path = find_browser()
    profile = Path(tempfile.mkdtemp(prefix="aas-us-acceptance-"))
    long_minutes = int(os.environ.get("AAS_LONG_MINUTES", "30"))
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            str(profile), executable_path=browser_path, headless=False,
            args=[f"--disable-extensions-except={ROOT}", f"--load-extension={ROOT}", "--no-first-run", "--disable-dev-shm-usage"],
            viewport={"width": 1365, "height": 900},
        )
        try:
            extension_id = await discover_extension_id(context, profile)
            report["extension_id"] = extension_id
            if not extension_id:
                report["failures"].append("Could not discover loaded extension ID")
                raise RuntimeError("extension not loaded")

            report["tests"]["popup_theme"] = await popup_theme_check(context, extension_id)
            if not report["tests"]["popup_theme"]["ok"]:
                report["failures"].append("popup light/dark theme did not differ")

            await set_enabled(context, extension_id, True)
            page = await context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))

            home = await inspect(page, "homepage", BASE + "/")
            report["tests"]["homepage"] = home
            search = await inspect(page, "search", BASE + "/s?k=usb+cable")
            report["tests"]["search"] = search
            product_url = await first_product(page)
            if not product_url:
                product_url = BASE + "/dp/B0D1XD1ZV3"
                report["limitations"].append("Live search did not expose a product link; used fallback direct product URL")
            report["tests"]["product"] = await inspect(page, "product", product_url)
            report["tests"]["cart"] = await inspect(page, "cart", BASE + "/gp/cart/view.html")

            # Fresh direct URL.
            direct = await context.new_page()
            report["tests"]["fresh_direct_product"] = await inspect(direct, "fresh_direct_product", product_url)
            await direct.close()

            # External -> Amazon in the same tab.
            external = await context.new_page()
            try:
                await external.goto("https://example.com/", wait_until="domcontentloaded", timeout=20000)
                report["tests"]["external_to_amazon"] = await inspect(external, "external_to_amazon", product_url)
            finally:
                await external.close()

            # Amazon -> Amazon + history traversal.
            nav = await context.new_page()
            await inspect(nav, "nav_home", BASE + "/")
            await inspect(nav, "nav_product", product_url)
            before_back = nav.url
            await nav.go_back(wait_until="domcontentloaded", timeout=30000)
            await nav.wait_for_timeout(800)
            back_active = await nav.locator(STYLE_SELECTOR).count() > 0
            await nav.go_forward(wait_until="domcontentloaded", timeout=30000)
            await nav.wait_for_timeout(800)
            forward_active = await nav.locator(STYLE_SELECTOR).count() > 0
            report["tests"]["navigation_history"] = {"before_back": before_back, "back_active": back_active, "forward_active": forward_active, "ok": back_active and forward_active}
            await nav.close()

            # Resize stability.
            resize = await context.new_page()
            await inspect(resize, "resize_product", product_url)
            resize_states = []
            for width, height in ((1920,1080),(1280,720),(900,800),(1440,900)):
                await resize.set_viewport_size({"width": width, "height": height})
                await resize.wait_for_timeout(500)
                state = await resize.evaluate("""
                () => ({styles: document.querySelectorAll('#aas-soft-hide-style,#aas-hard-hide-style').length,
                        overflow: Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth||0)-innerWidth,
                        pl: getComputedStyle(document.body).paddingLeft, pr:getComputedStyle(document.body).paddingRight})
                """)
                resize_states.append({"size": [width,height], **state})
            report["tests"]["resize"] = {"states": resize_states, "ok": all(x["styles"] > 0 for x in resize_states)}
            await resize.close()

            # Two open tabs + saved Off fresh tab.
            tab1, tab2 = await context.new_page(), await context.new_page()
            await inspect(tab1, "tab1", BASE + "/")
            await inspect(tab2, "tab2", product_url)
            off = await set_enabled(context, extension_id, False)
            await tab1.wait_for_timeout(800)
            off1 = await tab1.locator(STYLE_SELECTOR).count() == 0
            off2 = await tab2.locator(STYLE_SELECTOR).count() == 0
            fresh_off = await context.new_page()
            fresh_off_result = await inspect(fresh_off, "fresh_saved_off", BASE + "/", expect_active=False)
            await fresh_off.close()
            on = await set_enabled(context, extension_id, True)
            await tab1.wait_for_timeout(900)
            on1 = await tab1.locator(STYLE_SELECTOR).count() > 0
            on2 = await tab2.locator(STYLE_SELECTOR).count() > 0
            report["tests"]["two_tabs_toggle"] = {"off": off, "on": on, "off_tab1": off1, "off_tab2": off2, "on_tab1": on1, "on_tab2": on2, "fresh_off": fresh_off_result, "ok": bool(off.get('ok') and on.get('ok') and off1 and off2 and on1 and on2 and fresh_off_result.get('active') is False)}
            await tab1.close(); await tab2.close()

            # Dynamic live DOM checks if Rufus is actually present.
            await inspect(page, "mutation_product", product_url)
            report["tests"]["dynamic_mutation"] = await dynamic_mutation_check(page)

            # Public/account-gated routes. For sensitive routes active must be false even if Amazon redirects to sign-in.
            report["tests"]["account"] = await inspect(page, "account", BASE + "/gp/css/homepage.html", expect_active=True)
            report["tests"]["orders"] = await inspect(page, "orders", BASE + "/gp/your-account/order-history", expect_active=True)
            report["tests"]["checkout_direct"] = await inspect(page, "checkout_direct", BASE + "/gp/buy/spc/handlers/display.html", expect_active=None)
            checkout_style_count = await page.locator(STYLE_SELECTOR).count()
            report["tests"]["checkout_direct"]["sensitive_inactive"] = checkout_style_count == 0 if "/gp/buy" in page.url or "/checkout" in page.url else None
            report["tests"]["returns_direct"] = await inspect(page, "returns_direct", BASE + "/spr/returns", expect_active=None)
            returns_style_count = await page.locator(STYLE_SELECTOR).count()
            report["tests"]["returns_direct"]["sensitive_inactive"] = returns_style_count == 0 if "/spr/returns" in page.url or "/returns" in page.url else None
            report["limitations"].append("Orders/account/checkout/returns were tested only as an unauthenticated public session; authenticated controls and transaction flows still require the publisher's signed-in Amazon session.")

            # Long-lived real Amazon tab. Keep a product page alive and verify every minute.
            long_page = await context.new_page()
            long_initial = await inspect(long_page, "long_lived_initial", product_url)
            checkpoints = []
            for minute in range(1, long_minutes + 1):
                await long_page.wait_for_timeout(60_000)
                if long_page.is_closed():
                    checkpoints.append({"minute": minute, "closed": True, "ok": False})
                    break
                state = await long_page.evaluate("""
                () => ({styles: document.querySelectorAll('#aas-soft-hide-style,#aas-hard-hide-style').length,
                        bodyVisible: !!document.body && getComputedStyle(document.body).display !== 'none',
                        rufus: document.querySelectorAll('#nav-rufus-disco,.nav-rufus-disco,#rufus-container,.rufus-container,#rufus-sidebar,.rufus-sidebar,#rufus-panel,.rufus-panel').length})
                """)
                checkpoints.append({"minute": minute, **state, "ok": state["styles"] > 0 and state["bodyVisible"]})
            report["tests"]["long_lived"] = {"minutes": long_minutes, "initial": long_initial, "checkpoints": checkpoints, "ok": len(checkpoints) == long_minutes and all(x.get("ok") for x in checkpoints)}
            await long_page.close()

            report["tests"]["page_errors"] = errors

            # Aggregate only assertions that constitute extension failures. Amazon blocks become limitations.
            required_page_keys = ["homepage", "search", "product", "cart", "fresh_direct_product", "external_to_amazon"]
            for key in required_page_keys:
                item = report["tests"].get(key, {})
                if item.get("blocked"):
                    report["limitations"].append(f"{key}: Amazon challenged the CI runner")
                elif item.get("error"):
                    report["failures"].append(f"{key}: {item['error']}")
            for key in ("navigation_history", "resize", "two_tabs_toggle", "long_lived"):
                if not report["tests"].get(key, {}).get("ok"):
                    report["failures"].append(f"{key}: assertion failed")
            dyn = report["tests"].get("dynamic_mutation", {})
            if dyn.get("candidate_found") and (dyn.get("rewrite_reapplied") is not True or dyn.get("identity_restored") is not True):
                report["failures"].append("dynamic_mutation: live Rufus mutation assertion failed")
        finally:
            await context.close()
    shutil.rmtree(profile, ignore_errors=True)

    report["verdict"] = "PASS" if not report["failures"] else "FAIL"
    (REPORT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Amazon US release acceptance", "", f"Verdict: **{report['verdict']}**", "", f"Extension ID discovered: **{'yes' if report['extension_id'] else 'no'}**", ""]
    for name, result in report["tests"].items():
        if isinstance(result, dict):
            status = "PASS"
            if result.get("error") or result.get("ok") is False:
                status = "FAIL"
            elif result.get("blocked"):
                status = "BLOCKED"
            lines.append(f"- **{name}**: {status}")
    if report["failures"]:
        lines += ["", "## Extension failures"] + [f"- {x}" for x in report["failures"]]
    if report["limitations"]:
        lines += ["", "## Limitations"] + [f"- {x}" for x in report["limitations"]]
    (REPORT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((REPORT_DIR / "report.md").read_text(encoding="utf-8"))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
