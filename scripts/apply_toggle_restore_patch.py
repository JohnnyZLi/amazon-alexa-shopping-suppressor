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
    "  const originalInlineStyles = new WeakMap();\n",
    """  const originalInlineStyles = new WeakMap();
  const removedDockClasses = new Set();
  const removedDockStyles = new Map();
""",
)

replace_once(
    "  function repairDocking() {\n",
    """  function rememberRemovedDockClass(body, className) {
    if (body.classList.contains(className)) removedDockClasses.add(className);
  }

  function rememberRemovedDockStyle(body, property) {
    const value = body.style.getPropertyValue(property);
    if (!value) return;
    removedDockStyles.set(property, {
      value,
      priority: body.style.getPropertyPriority(property),
    });
  }

  function clearDockingState() {
    removedDockClasses.clear();
    removedDockStyles.clear();
  }

  function restoreDockingState() {
    const body = document.body;
    if (body) {
      for (const className of removedDockClasses) body.classList.add(className);
      for (const [property, original] of removedDockStyles.entries()) {
        body.style.setProperty(property, original.value, original.priority || '');
      }
    }
    clearDockingState();
  }

  function repairDocking() {
""",
)

replace_once(
    """      if (body.classList.contains(className)) {
        body.classList.remove(className);
        changed = true;
      }
""",
    """      if (body.classList.contains(className)) {
        rememberRemovedDockClass(body, className);
        body.classList.remove(className);
        changed = true;
      }
""",
)

replace_once(
    """      if (body.style.getPropertyValue(property)) {
        body.style.removeProperty(property);
        changed = true;
      }
""",
    """      if (body.style.getPropertyValue(property)) {
        rememberRemovedDockStyle(body, property);
        body.style.removeProperty(property);
        changed = true;
      }
""",
)

replace_once(
    """      if (isLargeDockPadding(left)) {
        body.style.removeProperty('padding-left');
        changed = true;
      }
""",
    """      if (isLargeDockPadding(left)) {
        rememberRemovedDockStyle(body, 'padding-left');
        body.style.removeProperty('padding-left');
        changed = true;
      }
""",
)

replace_once(
    """      if (isLargeDockPadding(right)) {
        body.style.removeProperty('padding-right');
        changed = true;
      }
""",
    """      if (isLargeDockPadding(right)) {
        rememberRemovedDockStyle(body, 'padding-right');
        body.style.removeProperty('padding-right');
        changed = true;
      }
""",
)

replace_once(
    """      if (hadDockClass && isLargeDockPadding(top)) {
        body.style.removeProperty('padding-top');
        changed = true;
      }
""",
    """      if (hadDockClass && isLargeDockPadding(top)) {
        rememberRemovedDockStyle(body, 'padding-top');
        body.style.removeProperty('padding-top');
        changed = true;
      }
""",
)

replace_once(
    """  function deactivate(reason) {
    if (!active) return;
    active = false;
    aggressiveMode = false;
    clearScheduledWork();
    if (bodyObserver) bodyObserver.disconnect();
    if (domObserver) domObserver.disconnect();
    if (bodyWaitObserver) bodyWaitObserver.disconnect();
    bodyObserver = null;
    domObserver = null;
    bodyWaitObserver = null;
    removeInjectedStyles();
    restoreAllManagedElements();
    log('Inactive:', reason);
  }
""",
    """  function deactivate(reason, restoreDock = false) {
    if (!active) {
      if (restoreDock) restoreDockingState();
      else clearDockingState();
      return;
    }
    active = false;
    aggressiveMode = false;
    clearScheduledWork();
    if (bodyObserver) bodyObserver.disconnect();
    if (domObserver) domObserver.disconnect();
    if (bodyWaitObserver) bodyWaitObserver.disconnect();
    bodyObserver = null;
    domObserver = null;
    bodyWaitObserver = null;
    removeInjectedStyles();
    restoreAllManagedElements();
    if (restoreDock) restoreDockingState();
    else clearDockingState();
    log('Inactive:', reason);
  }
""",
)

replace_once(
    "        deactivate('disabled by user');\n",
    "        deactivate('disabled by user', true);\n",
)

replace_once(
    "      deactivate(`${eventName}: disabled by user`);\n",
    "      deactivate(`${eventName}: disabled by user`, true);\n",
)

path.write_text(text, encoding="utf-8")
print("Added reversible dock-state handling for the user toggle")
