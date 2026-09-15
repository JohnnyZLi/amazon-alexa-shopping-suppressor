from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


content_path = Path("content.js")
text = content_path.read_text(encoding="utf-8")

# Adios 2.0.0 does not unconditionally target these suggestion containers.
# Keep suppressing them on normal shopping/search pages, but route them through
# our guarded path so Returns can preserve Amazon's functional AI workflow.
for selector in (
    ".s-ask-rufus-mshop-suggestion-container",
    ".s-suggestion-nile-desktop-container",
):
    text = replace_once(
        text,
        f"    '{selector}',\n",
        "",
        f"remove {selector} from STATIC_SAFE_SELECTORS",
    )

text = replace_once(
    text,
    "    '.rufus-pill',\n    '.rufus-sidebar',\n",
    "    '.rufus-pill',\n"
    "    '.s-ask-rufus-mshop-suggestion-container',\n"
    "    '.s-suggestion-nile-desktop-container',\n"
    "    '.rufus-sidebar',\n",
    "add suggestion surfaces to guarded selectors",
)

old_preserve = """  const RETURN_FLOW_PRESERVE_SELECTORS = Object.freeze([\n    '#rufus-container-main-view',\n    '.rufus-container-main-view',\n    '.rufus-conversation-container',\n    '.rufus-textarea-container',\n    '.rufus-pill',\n  ]);\n"""
new_preserve = """  const RETURN_FLOW_PRESERVE_SELECTORS = Object.freeze([\n    '#rufus-container-main-view',\n    '.rufus-container-main-view',\n    '.rufus-conversation-container',\n    '.rufus-textarea-container',\n    '.rufus-pill',\n    '.s-ask-rufus-mshop-suggestion-container',\n    '.s-suggestion-nile-desktop-container',\n  ]);\n"""
text = replace_once(text, old_preserve, new_preserve, "extend Returns preserve selectors")
content_path.write_text(text, encoding="utf-8")


smoke_path = Path("scripts/browser_smoke.py")
smoke = smoke_path.read_text(encoding="utf-8")

smoke = replace_once(
    smoke,
    "            '<h1 id=\"return-heading\">Select your primary reason for return.</h1>'\n"
    "            '<section class=\"orc-rufus-return-flow\"><div id=\"rufus-container-main-view\">'\n",
    "            '<h1 id=\"return-heading\">Select your primary reason for return.</h1>'\n"
    "            '<div id=\"return-ai-ingress\" class=\"s-ask-rufus-mshop-suggestion-container\">AI return ingress</div>'\n"
    "            '<div id=\"return-ai-options\" class=\"s-suggestion-nile-desktop-container\">AI return options</div>'\n"
    "            '<section class=\"orc-rufus-return-flow\"><div id=\"rufus-container-main-view\">'\n",
    "add Returns suggestion-surface fixture",
)

smoke = replace_once(
    smoke,
    "        assert await computed(page, \"#rufus-panel\", \"display\") == \"none\", path\n"
    "        assert await computed(page, \"#return-reason\", \"display\") != \"none\", path\n",
    "        assert await computed(page, \"#rufus-panel\", \"display\") == \"none\", path\n"
    "        assert await computed(page, \"#return-ai-ingress\", \"display\") != \"none\", path\n"
    "        assert await computed(page, \"#return-ai-options\", \"display\") != \"none\", path\n"
    "        assert await computed(page, \"#return-reason\", \"display\") != \"none\", path\n",
    "assert Returns suggestion surfaces remain visible",
)

anchor = "async def assert_account_and_order_pages_keep_controls(browser: Browser) -> None:\n"
new_test = '''async def assert_search_suggestion_surfaces_still_suppressed(browser: Browser) -> None:\n    page = await new_page(\n        browser,\n        '<html><head></head><body>'\n        '<div id="shopping-ai-ingress" class="s-ask-rufus-mshop-suggestion-container">shopping AI</div>'\n        '<div id="shopping-ai-options" class="s-suggestion-nile-desktop-container">shopping suggestions</div>'\n        '</body></html>',\n        "/s?k=portable+charger",\n        storage_enabled=True,\n    )\n    await page.wait_for_timeout(130)\n    assert await computed(page, "#shopping-ai-ingress", "display") == "none"\n    assert await computed(page, "#shopping-ai-options", "display") == "none"\n    await page.close()\n\n\n'''
smoke = replace_once(smoke, anchor, new_test + anchor, "add normal-page suggestion suppression test")

smoke = replace_once(
    smoke,
    '        ("embedded Returns Rufus workflow remains usable", assert_embedded_return_rufus_workflow_stays_usable),\n'
    '        ("account/order pages keep controls while suppressing Rufus", assert_account_and_order_pages_keep_controls),\n',
    '        ("embedded Returns Rufus workflow remains usable", assert_embedded_return_rufus_workflow_stays_usable),\n'
    '        ("shopping suggestion surfaces remain suppressed off Returns", assert_search_suggestion_surfaces_still_suppressed),\n'
    '        ("account/order pages keep controls while suppressing Rufus", assert_account_and_order_pages_keep_controls),\n',
    "register suggestion-surface regression",
)

smoke_path.write_text(smoke, encoding="utf-8")
