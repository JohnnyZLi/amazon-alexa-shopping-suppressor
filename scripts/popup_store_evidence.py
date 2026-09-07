#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from playwright.async_api import BrowserContext, async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "popup-store-evidence"
OUT.mkdir(parents=True, exist_ok=True)


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


async def main() -> int:
    profile = Path(tempfile.mkdtemp(prefix="aas-popup-evidence-"))
    browser = find_browser()
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            str(profile), executable_path=browser, headless=False,
            args=[f"--disable-extensions-except={ROOT}", f"--load-extension={ROOT}", "--no-first-run"],
            viewport={"width": 336, "height": 230},
        )
        try:
            extension_id = await discover_extension_id(context, profile)
            if not extension_id:
                raise RuntimeError("Extension ID not discovered")
            page = await context.new_page()
            await page.goto(f"chrome-extension://{extension_id}/popup.html", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_selector("#enabled", timeout=10000)
            await page.wait_for_selector(".control-card", timeout=10000)

            evidence = {"extension_id": extension_id, "light": {}, "dark": {}}
            for scheme in ("light", "dark"):
                await page.emulate_media(color_scheme=scheme)
                await page.wait_for_timeout(250)
                state = await page.evaluate("""
                () => {
                  const toggle = document.querySelector('#enabled');
                  const status = document.querySelector('#status');
                  const card = document.querySelector('.control-card');
                  const detail = document.querySelector('#state-description');
                  return {
                    checked: toggle.checked,
                    status: status.textContent.trim(),
                    detail: detail?.textContent?.trim() || '',
                    bodyBackground: getComputedStyle(document.body).backgroundColor,
                    bodyColor: getComputedStyle(document.body).color,
                    cardBackground: getComputedStyle(card).backgroundColor,
                    width: document.documentElement.scrollWidth,
                    height: document.documentElement.scrollHeight,
                  };
                }
                """)
                evidence[scheme] = state
                await page.screenshot(path=str(OUT / f"popup-{scheme}.png"), full_page=True)

            # Also capture the Off state in light mode to document inverse copy and state.
            await page.emulate_media(color_scheme="light")
            await page.click("#enabled")
            await page.wait_for_timeout(450)
            off_state = await page.evaluate("""
            () => ({
              checked: document.querySelector('#enabled').checked,
              status: document.querySelector('#status').textContent.trim(),
              detail: document.querySelector('#state-description')?.textContent?.trim() || ''
            })
            """)
            evidence["off"] = off_state
            await page.screenshot(path=str(OUT / "popup-off-light.png"), full_page=True)
            (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")

            ok = (
                evidence["light"]["checked"] is True
                and evidence["light"]["status"] == "On"
                and evidence["dark"]["checked"] is True
                and evidence["dark"]["status"] == "On"
                and evidence["light"]["bodyBackground"] != evidence["dark"]["bodyBackground"]
                and evidence["light"]["cardBackground"] != evidence["dark"]["cardBackground"]
                and off_state["checked"] is False
                and off_state["status"] == "Off"
                and "untouched" in off_state["detail"].lower()
            )
            print(json.dumps(evidence, indent=2))
            return 0 if ok else 1
        finally:
            await context.close()
            shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
