#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "content.js"
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one match, found {count}: {old[:100]!r}")
    text = text.replace(old, new, 1)


replace_once(
    "   * - No network requests, persistence, remote dependencies, or privileged Chrome APIs.\n",
    "   * - No network requests or remote dependencies; Chrome storage is used only for the local on/off preference.\n",
)

replace_once(
    "  const STYLE_IDS = Object.freeze({\n",
    "  const STORAGE_KEY = 'enabled';\n\n  const STYLE_IDS = Object.freeze({\n",
)

replace_once(
    "  let active = false;\n",
    "  let userEnabled = true;\n  let active = false;\n",
)

replace_once(
    "  function isSensitiveFlow() {\n",
    """  function hasStorageAPI() {
    return typeof chrome !== 'undefined'
      && chrome.storage
      && chrome.storage.local
      && chrome.storage.onChanged;
  }

  async function readEnabledPreference() {
    if (!hasStorageAPI()) return true;
    try {
      const stored = await chrome.storage.local.get({ [STORAGE_KEY]: true });
      return stored[STORAGE_KEY] !== false;
    } catch (error) {
      warn('Could not read enabled preference; defaulting to enabled.', error);
      return true;
    }
  }

  function startPreferenceObserver() {
    if (!hasStorageAPI()) return;
    chrome.storage.onChanged.addListener((changes, areaName) => {
      if (areaName !== 'local' || !changes[STORAGE_KEY]) return;
      const enabled = changes[STORAGE_KEY].newValue !== false;
      if (enabled === userEnabled) return;
      userEnabled = enabled;
      if (!userEnabled) {
        deactivate('disabled by user');
        return;
      }
      if (!isSensitiveFlow()) activate('enabled by user');
    });
  }

  function isSensitiveFlow() {
""",
)

replace_once(
    "  function activate(reason) {\n    if (active || isSensitiveFlow()) return;\n",
    "  function activate(reason) {\n    if (!userEnabled || active || isSensitiveFlow()) return;\n",
)

replace_once(
    "  function onNavigationSignal(eventName) {\n    if (isSensitiveFlow()) {\n",
    """  function onNavigationSignal(eventName) {
    if (!userEnabled) {
      deactivate(`${eventName}: disabled by user`);
      return;
    }
    if (isSensitiveFlow()) {
""",
)

replace_once(
    "  function boot() {\n",
    "  async function boot() {\n",
)

replace_once(
    """    if (isSensitiveFlow()) {
      log('Sensitive flow detected; extension remains inactive.');
      return;
    }

    activate('initial document');
""",
    """    startPreferenceObserver();
    userEnabled = await readEnabledPreference();
    if (!userEnabled) {
      log('Disabled by user; extension remains inactive.');
      return;
    }

    if (isSensitiveFlow()) {
      log('Sensitive flow detected; extension remains inactive.');
      return;
    }

    activate('initial document');
""",
)

replace_once(
    """  try {
    boot();
  } catch (error) {
    try { deactivate('fatal initialization error'); } catch { /* best effort */ }
    warn('Fatal initialization error; extension deactivated.', error);
  }
""",
    """  boot().catch((error) => {
    try { deactivate('fatal initialization error'); } catch { /* best effort */ }
    warn('Fatal initialization error; extension deactivated.', error);
  });
""",
)

path.write_text(text, encoding="utf-8")
print("Applied toggle integration to content.js")
