(() => {
  'use strict';

  /*
   * Design goals:
   * - Hide Alexa/Rufus immediately without removing it from layout while Amazon initializes.
   * - Once initialization is safely underway, collapse the UI completely.
   * - Continuously undo Rufus docking state that creates the large blank side gutter.
   * - Prefer false negatives over false positives: never hide page-shell/main-content elements.
   * - Restore inline styles if a dynamic element stops being a Rufus/Alexa candidate.
   * - Stay entirely inactive on sensitive checkout/returns flows.
   * - No network requests, persistence, remote dependencies, or privileged Chrome APIs.
   */

  const CONFIG = Object.freeze({
    DEBUG: false,
    INIT_POLL_MS: 100,
    MIN_SOFT_HIDE_MS: 3000,
    MAX_SOFT_HIDE_MS: 8000,
    FALLBACK_SCAN_MS: 5000,
    SCAN_DEBOUNCE_MS: 80,
    LARGE_DOCK_PADDING_PX: 200,
  });

  const STYLE_IDS = Object.freeze({
    soft: 'aas-soft-hide-style',
    hard: 'aas-hard-hide-style',
  });

  // Exact Rufus/Alexa-specific selectors safe enough for unconditional CSS suppression.
  // Generic container-class names stay in the guarded path below.
  const STATIC_SAFE_SELECTORS = Object.freeze([
    '#nav-rufus-disco',
    '.nav-rufus-disco',
    '#nav-flyout-rufus',
    '.nav-rufus-content',
    '#Rufus',
    '#dpx-nice-widget-container',
    '.dpx-smidget-desktop-pill-list',
    '#dpx-rex-nice-widget-container',
    '#nile-inline-btf_feature_div',
    '#nile-inline_feature_div',
    '#rufus-price-ingress',
    '.rufus-panel-container',
    '#rufus-container',
    '#rufus-container-main-view',
    '.rufus-conversation-container',
    '.rufus-textarea-container',
    '#rufus-sidebar',
    '#rufus-panel',
    '#rufus-wrapper',
    '.rufus-pill',
    '.s-ask-rufus-mshop-suggestion-container',
    '.s-suggestion-nile-desktop-container',
  ]);

  const GUARDED_SELECTORS = Object.freeze([
    '#nav-xshop-container [href*="rufus"]',
    '.nav-a[href*="rufus"]',
    '#ask_feature_div',
    '[data-feature-name="ask"]',
    '[data-feature-name="nile-inline-btf"]',
    '[data-feature-name="nile-inline"]',
    '[class*="rufus-ingress"]',
    '[data-action*="show-rufus-price-ingress"]',
    '.rufus-container',
    '.rufus-container-main-view',
    '.rufus-sidebar',
    '.rufus-panel',
    '.rufus-wrapper',
    '[id*="rufus"][id*="sidebar"]',
    '[class*="rufus"][class*="sidebar"]:not([class*="rufus-web-"]):not([class*="orc-rufus-"])',
    '[id*="rufus"][id*="panel"]',
    '[class*="rufus"][class*="panel"]:not([class*="rufus-web-"]):not([class*="orc-rufus-"])',
    '[id*="rufus"][id*="wrapper"]',
    '[class*="rufus"][class*="wrapper"]:not([class*="rufus-web-"]):not([class*="orc-rufus-"])',
  ]);

  const HEURISTIC_CANDIDATE_SELECTORS = Object.freeze([
    '[id*="rufus"]',
    '[class*="rufus"]',
    '[id*="nile-inline"]',
    '[class*="nile-inline"]',
    '[id*="dpx-nice"]',
    '[class*="dpx-nice"]',
    '[id*="dpx-rex-nice"]',
    '[class*="dpx-smidget"]',
    '[data-action*="rufus"]',
    '[data-csa-c-slot-id*="rufus"]',
  ]);

  const INIT_SIGNAL_SELECTORS = Object.freeze([
    '#nav-rufus-disco',
    '.nav-rufus-disco',
    '#dpx-nice-widget-container',
    '.rufus-panel-container',
    '#rufus-container',
    '.rufus-container',
    '.rufus-container-main-view',
    '.rufus-conversation-container',
  ]);

  const RUFUS_DOCK_CLASSES = Object.freeze([
    'rufus-docked-left',
    'rufus-docked-right',
    'rufus-docked-opening-transition',
    'rufus-docked-closing-transition',
  ]);

  const RUFUS_DOCK_PROPERTIES = Object.freeze([
    '--total-rufus-panel-full-width',
    '--total-rufus-panel-half-width',
  ]);

  const SENSITIVE_PATH_PATTERNS = Object.freeze([
    /^\/gp\/buy(?:\/|$)/i,
    /^\/checkout(?:\/|$)/i,
    /^\/hz\/checkout(?:\/|$)/i,
    /^\/spr\/returns(?:\/|$)/i,
    /^\/hz\/returns(?:\/|$)/i,
    /^\/gp\/your-account\/returns(?:\/|$)/i,
  ]);

  const PAGE_SHELL_TAGS = new Set(['HTML', 'HEAD', 'BODY']);
  const PAGE_SHELL_IDS = new Set([
    'a-page',
    'dp',
    'dp-container',
    'ppd',
    'centerCol',
    'rightCol',
    'leftCol',
    'navbar',
    'nav-belt',
    'nav-main',
    'navFooter',
    'a-popover-root',
    'pageContent',
    'search',
  ]);

  const MAIN_CONTENT_SENTINEL_IDS = Object.freeze([
    'centerCol',
    'rightCol',
    'dp-container',
    'search',
    'pageContent',
  ]);

  const SOFT_INLINE_STYLES = Object.freeze({
    opacity: '0',
    'pointer-events': 'none',
  });

  const HARD_INLINE_STYLES = Object.freeze({
    display: 'none',
    visibility: 'hidden',
    opacity: '0',
    width: '0',
    height: '0',
    'min-width': '0',
    'min-height': '0',
    'max-width': '0',
    'max-height': '0',
    overflow: 'hidden',
    'pointer-events': 'none',
  });

  const staticSelector = STATIC_SAFE_SELECTORS.join(',\n');
  const knownSelector = [
    ...STATIC_SAFE_SELECTORS,
    ...GUARDED_SELECTORS,
  ].join(',');
  const candidateSelector = [
    ...STATIC_SAFE_SELECTORS,
    ...GUARDED_SELECTORS,
    ...HEURISTIC_CANDIDATE_SELECTORS,
  ].join(',');

  let active = false;
  let aggressiveMode = false;
  let domContentLoaded = document.readyState !== 'loading';
  let bodyObserver = null;
  let domObserver = null;
  let bodyWaitObserver = null;
  let initPollTimer = null;
  let fallbackTimer = null;
  let scanTimer = null;
  let scanAnimationFrame = null;
  let startedAt = performance.now();

  const managedElements = new Set();
  const originalInlineStyles = new WeakMap();

  function log(...args) {
    if (CONFIG.DEBUG) console.debug('[AlexaSuppressor]', ...args);
  }

  function warn(...args) {
    if (CONFIG.DEBUG) console.warn('[AlexaSuppressor]', ...args);
  }

  function isSensitiveFlow() {
    const path = String(location.pathname || '/');
    return SENSITIVE_PATH_PATTERNS.some((pattern) => pattern.test(path));
  }

  function injectStyle(id, cssText) {
    if (document.getElementById(id)) return;
    const style = document.createElement('style');
    style.id = id;
    style.textContent = cssText;
    const parent = document.head || document.documentElement;
    if (parent) parent.appendChild(style);
  }

  function removeInjectedStyles() {
    for (const id of Object.values(STYLE_IDS)) {
      const style = document.getElementById(id);
      if (style) style.remove();
    }
  }

  function installSoftHideCSS() {
    injectStyle(STYLE_IDS.soft, `
${staticSelector} {
  opacity: 0 !important;
  pointer-events: none !important;
}

body.rufus-docked-left,
body.rufus-docked-right {
  padding-left: 0 !important;
  padding-right: 0 !important;
  --total-rufus-panel-full-width: 0px !important;
  --total-rufus-panel-half-width: 0px !important;
}
`);
  }

  function installHardHideCSS() {
    injectStyle(STYLE_IDS.hard, `
${staticSelector} {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
  min-width: 0 !important;
  min-height: 0 !important;
  max-width: 0 !important;
  max-height: 0 !important;
  overflow: hidden !important;
  pointer-events: none !important;
}

body.rufus-docked-left,
body.rufus-docked-right {
  padding-left: 0 !important;
  padding-right: 0 !important;
  --total-rufus-panel-full-width: 0px !important;
  --total-rufus-panel-half-width: 0px !important;
}
`);
  }

  function getClassString(element) {
    try {
      if (typeof element.className === 'string') return element.className;
      if (element.className && typeof element.className.baseVal === 'string') return element.className.baseVal;
      return String(element.className || '');
    } catch {
      return '';
    }
  }

  function containsMainContent(element) {
    for (const id of MAIN_CONTENT_SENTINEL_IDS) {
      const sentinel = document.getElementById(id);
      if (sentinel && sentinel !== element && element.contains(sentinel)) return true;
    }
    return false;
  }

  function isExplicitlyExcluded(element) {
    const id = String(element.id || '').toLowerCase();
    const classes = getClassString(element).toLowerCase();
    const slot = String(element.getAttribute('data-csa-c-slot-id') || '').toLowerCase();

    if (classes.includes('rufus-web-') || classes.includes('orc-rufus-')) return true;
    if (id.includes('rufus-web-') || id.includes('orc-rufus-')) return true;
    if (id.startsWith('rufus-text') || id.startsWith('rufus-submit')) return true;
    if (slot.includes('rufus-web-') || slot.includes('rufus-input') || slot.includes('rufus-container-submit')) return true;
    if (id === 'nav-rufus-disco-avatar' || id === 'nav-rufus-disco-text') return true;

    return false;
  }

  function hasRufusIdentity(element) {
    const id = String(element.id || '').toLowerCase();
    const classes = getClassString(element).toLowerCase();
    const feature = String(element.getAttribute('data-feature-name') || '').toLowerCase();
    const action = String(element.getAttribute('data-action') || '').toLowerCase();
    const slot = String(element.getAttribute('data-csa-c-slot-id') || '').toLowerCase();

    try {
      if (element.matches && element.matches(knownSelector)) return true;
    } catch {
      // Fall through to conservative string checks.
    }

    if (id.includes('rufus') || id.includes('nile-inline') || id.includes('dpx-nice') || id.includes('dpx-rex-nice')) return true;
    if (classes.includes('rufus') || classes.includes('nile-inline') || classes.includes('dpx-nice') || classes.includes('dpx-smidget')) return true;
    if (feature === 'ask' || feature === 'nile-inline' || feature === 'nile-inline-btf') return true;
    if (action.includes('rufus')) return true;
    if (slot.includes('rufus')) return true;

    return false;
  }

  function isSafeRufusCandidate(element) {
    try {
      if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;
      if (PAGE_SHELL_TAGS.has(element.tagName)) return false;
      if (element.id && PAGE_SHELL_IDS.has(element.id)) return false;
      if (isExplicitlyExcluded(element)) return false;
      if (containsMainContent(element)) return false;
      return hasRufusIdentity(element);
    } catch (error) {
      warn('Candidate validation failed; leaving element untouched.', error);
      return false;
    }
  }

  function rememberOriginalInlineStyle(element, property) {
    let originals = originalInlineStyles.get(element);
    if (!originals) {
      originals = new Map();
      originalInlineStyles.set(element, originals);
    }
    if (originals.has(property)) return;
    originals.set(property, {
      value: element.style.getPropertyValue(property),
      priority: element.style.getPropertyPriority(property),
    });
  }

  function observeManagedElement(element) {
    if (!domObserver || !element || !element.isConnected) return;
    try {
      domObserver.observe(element, {
        attributes: true,
        attributeFilter: ['id', 'class', 'style', 'data-feature-name', 'data-action', 'data-csa-c-slot-id'],
      });
    } catch {
      // Document-level observation and fallback scans still provide coverage.
    }
  }

  function applyManagedStyles(element, styles) {
    let changed = false;
    for (const [property, value] of Object.entries(styles)) {
      rememberOriginalInlineStyle(element, property);
      if (element.style.getPropertyValue(property) === value && element.style.getPropertyPriority(property) === 'important') continue;
      element.style.setProperty(property, value, 'important');
      changed = true;
    }
    managedElements.add(element);
    observeManagedElement(element);
    return changed;
  }

  function restoreManagedElement(element) {
    const originals = originalInlineStyles.get(element);
    if (originals) {
      for (const [property, original] of originals.entries()) {
        if (original.value) element.style.setProperty(property, original.value, original.priority || '');
        else element.style.removeProperty(property);
      }
    }
    originalInlineStyles.delete(element);
    managedElements.delete(element);
    log('Restored', element.id || getClassString(element) || element.tagName);
  }

  function restoreUnsafeManagedElements() {
    for (const element of Array.from(managedElements)) {
      if (!element.isConnected) {
        managedElements.delete(element);
        originalInlineStyles.delete(element);
        continue;
      }
      if (!isSafeRufusCandidate(element)) restoreManagedElement(element);
    }
  }

  function restoreAllManagedElements() {
    for (const element of Array.from(managedElements)) {
      if (element.isConnected) restoreManagedElement(element);
      else {
        managedElements.delete(element);
        originalInlineStyles.delete(element);
      }
    }
  }

  function softHideElement(element) {
    if (!isSafeRufusCandidate(element)) {
      if (managedElements.has(element)) restoreManagedElement(element);
      return;
    }
    applyManagedStyles(element, SOFT_INLINE_STYLES);
  }

  function hardHideElement(element) {
    if (!isSafeRufusCandidate(element)) {
      if (managedElements.has(element)) restoreManagedElement(element);
      return;
    }
    if (applyManagedStyles(element, HARD_INLINE_STYLES)) log('Hidden', element.id || getClassString(element) || element.tagName);
  }

  function suppressElement(element) {
    if (!active) return;
    if (aggressiveMode) hardHideElement(element);
    else softHideElement(element);
  }

  function isLargeDockPadding(value) {
    if (!value) return false;
    const normalized = String(value).toLowerCase();
    if (normalized.includes('rufus') || normalized.includes('--total-rufus-panel')) return true;
    const numeric = Number.parseFloat(normalized);
    return Number.isFinite(numeric) && numeric > CONFIG.LARGE_DOCK_PADDING_PX;
  }

  function repairDocking() {
    if (!active || isSensitiveFlow()) return false;
    const body = document.body;
    if (!body) return false;

    const hadDockClass = RUFUS_DOCK_CLASSES.some((name) => body.classList.contains(name));
    const hadDockProperty = RUFUS_DOCK_PROPERTIES.some((name) => Boolean(body.style.getPropertyValue(name)));
    const hasExplicitDockEvidence = hadDockClass || hadDockProperty;

    let changed = false;

    for (const className of RUFUS_DOCK_CLASSES) {
      if (body.classList.contains(className)) {
        body.classList.remove(className);
        changed = true;
      }
    }

    for (const property of RUFUS_DOCK_PROPERTIES) {
      if (body.style.getPropertyValue(property)) {
        body.style.removeProperty(property);
        changed = true;
      }
    }

    if (hasExplicitDockEvidence) {
      const left = body.style.getPropertyValue('padding-left');
      const right = body.style.getPropertyValue('padding-right');
      const top = body.style.getPropertyValue('padding-top');

      if (isLargeDockPadding(left)) {
        body.style.removeProperty('padding-left');
        changed = true;
      }
      if (isLargeDockPadding(right)) {
        body.style.removeProperty('padding-right');
        changed = true;
      }
      if (hadDockClass && isLargeDockPadding(top)) {
        body.style.removeProperty('padding-top');
        changed = true;
      }
    }

    if (changed) log('Repaired Rufus docking state');
    return changed;
  }

  function scanDocument() {
    if (!active || isSensitiveFlow()) return;
    repairDocking();
    restoreUnsafeManagedElements();
    try {
      const elements = document.querySelectorAll(candidateSelector);
      for (const element of elements) suppressElement(element);
    } catch (error) {
      warn('Candidate scan failed.', error);
    }
  }

  function scheduleScan() {
    if (!active || scanTimer || scanAnimationFrame) return;

    scanTimer = window.setTimeout(() => {
      scanTimer = null;
      if (!active) return;
      scanAnimationFrame = requestAnimationFrame(() => {
        scanAnimationFrame = null;
        scanDocument();
      });
    }, CONFIG.SCAN_DEBOUNCE_MS);
  }

  function inspectAddedNode(node) {
    if (!active || !node || node.nodeType !== Node.ELEMENT_NODE) return;
    const element = /** @type {Element} */ (node);

    suppressElement(element);

    try {
      const descendants = element.querySelectorAll(candidateSelector);
      for (const descendant of descendants) suppressElement(descendant);
    } catch {
      // Fail open; scheduled scan remains a fallback.
    }
  }

  function startDOMObserver() {
    if (!active) return;
    if (domObserver) domObserver.disconnect();

    const target = document.body || document.documentElement;
    if (!target) return;

    domObserver = new MutationObserver((mutations) => {
      if (!active) return;
      let shouldRescan = false;

      for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length) {
          shouldRescan = true;
          for (const node of mutation.addedNodes) inspectAddedNode(node);
          continue;
        }

        if (mutation.type === 'attributes') {
          const targetElement = mutation.target;
          if (!targetElement || targetElement.nodeType !== Node.ELEMENT_NODE) continue;

          if (managedElements.has(targetElement) && !isSafeRufusCandidate(targetElement)) {
            restoreManagedElement(targetElement);
            continue;
          }

          if (managedElements.has(targetElement) || isSafeRufusCandidate(targetElement)) suppressElement(targetElement);
        }
      }

      if (shouldRescan) scheduleScan();
    });

    domObserver.observe(target, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['id', 'class', 'data-feature-name', 'data-action', 'data-csa-c-slot-id'],
    });

    for (const element of managedElements) observeManagedElement(element);
  }

  function startBodyObserver() {
    if (!active || !document.body) return;
    if (bodyObserver) bodyObserver.disconnect();

    bodyObserver = new MutationObserver(() => {
      repairDocking();
    });

    bodyObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ['class', 'style'],
    });

    repairDocking();
  }

  function whenBodyExists(callback) {
    if (document.body) {
      callback();
      return;
    }

    if (bodyWaitObserver) return;
    bodyWaitObserver = new MutationObserver(() => {
      if (!document.body) return;
      bodyWaitObserver.disconnect();
      bodyWaitObserver = null;
      callback();
    });

    const root = document.documentElement;
    if (root) bodyWaitObserver.observe(root, { childList: true });
  }

  function hasInitializedSignal() {
    if (document.readyState === 'loading' && !domContentLoaded) return false;

    for (const selector of INIT_SIGNAL_SELECTORS) {
      try {
        const element = document.querySelector(selector);
        if (!element) continue;
        if (element.children.length > 0) return true;
        if ((element.textContent || '').trim().length > 0) return true;
      } catch {
        // Ignore selector/query failures.
      }
    }

    return false;
  }

  function enterAggressiveMode(reason) {
    if (!active || aggressiveMode) return;
    aggressiveMode = true;
    installHardHideCSS();
    repairDocking();
    scanDocument();
    log('Aggressive mode enabled:', reason);
  }

  function startInitializationController() {
    if (initPollTimer) window.clearInterval(initPollTimer);

    initPollTimer = window.setInterval(() => {
      if (!active) return;
      const elapsed = performance.now() - startedAt;
      if (elapsed < CONFIG.MIN_SOFT_HIDE_MS) return;

      if (hasInitializedSignal()) {
        window.clearInterval(initPollTimer);
        initPollTimer = null;
        enterAggressiveMode('initialization signal');
        return;
      }

      if (elapsed >= CONFIG.MAX_SOFT_HIDE_MS) {
        window.clearInterval(initPollTimer);
        initPollTimer = null;
        enterAggressiveMode('safety timeout');
      }
    }, CONFIG.INIT_POLL_MS);
  }

  function startFallbackRepair() {
    if (fallbackTimer) window.clearInterval(fallbackTimer);
    fallbackTimer = window.setInterval(() => {
      if (!active) return;
      if (isSensitiveFlow()) {
        deactivate('sensitive flow detected');
        return;
      }
      scanDocument();
    }, CONFIG.FALLBACK_SCAN_MS);
  }

  function clearScheduledWork() {
    if (initPollTimer) window.clearInterval(initPollTimer);
    if (fallbackTimer) window.clearInterval(fallbackTimer);
    if (scanTimer) window.clearTimeout(scanTimer);
    if (scanAnimationFrame) cancelAnimationFrame(scanAnimationFrame);
    initPollTimer = null;
    fallbackTimer = null;
    scanTimer = null;
    scanAnimationFrame = null;
  }

  function deactivate(reason) {
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

  function activate(reason) {
    if (active || isSensitiveFlow()) return;
    active = true;
    aggressiveMode = false;
    startedAt = performance.now();
    domContentLoaded = document.readyState !== 'loading';
    installSoftHideCSS();

    whenBodyExists(() => {
      if (!active) return;
      startBodyObserver();
      startDOMObserver();
      scanDocument();
    });

    startInitializationController();
    startFallbackRepair();
    log('Active:', reason);
  }

  function onNavigationSignal(eventName) {
    if (isSensitiveFlow()) {
      deactivate(`${eventName}: sensitive flow`);
      return;
    }
    if (!active) activate(`${eventName}: safe flow`);
    else {
      repairDocking();
      scheduleScan();
    }
  }

  function boot() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        domContentLoaded = true;
        if (active) {
          whenBodyExists(() => {
            if (!active) return;
            startBodyObserver();
            startDOMObserver();
            scanDocument();
          });
        }
      }, { once: true });
    }

    window.addEventListener('load', () => {
      if (active) {
        repairDocking();
        scheduleScan();
      }
    }, { once: true });

    window.addEventListener('pageshow', () => onNavigationSignal('pageshow'));
    window.addEventListener('popstate', () => onNavigationSignal('popstate'));

    if (isSensitiveFlow()) {
      log('Sensitive flow detected; extension remains inactive.');
      return;
    }

    activate('initial document');
  }

  try {
    boot();
  } catch (error) {
    try { deactivate('fatal initialization error'); } catch { /* best effort */ }
    warn('Fatal initialization error; extension deactivated.', error);
  }
})();
