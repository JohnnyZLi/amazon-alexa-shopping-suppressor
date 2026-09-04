# Changelog

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
