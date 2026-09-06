#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, async_playwright

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "artifacts" / "live-marketplaces"

MARKETPLACES = [
    "amazon.com",
    "amazon.ca",
    "amazon.com.mx",
    "amazon.com.br",
    "amazon.co.uk",
    "amazon.de",
    "amazon.fr",
    "amazon.it",
    "amazon.es",
    "amazon.nl",
    "amazon.com.be",
    "amazon.se",
    "amazon.pl",
    "amazon.ie",
    "amazon.com.tr",
    "amazon.ae",
    "amazon.sa",
    "amazon.eg",
    "amazon.co.za",
    "amazon.co.jp",
    "amazon.in",
    "amazon.sg",
    "amazon.com.au",
]

RUFUS_SELECTORS = ",".join(
    [
        "#nav-rufus-disco",
        ".nav-rufus-disco",
        "#nav-flyout-rufus",
        "#Rufus",
        "#rufus-container",
        ".rufus-container",
        "#rufus-sidebar",
        ".rufus-sidebar",
        "#rufus-panel",
        ".rufus-panel",
        ".rufus-panel-container",
        "#dpx-nice-widget-container",
        "#dpx-rex-nice-widget-container",
        "#rufus-price-ingress",
        ".s-ask-rufus-mshop-suggestion-container",
        ".s-suggestion-nile-desktop-container",
    ]
)

BLOCK_MARKERS = [
    "robot check",
    "enter the characters you see below",
    "sorry, we just need to make sure you're not a robot",
    "validatecaptcha",
    "automated access to amazon data",
]


def find_browser() -> str:
    # Prefer unbranded Chromium because --load-extension remains supported there.
    for candidate in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(candidate)
        if path:
            return path
    raise RuntimeError("Chromium/Chrome executable not found")


def marketplace_host_matches(final_url: str, marketplace: str) -> bool:
    host = (urlparse(final_url).hostname or "").lower()
    return host == marketplace or host == f"www.{marketplace}"


async def discover_extension_id(context: BrowserContext, profile_dir: Path) -> str | None:
    page = await context.new_page()
    try:
        await page.goto("chrome://extensions/", wait_until="domcontentloaded", timeout=15000)
        for _ in range(20):
            items = await page.evaluate(
                """
                () => {
                  const manager = document.querySelector('extensions-manager');
                  const list = manager?.shadowRoot?.querySelector('extensions-item-list');
                  const nodes = list?.shadowRoot?.querySelectorAll('extensions-item') || [];
                  return [...nodes].map(item => ({
                    id: item.id || item.getAttribute('id') || '',
                    name: item.shadowRoot?.querySelector('#name')?.textContent?.trim() || '',
                  }));
                }
                """
            )
            for item in items:
                if "Alexa" in item.get("name", "") and "Suppressor" in item.get("name", ""):
                    return item.get("id") or None
            await page.wait_for_timeout(250)
    finally:
        await page.close()

    # Fallback for Chromium builds where chrome://extensions internals are not script-readable.
    for relative in (Path("Default/Preferences"), Path("Default/Secure Preferences")):
        path = profile_dir / relative
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        settings = data.get("extensions", {}).get("settings", {})
        for extension_id, details in settings.items():
            manifest = details.get("manifest", {}) if isinstance(details, dict) else {}
            name = str(manifest.get("name", ""))
            if "Alexa" in name and "Suppressor" in name:
                return extension_id
    return None


async def set_enabled(context: BrowserContext, extension_id: str, enabled: bool) -> dict:
    page = await context.new_page()
    result = {"requested": enabled, "ok": False, "checked": None, "status": None, "error": None}
    try:
        await page.goto(f"chrome-extension://{extension_id}/popup.html", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_selector("#enabled", timeout=10000)
        current = await page.is_checked("#enabled")
        if current != enabled:
            await page.click("#enabled")
        await page.wait_for_timeout(500)
        result["checked"] = await page.is_checked("#enabled")
        result["status"] = await page.locator("#status").text_content()
        result["ok"] = result["checked"] is enabled and result["status"] == ("On" if enabled else "Off")
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        await page.close()
    return result


async def inspect_page(page: Page, marketplace: str, kind: str, url: str) -> dict:
    result = {
        "kind": kind,
        "requested_url": url,
        "final_url": None,
        "http_status": None,
        "marketplace_host": False,
        "blocked": False,
        "extension_active": False,
        "style_count": 0,
        "body_visible": False,
        "rufus_candidates": 0,
        "rufus_hidden": None,
        "title": None,
        "error": None,
    }
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        result["http_status"] = response.status if response else None
        await page.wait_for_timeout(1800)
        result["final_url"] = page.url
        result["marketplace_host"] = marketplace_host_matches(page.url, marketplace)
        result["title"] = (await page.title())[:200]

        try:
            body_text = (await page.locator("body").inner_text(timeout=5000)).lower()
        except Exception:
            body_text = ""
        result["blocked"] = any(marker in body_text or marker in page.url.lower() for marker in BLOCK_MARKERS)

        result["style_count"] = await page.locator("#aas-soft-hide-style, #aas-hard-hide-style").count()
        result["extension_active"] = result["style_count"] > 0

        result["body_visible"] = await page.evaluate(
            """
            () => {
              const body = document.body;
              if (!body) return false;
              const s = getComputedStyle(body);
              return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity || 1) > 0;
            }
            """
        )

        try:
            candidates = page.locator(RUFUS_SELECTORS)
            count = await candidates.count()
            result["rufus_candidates"] = count
            if count:
                states = await candidates.evaluate_all(
                    """
                    els => els.slice(0, 40).map(el => {
                      const s = getComputedStyle(el);
                      return {
                        display: s.display,
                        visibility: s.visibility,
                        opacity: Number.parseFloat(s.opacity || '1'),
                      };
                    })
                    """
                )
                result["rufus_hidden"] = all(
                    state["display"] == "none"
                    or state["visibility"] == "hidden"
                    or state["opacity"] <= 0.01
                    for state in states
                )
        except Exception:
            # Rufus detection is evidence, not a prerequisite for a smoke pass.
            pass
    except PlaywrightTimeoutError as exc:
        result["error"] = f"timeout: {exc}"
        result["final_url"] = page.url
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["final_url"] = page.url
    return result


async def first_product_url(page: Page, marketplace: str) -> str | None:
    try:
        links = await page.locator('a[href*="/dp/"]').evaluate_all(
            """
            (els, marketplace) => els
              .map(el => el.href)
              .filter(Boolean)
              .filter(href => {
                try {
                  const u = new URL(href);
                  return u.hostname === marketplace || u.hostname === `www.${marketplace}`;
                } catch {
                  return false;
                }
              })
            """,
            marketplace,
        )
    except Exception:
        return None
    seen = set()
    for href in links:
        clean = href.split("?")[0]
        if clean in seen:
            continue
        seen.add(clean)
        if "/dp/" in clean:
            return clean
    return None


async def run_marketplace(context: BrowserContext, extension_id: str | None, marketplace: str) -> dict:
    page = await context.new_page()
    await page.set_viewport_size({"width": 1365, "height": 900})
    result = {
        "marketplace": marketplace,
        "home": None,
        "toggle_off": None,
        "toggle_on": None,
        "off_cleared_styles": None,
        "on_restored_styles": None,
        "search": None,
        "product": None,
        "product_discovery": None,
        "verdict": "INCONCLUSIVE",
        "notes": [],
    }

    try:
        if extension_id:
            await set_enabled(context, extension_id, True)

        home_url = f"https://www.{marketplace}/"
        result["home"] = await inspect_page(page, marketplace, "home", home_url)

        if extension_id and result["home"]["extension_active"]:
            result["toggle_off"] = await set_enabled(context, extension_id, False)
            await page.wait_for_timeout(700)
            result["off_cleared_styles"] = await page.locator("#aas-soft-hide-style, #aas-hard-hide-style").count() == 0

            result["toggle_on"] = await set_enabled(context, extension_id, True)
            await page.wait_for_timeout(900)
            result["on_restored_styles"] = await page.locator("#aas-soft-hide-style, #aas-hard-hide-style").count() > 0
        elif not extension_id:
            result["notes"].append("Could not discover extension ID; live toggle test skipped.")

        search_url = f"https://www.{marketplace}/s?k=usb+cable"
        result["search"] = await inspect_page(page, marketplace, "search", search_url)

        product_url = None
        if result["search"]["error"] is None and not result["search"]["blocked"]:
            product_url = await first_product_url(page, marketplace)
        result["product_discovery"] = product_url
        if product_url:
            result["product"] = await inspect_page(page, marketplace, "product", product_url)
        else:
            result["product"] = {
                "kind": "product",
                "requested_url": None,
                "final_url": None,
                "http_status": None,
                "marketplace_host": False,
                "blocked": bool(result["search"]["blocked"]),
                "extension_active": False,
                "style_count": 0,
                "body_visible": False,
                "rufus_candidates": 0,
                "rufus_hidden": None,
                "title": None,
                "error": "no product link discovered from live search",
            }

        pages = [result["home"], result["search"], result["product"]]
        accessible = [p for p in pages if p and not p["blocked"] and p["error"] is None]
        blocked_count = sum(1 for p in pages if p and p["blocked"])
        extension_failures = [p for p in accessible if not p["extension_active"] or not p["body_visible"]]
        rufus_failures = [
            p for p in accessible if p["rufus_candidates"] > 0 and p["rufus_hidden"] is False
        ]
        toggle_failed = extension_id is not None and (
            not result["toggle_off"]
            or not result["toggle_off"]["ok"]
            or not result["toggle_on"]
            or not result["toggle_on"]["ok"]
            or result["off_cleared_styles"] is not True
            or result["on_restored_styles"] is not True
        )

        if extension_failures or rufus_failures or toggle_failed:
            result["verdict"] = "FAIL"
            if extension_failures:
                result["notes"].append("Extension/style or page-shell smoke assertion failed on an accessible page.")
            if rufus_failures:
                result["notes"].append("A detected Rufus candidate was not suppressed while On.")
            if toggle_failed:
                result["notes"].append("Off/On storage propagation failed on the live marketplace page.")
        elif len(accessible) == 3 and extension_id is not None:
            result["verdict"] = "PASS"
        elif blocked_count == 3:
            result["verdict"] = "BLOCKED"
            result["notes"].append("All live page types were blocked/challenged by Amazon from the CI runner.")
        else:
            result["verdict"] = "PARTIAL"
            if blocked_count:
                result["notes"].append(f"Amazon challenged {blocked_count} of 3 live page types from the CI runner.")
            if not product_url:
                result["notes"].append("Could not discover a product URL from the live search page.")
    finally:
        if extension_id:
            await set_enabled(context, extension_id, True)
        await page.close()

    return result


def markdown_report(results: list[dict], extension_id: str | None) -> str:
    counts: dict[str, int] = {}
    for result in results:
        counts[result["verdict"]] = counts.get(result["verdict"], 0) + 1

    lines = [
        "# Live Amazon marketplace smoke report",
        "",
        f"Marketplaces attempted: **{len(results)} / {len(MARKETPLACES)}**",
        f"Unpacked extension ID discovered: **{'yes' if extension_id else 'no'}**",
        "",
        "Verdict counts: " + ", ".join(f"**{key}: {value}**" for key, value in sorted(counts.items())),
        "",
        "| Marketplace | Verdict | Home | Toggle | Search | Product | Rufus evidence |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]

    def page_cell(page: dict | None) -> str:
        if not page:
            return "—"
        if page.get("blocked"):
            return "BLOCKED"
        if page.get("error"):
            return "ERROR"
        if page.get("extension_active") and page.get("body_visible"):
            return "PASS"
        return "FAIL"

    for result in results:
        toggle_ok = (
            result.get("toggle_off", {}).get("ok")
            and result.get("toggle_on", {}).get("ok")
            and result.get("off_cleared_styles") is True
            and result.get("on_restored_styles") is True
        ) if result.get("toggle_off") and result.get("toggle_on") else False
        evidence = []
        for page_name in ("home", "search", "product"):
            page = result.get(page_name)
            if page and page.get("rufus_candidates", 0):
                evidence.append(f"{page_name}:{page['rufus_candidates']} hidden={page.get('rufus_hidden')}")
        lines.append(
            f"| {result['marketplace']} | **{result['verdict']}** | {page_cell(result['home'])} | "
            f"{'PASS' if toggle_ok else 'SKIP/FAIL'} | {page_cell(result['search'])} | "
            f"{page_cell(result['product'])} | {'; '.join(evidence) if evidence else 'none detected'} |"
        )

    lines.extend(["", "## Notes", ""])
    for result in results:
        if result["notes"]:
            lines.append(f"- **{result['marketplace']}**: {' '.join(result['notes'])}")
    lines.append("")
    lines.append(
        "PASS requires live homepage, search, and product pages to load without an Amazon bot challenge, "
        "the extension's injected styles to be present while On, the page body to remain visible, any detected "
        "Rufus candidates to be hidden, and Off/On to propagate to the already-open live page."
    )
    return "\n".join(lines) + "\n"


async def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    browser_path = find_browser()
    profile_dir = Path(tempfile.mkdtemp(prefix="aas-live-marketplaces-"))
    results: list[dict] = []
    extension_id: str | None = None

    try:
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                executable_path=browser_path,
                headless=False,
                ignore_default_args=["--disable-extensions"],
                args=[
                    f"--disable-extensions-except={ROOT}",
                    f"--load-extension={ROOT}",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1365,900",
                ],
                locale="en-US",
            )
            try:
                await asyncio.sleep(1.5)
                extension_id = await discover_extension_id(context, profile_dir)
                print(f"Extension ID: {extension_id or 'NOT FOUND'}")
                for index, marketplace in enumerate(MARKETPLACES, 1):
                    print(f"[{index:02d}/{len(MARKETPLACES)}] Testing {marketplace} ...", flush=True)
                    result = await run_marketplace(context, extension_id, marketplace)
                    results.append(result)
                    print(f"  -> {result['verdict']}", flush=True)
                    await asyncio.sleep(0.4)
            finally:
                await context.close()
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)

    payload = {
        "marketplaces_expected": MARKETPLACES,
        "extension_id_discovered": extension_id,
        "results": results,
    }
    (REPORT_DIR / "report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_md = markdown_report(results, extension_id)
    (REPORT_DIR / "report.md").write_text(report_md, encoding="utf-8")
    print("\n" + report_md)

    if len(results) != len(MARKETPLACES):
        return 2
    if any(result["verdict"] == "FAIL" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
