#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

from live_marketplace_smoke import (
    ROOT,
    discover_extension_id,
    find_browser,
    inspect_page,
    set_enabled,
)

OUT = ROOT / "artifacts" / "live-marketplaces-retry"

CASES = {
    "amazon.de": {
        "searches": [
            "https://www.amazon.de/-/en/s?k=usb+cable",
            "https://www.amazon.de/s?k=usb-c+kabel",
            "https://www.amazon.de/-/en/gp/bestsellers/",
        ],
        "product": "https://www.amazon.de/-/en/15-Inch-15-3-Inch-Illuminated-Keyboard-FaceTime/dp/B0CX21V4NY",
    },
    "amazon.fr": {
        "searches": [
            "https://www.amazon.fr/cable-usb-c/s?k=cable+usb+c",
            "https://www.amazon.fr/s?k=cable+usb-c",
            "https://www.amazon.fr/gp/bestsellers/high-tech/",
        ],
        "product": "https://www.amazon.fr/UGREEN-Charge-Compatible-MacBook-Manette/dp/B08FDJ36XW",
    },
    "amazon.pl": {
        "searches": [
            "https://www.amazon.pl/s?k=kabel+usb-c",
            "https://www.amazon.pl/gp/bestsellers/electronics/20788627031",
            "https://www.amazon.pl/gp/bestsellers/electronics",
        ],
        "product": "https://www.amazon.pl/Anker-Kabel-USB-C-Lightning-certyfikatem/dp/B07H256MBK",
    },
}

LOCALIZED_BLOCK_TITLES = {
    "Tut uns Leid!",
    "Toutes nos excuses",
    "Przepraszamy",
}


def usable(page_result: dict) -> bool:
    title = str(page_result.get("title") or "").strip()
    status = page_result.get("http_status")
    return (
        page_result.get("error") is None
        and page_result.get("extension_active") is True
        and page_result.get("body_visible") is True
        and status is not None
        and 200 <= status < 400
        and title not in LOCALIZED_BLOCK_TITLES
    )


async def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    profile_dir = Path(tempfile.mkdtemp(prefix="aas-live-retry-"))
    browser_path = find_browser()
    results = []
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
                if not extension_id:
                    raise RuntimeError("Could not discover unpacked extension ID")
                await set_enabled(context, extension_id, True)

                for marketplace, case in CASES.items():
                    page = await context.new_page()
                    await page.set_viewport_size({"width": 1365, "height": 900})
                    try:
                        attempts = []
                        selected = None
                        for url in case["searches"]:
                            current = await inspect_page(page, marketplace, "search-retry", url)
                            attempts.append(current)
                            if usable(current):
                                selected = current
                                break
                            await page.wait_for_timeout(750)

                        product = await inspect_page(page, marketplace, "product-retry", case["product"])

                        # Exercise the real local toggle on the direct live product page too.
                        off = await set_enabled(context, extension_id, False)
                        await page.wait_for_timeout(650)
                        off_cleared = await page.locator("#aas-soft-hide-style, #aas-hard-hide-style").count() == 0
                        on = await set_enabled(context, extension_id, True)
                        await page.wait_for_timeout(850)
                        on_restored = await page.locator("#aas-soft-hide-style, #aas-hard-hide-style").count() > 0

                        verdict = "PASS" if (
                            selected is not None
                            and usable(product)
                            and off.get("ok")
                            and on.get("ok")
                            and off_cleared
                            and on_restored
                        ) else "PARTIAL"
                        results.append({
                            "marketplace": marketplace,
                            "verdict": verdict,
                            "search_attempts": attempts,
                            "selected_search_or_browse": selected,
                            "product": product,
                            "toggle_off": off,
                            "toggle_on": on,
                            "off_cleared_styles": off_cleared,
                            "on_restored_styles": on_restored,
                        })
                        print(f"{marketplace}: {verdict}")
                    finally:
                        await set_enabled(context, extension_id, True)
                        await page.close()
            finally:
                await context.close()
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)

    (OUT / "report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Focused live marketplace retry",
        "",
        "| Marketplace | Verdict | Alternate search/browse | Direct product | Off/On |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in results:
        search_ok = r["selected_search_or_browse"] is not None
        product_ok = usable(r["product"])
        toggle_ok = r["toggle_off"]["ok"] and r["toggle_on"]["ok"] and r["off_cleared_styles"] and r["on_restored_styles"]
        lines.append(
            f"| {r['marketplace']} | **{r['verdict']}** | {'PASS' if search_ok else 'BLOCKED/FAIL'} | "
            f"{'PASS' if product_ok else 'BLOCKED/FAIL'} | {'PASS' if toggle_ok else 'FAIL'} |"
        )
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
