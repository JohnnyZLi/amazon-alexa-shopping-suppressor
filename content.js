
(() => {
  'use strict';

  /*
   * Design goals:
   * - Hide Alexa/Rufus immediately without removing it from layout while Amazon initializes.
   * - Once initialization is safely underway, collapse the UI completely.
   * - Continuously undo Rufus docking state that creates the large blank side gutter.
   * - Prefer false negatives over false positives: never hide page-shell/main-content elements.
   * - No network requests, persistence, remote dependencies, or privileged userscript APIs.
   */

  const CONFIG = Object.freeze({
    DEBUG: false,
    INIT_POLL_MS: 100,
    MIN_SOFT_HIDE_MS: 3000,
    MAX_SOFT_HIDE_MS: 8000,
    FALLBACK_SCAN_MS: 2500,
    SCAN_DEBOUNCE_MS: 80,
    LARGE_DOCK_PADDING_PX: 200,
  });

  const STYLE_IDS = Object.freeze({
    soft: 'aas-soft-hide-style',
    hard: 'aas-hard-hide-style',
  });

  // Known Alexa/Rufus UI. These selectors come from the working Adios Alexa 2.0.0
  // implementation, but intentionally exclude its broadest catch-all selectors.
  const HIGH_CONFIDENCE_SELECTORS = Object.freeze([
    // Nav / launcher
    '#nav-rufus-disco',
    '.nav-rufus-disco',
    '#nav-flyout-rufus',
    '.nav-rufus-content',
    '#nav-xshop-container [href*="rufus"]',
    '.nav-a[href*="rufus"]',
    '#Rufus',

    // Product-page / inline Ask widgets
    '#dpx-nice-widget-container',
    '.dpx-smidget-desktop-pill-list',
    '#dpx-rex-nice-widget-container',
    '#ask_feature_div',
    '#nile-inline-btf_feature_div',
    '#nile-inline_feature_div',
    '[data-feature-name="ask"]',
    '[data-feature-name="nile-inline-btf"]',
    '[data-feature-name="nile-inline"]',

    // Price-history / ingress surfaces
    '#rufus-price-ingress',
    '[class*="rufus-ingress"]',
    '[data-action*="show-rufus-price-ingress"]',

    // Sidebar / conversation UI
    '.rufus-panel-container',
    '#rufus-container',
    '.rufus-container',
    '#rufus-container-main-view',
    '.rufus-container-main-view',
    '.rufus-conversation-container',
    '.rufus-textarea-container',
    '#rufus-sidebar',
    '.rufus-sidebar',
    '#rufus-panel',
    '.rufus-panel',
    '#rufus-wrapper',
    '.rufus-wrapper',
    '[id*="rufus"][id*="sidebar"]',
    '[class*="rufus"][class*="sidebar"]:not([class*="rufus-web-"]):not([class*="orc-rufus-"])',
    '[id*="rufus"][id*="panel"]',
    '[class*="rufus"][class*="panel"]:not([class*="rufus-web-"]):not([class*="orc-rufus-"])',
    '[id*="rufus"][id*="wrapper"]',
    '[class*="rufus"][class*="wrapper"]:not([class*="rufus-web-"]):not([class*="orc-rufus-"])',

    // Known search-result suggestion surfaces
    '.rufus-pill',
    '.s-ask-rufus-mshop-suggestion-container',
    '.s-suggestion-nile-desktop-container',
  ]);

  // Used only to FIND possible candidates. Every result still goes through
  // isSafeRufusCandidate() before any inline hiding is applied.
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

  // If a candidate contains one of these, hiding it would likely remove real content.
  const MAIN_CONTENT_SENTINEL_IDS = Object.freeze([
    'centerCol',
    'rightCol',
    'dp-container',
    'search',
    'pageContent',
  ]);

  const exactSelector = HIGH_CONFIDENCE_SELECTORS.join(',\n');
  const candidateSelector = [
    ...HIGH_CONFIDENCE_SELECTORS,
    ...HEURISTIC_CANDIDATE_SELECTORS,
  ].join(',');

  let aggressiveMode = false;
  let domContentLoaded = document.readyState !== 'loading';
  let windowLoaded = document.readyState === 'complete';
  let bodyObserver = null;
  let domObserver = null;
  let bodyWaitObserver = null;
  let initPollTimer = null;
  let fallbackTimer = null;
  let scanTimer = null;
  let scanAnimationFrame = null;
  const startedAt = performance.now();
  const hiddenElements = new WeakSet();

  function log(...args) {
    if (CONFIG.DEBUG) console.debug('[AlexaSuppressor]', ...args);
  }

  function warn(...args) {
    if (CONFIG.DEBUG) console.warn('[AlexaSuppressor]', ...args);
  }

  function injectStyle(id, cssText) {
    if (document.getElementById(id)) return;
    const style = document.createElement('style');
    style.id = id;
    style.textContent = cssText;
    const parent = document.head || document.documentElement;
    if (parent) parent.appendChild(style);
  }

  function installSoftHideCSS() {
    // Preserve display and dimensions so Amazon can initialize its own Rufus code.
    injectStyle(STYLE_IDS.soft, `
${exactSelector} {
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
${exactSelector} {
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
      if (element.className && typeof element.className.baseVal === 'string') {
        return element.className.baseVal;
      }
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

    // Amazon reuses Rufus-named web components in returns/order workflows.
    if (classes.includes('rufus-web-') || classes.includes('orc-rufus-')) return true;
    if (id.includes('rufus-web-') || id.includes('orc-rufus-')) return true;
    if (id.startsWith('rufus-text') || id.startsWith('rufus-submit')) return true;
    if (slot.includes('rufus-web-') || slot.includes('rufus-input') || slot.includes('rufus-container-submit')) return true;

    // These are children of the nav launcher, not layout/UI containers themselves.
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
      if (element.matches && element.matches(HIGH_CONFIDENCE_SELECTORS.join(','))) return true;
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
      return false; // Fail open.
    }
  }

  function softHideElement(element) {
    if (!isSafeRufusCandidate(element)) return;
    element.style.setProperty('opacity', '0', 'important');
    element.style.setProperty('pointer-events', 'none', 'important');
  }

  function hardHideElement(element) {
    if (!isSafeRufusCandidate(element)) return;
    if (hiddenElements.has(element)) return;

    element.style.setProperty('display', 'none', 'important');
    element.style.setProperty('visibility', 'hidden', 'important');
    element.style.setProperty('opacity', '0', 'important');
    element.style.setProperty('width', '0', 'important');
    element.style.setProperty('height', '0', 'important');
    element.style.setProperty('min-width', '0', 'important');
    element.style.setProperty('min-height', '0', 'important');
    element.style.setProperty('max-width', '0', 'important');
    element.style.setProperty('max-height', '0', 'important');
    element.style.setProperty('overflow', 'hidden', 'important');
    element.style.setProperty('pointer-events', 'none', 'important');
    hiddenElements.add(element);
    log('Hidden', element.id || getClassString(element) || element.tagName);
  }

  function suppressElement(element) {
    if (aggressiveMode) hardHideElement(element);
    else softHideElement(element);
  }

  function rufusSidebarPresent() {
    const selectors = [
      '.rufus-panel-container',
      '#rufus-container',
      '.rufus-container',
      '#rufus-sidebar',
      '.rufus-sidebar',
      '#rufus-panel',
      '.rufus-panel',
      '#nav-flyout-rufus',
    ];
    return selectors.some((selector) => {
      try { return Boolean(document.querySelector(selector)); }
      catch { return false; }
    });
  }

  function isLargeDockPadding(value) {
    if (!value) return false;
    const normalized = String(value).toLowerCase();
    if (normalized.includes('rufus') || normalized.includes('--total-rufus-panel')) return true;
    const numeric = Number.parseFloat(normalized);
    return Number.isFinite(numeric) && numeric > CONFIG.LARGE_DOCK_PADDING_PX;
  }

  function repairDocking() {
    const body = document.body;
    if (!body) return false;

    // Capture evidence BEFORE removing it so padding cleanup is conservative.
    const hadDockClass = RUFUS_DOCK_CLASSES.some((name) => body.classList.contains(name));
    const hadDockProperty = RUFUS_DOCK_PROPERTIES.some((name) => Boolean(body.style.getPropertyValue(name)));
    const hadSidebar = rufusSidebarPresent();
    const hasDockEvidence = hadDockClass || hadDockProperty || hadSidebar;

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

    if (hasDockEvidence) {
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
      // Top padding is only removed when an explicit dock class was present.
      if (hadDockClass && isLargeDockPadding(top)) {
        body.style.removeProperty('padding-top');
        changed = true;
      }
    }

    if (changed) log('Repaired Rufus docking state');
    return changed;
  }

  function scanDocument() {
    repairDocking();
    try {
      const elements = document.querySelectorAll(candidateSelector);
      for (const element of elements) suppressElement(element);
    } catch (error) {
      warn('Candidate scan failed.', error);
    }
  }

  function scheduleScan() {
    if (scanTimer || scanAnimationFrame) return;

    scanTimer = window.setTimeout(() => {
      scanTimer = null;
      scanAnimationFrame = requestAnimationFrame(() => {
        scanAnimationFrame = null;
        scanDocument();
      });
    }, CONFIG.SCAN_DEBOUNCE_MS);
  }

  function inspectAddedNode(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return;
    const element = /** @type {Element} */ (node);

    if (isSafeRufusCandidate(element)) suppressElement(element);

    try {
      const descendants = element.querySelectorAll(candidateSelector);
      for (const descendant of descendants) suppressElement(descendant);
    } catch {
      // Fail open; the scheduled full scan remains a fallback.
    }
  }

  function startDOMObserver() {
    if (domObserver) domObserver.disconnect();

    const target = document.body || document.documentElement;
    if (!target) return;

    domObserver = new MutationObserver((mutations) => {
      let shouldRescan = false;

      for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length) {
          shouldRescan = true;
          for (const node of mutation.addedNodes) inspectAddedNode(node);
          continue;
        }

        if (mutation.type === 'attributes') {
          const targetElement = mutation.target;
          if (targetElement && targetElement.nodeType === Node.ELEMENT_NODE && isSafeRufusCandidate(targetElement)) {
            suppressElement(targetElement);
          }
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
  }

  function startBodyObserver() {
    if (!document.body) return;
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
    // Do not hard-hide before basic document construction has started.
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

    // Do not treat normal page lifecycle as proof that Rufus is initialized.
    // Amazon can inject Alexa late; the controller's absolute timeout handles
    // pages with no Rufus signal without risking an early hard-hide race.
    return false;
  }

  function enterAggressiveMode(reason) {
    if (aggressiveMode) return;
    aggressiveMode = true;
    installHardHideCSS();
    repairDocking();
    scanDocument();
    log('Aggressive mode enabled:', reason);
  }

  function startInitializationController() {
    if (initPollTimer) window.clearInterval(initPollTimer);

    initPollTimer = window.setInterval(() => {
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
      repairDocking();
      scanDocument();
    }, CONFIG.FALLBACK_SCAN_MS);
  }

  function onNavigationSignal(eventName) {
    log('Navigation signal:', eventName);
    repairDocking();
    scheduleScan();
  }

  function init() {
    installSoftHideCSS();

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        domContentLoaded = true;
        whenBodyExists(() => {
          startBodyObserver();
          startDOMObserver();
          scanDocument();
        });
      }, { once: true });
    }

    window.addEventListener('load', () => {
      windowLoaded = true;
      repairDocking();
      scheduleScan();
    }, { once: true });

    window.addEventListener('pageshow', () => onNavigationSignal('pageshow'));
    window.addEventListener('popstate', () => onNavigationSignal('popstate'));

    whenBodyExists(() => {
      startBodyObserver();
      startDOMObserver();
      scanDocument();
    });

    startInitializationController();
    startFallbackRepair();
  }

  try {
    init();
  } catch (error) {
    // Never let the suppressor break Amazon. Logging is intentionally gated.
    warn('Fatal initialization error; leaving Amazon untouched where possible.', error);
  }
})();
