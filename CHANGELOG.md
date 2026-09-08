# Changelog

## 1.0.0 — 2026-09-07

First public-release candidate after live marketplace validation and Chrome Web Store preparation.

- Keeps the narrow single purpose: suppress Amazon Alexa for Shopping/Rufus UI and reclaim layout space reserved for its docked sidebar.
- Ships the persistent toolbar **Suppressor On/Off** control using exactly one Chrome API permission, `storage`, for the local boolean preference.
- Turning Off restores extension-managed Rufus styles and recorded dock state immediately; turning On resumes suppression on normal Amazon pages without a reload.
- Includes the saved-Off startup race fix found through real persistent-profile Chromium testing.
- Includes sensitive checkout/returns fail-open behavior and restoration across same-document navigation.
- Fixes the post-purchase order-confirmation regression: known thank-you/order-confirmation routes resume Rufus suppression and dock-gutter repair after payment while active checkout remains untouched.
- Includes the compact redesigned toolbar popup with automatic light/dark `prefers-color-scheme` support and explicit local/no-tracking copy.
- Retains all 23 explicitly scoped HTTPS Amazon retail storefronts after live real-extension testing across every supported marketplace produced no extension-side failures.
- Adds permanent synthetic and adversarial Chromium release gates, including toggle storms, multi-tab propagation, style-rewrite recovery, sensitive-flow interleaving, and long-lived mutation/dock churn.
- Adds release validation evidence and refreshed Chrome Web Store listing/privacy/permission documentation.
- Updates the 128x128 install/Web Store icon to a 96x96 artwork box with 16px transparent padding on every side and adds a validator assertion for that padding.
- Adds a current popup-focused 1280x800 store screenshot and simplifies promotional artwork to be more brand-focused.
- Runtime remains local-only: no analytics, telemetry, remote code, network requests, service worker, cookies, history, tabs, scripting, or activeTab access.

## 0.3.2 — 2026-09-06

Sensitive-flow restoration and same-document navigation hardening.

- Restores recorded Rufus dock classes, width variables, and associated body padding when a running suppressor transitions into checkout or returns instead of leaving layout changes behind.
- Restores dock state on fatal deactivation as part of the fail-open path.
- Watches Chromium's Navigation API `currententrychange` event so `history.pushState()` / `replaceState()` transitions into sensitive routes deactivate immediately and transitions back to normal Amazon pages resume suppression without a reload.
- Strengthened synthetic Chromium coverage to assert dock restoration/resuppression across both `popstate` and Navigation API same-document transitions.
- Independently exercised all 46 exact bare/www Amazon HTTPS host patterns with the real unpacked extension; unlisted hosts remained untouched.

## 0.3.1 — 2026-09-05

Startup preference race fix.

- Fixed a real-Chrome startup race where a saved **Off** preference could lose to an early `pageshow` event while `chrome.storage.local.get()` was still resolving, activating suppression before the preference was known.
- Suppression activation is now gated on an explicit `preferenceLoaded` state, so a fresh Amazon page remains untouched while saved Off is being loaded.
- Storage-change events that arrive during startup remain authoritative and cannot be overwritten by a stale initial read.
- Added a synthetic Chromium regression that deliberately delays the storage read and fires `pageshow` before it resolves.

## 0.3.0 — 2026-09-04

User control plus release-preflight automation and publication preparation.

- Added a toolbar popup with a persistent **Suppressor On/Off** switch.
- Added exactly one Chrome API permission, `storage`, used only for the local boolean `enabled` preference.
- Turning the suppressor Off immediately disconnects observers/timers, removes injected styles, restores managed Rufus element styles, and restores Rufus dock classes/styles removed by the extension on the current page.
- Turning the suppressor back On resumes suppression immediately on non-sensitive Amazon pages without requiring a reload.
- Disabled-at-start behavior leaves Amazon untouched while preserving the Off preference across Chrome restarts.
- Added popup assets to deterministic release packaging and expanded static validation to enforce the storage-only permission/API policy.
- Added synthetic Chromium coverage for startup-disabled behavior, live Off→On restoration/resumption, and popup preference persistence.
- Added a synthetic Chromium regression suite that executes the production content script against controlled DOM fixtures.
- Added automated checks for soft/hard suppression, guarded-selector safety, page-shell protection, dynamic style restoration, style rewrite re-suppression, dock repair, sensitive-route inactivity, and safe/sensitive navigation transitions.
- Added the synthetic browser suite to push/PR CI and to the tag-driven release workflow.
- CI now uploads the exact deterministic candidate ZIP and SHA-256 artifact for manual validation.
- Added a pinned development-only Playwright dependency; the runtime extension remains dependency-free.
- Added GitHub Pages-ready landing and privacy-policy routes under `docs/`.
- Updated the release test plan, privacy/security documentation, and Chrome Web Store checklist to distinguish automated preflight from required live Amazon validation.

## 0.2.0 — 2026-09-04

Public-release hardening and release infrastructure.

- Moved generic `.rufus-*` container classes out of unconditional CSS and into the guarded JavaScript suppression path.
- Replaced one-way `WeakSet` hiding with tracked, idempotent inline-style management.
- Added restoration of original inline style values when a dynamic element stops matching the Rufus/Alexa safety policy.
- Added managed-element style observation so Amazon cannot permanently re-enable a safe Rufus candidate by rewriting its inline styles.
- Tightened dock repair: generic numeric body padding now requires an explicit Rufus dock class or Rufus dock-width custom property on the same pass.
- Added sensitive-flow protection that keeps the extension inactive on recognized checkout and returns routes and deactivates on matching navigation signals.
- Increased fallback scan interval from 2.5s to 5s while retaining mutation-driven handling.
- Updated the manifest description and added the repository homepage URL without adding any privileged Chrome permissions.
- Added dependency-free validation and deterministic ZIP packaging scripts.
- Added push/PR validation and tag-driven GitHub Release workflows.
- Added MIT license, privacy policy, security policy, `.gitignore`, and Chrome Web Store release checklist.

## 0.1.1 — 2026-09-03

Security-hardening release with no intended change to Alexa/Rufus suppression behavior.

- Narrowed content-script scope from `*://*.amazon...` patterns to exact bare/`www` retail hosts over HTTPS only.
- Removed execution on arbitrary Amazon subdomains and HTTP pages.
- Split Rufus/Alexa selectors into unconditional `STATIC_SAFE_SELECTORS` and JavaScript-guarded `GUARDED_SELECTORS`.
- Broad substring/generic attribute selectors now pass through `isSafeRufusCandidate()` instead of bypassing fail-open checks through CSS.
- Updated README security wording to distinguish privileged Chrome API permissions from content-script site access.

## 0.1.0 — 2026-09-01

Initial known-good baseline.

- Manifest V3 Chrome extension with no privileged permissions, background worker, storage, popup, network requests, or remote code.
- Two-phase Alexa/Rufus suppression: soft-hide first, hard-hide after initialization.
- Rufus docking-class/CSS-variable cleanup and body-padding repair.
- Dedicated body observer plus DOM reinjection observer.
- Guarded heuristic Rufus candidate detection with page-shell and returns-flow protections.
- Explicit support scope for 23 Amazon retail domains.
- User-confirmed fix for the Amazon Alexa for Shopping blank-sidebar-gutter failure mode.
