# Chrome Web Store release checklist

This document tracks the remaining work between the current release candidate and a public Chrome Web Store submission.

## Runtime / code

- [x] Manifest V3
- [x] HTTPS-only retail host scope
- [x] Exactly one Chrome API permission: `storage`
- [x] `storage` is used only for the local boolean On/Off preference
- [x] No background/service worker
- [x] No telemetry, network requests, or remote code
- [x] No tabs/scripting/activeTab/history/downloads/cookies/webRequest permissions
- [x] Toolbar popup with persistent Suppressor On/Off switch
- [x] Popup follows light/dark `prefers-color-scheme` without storing another preference
- [x] Saved-Off startup waits for the persisted preference before suppression can activate
- [x] Toggle Off restores managed element styles and recorded Rufus dock state
- [x] Toggle On resumes suppression without a reload on non-sensitive pages
- [x] Broad selectors routed through fail-open JavaScript validation
- [x] Managed inline styles are restorable if element identity changes
- [x] Dock-padding repair requires explicit Rufus dock evidence
- [x] Recognized checkout/returns routes are intentionally inactive
- [x] Sensitive-route deactivation restores recorded Rufus dock state
- [x] Same-document pushState/replaceState route changes are observed through the Chromium Navigation API
- [x] Deterministic packaging script includes popup runtime assets
- [x] Static/security CI validation
- [x] Synthetic Chromium regression suite
- [x] Adversarial Chromium regression suite
- [x] Synthetic tests cover startup-disabled, live Off/On, popup persistence, and sensitive-flow restoration behavior
- [x] Adversarial tests cover toggle storms, two open tabs, style-rewrite fights, sensitive-flow interleaving, and long-lived churn
- [x] Real Chromium persistence test across complete browser-process restarts
- [x] CI uploads the exact candidate ZIP + SHA-256 artifact
- [x] Tag-driven GitHub release packaging
- [x] Release workflow re-runs static, synthetic, and adversarial browser checks before publishing
- [x] Manifest icon set: 16, 32, 48, 128 px
- [x] Validator checks icon presence and exact PNG dimensions
- [x] 128px store icon generator follows Chrome Web Store 96px-artwork / 16px-padding square-icon guidance
- [x] Manual browser regression plan documented in `docs/TEST_PLAN.md`
- [x] Live real-extension smoke coverage across all 23 supported Amazon marketplaces
- [x] First-release marketplace scope decision: retain all 23 supported storefronts
- [ ] Complete remaining deep Amazon US release acceptance on the exact release line
- [ ] Complete authenticated Amazon Orders / Account / Checkout / Returns acceptance in the publisher's normal Chrome session

## Branding / listing assets

All extension artwork is original and does not use Amazon, Alexa, or Rufus logos.

- [x] Original 16x16 PNG icon
- [x] Original 32x32 PNG icon
- [x] Original 48x48 PNG icon
- [x] Original 128x128 PNG icon
- [x] Manifest `icons` entries
- [x] 1280x800 before/after screenshot
- [x] 1280x800 full-width result screenshot
- [x] 1280x800 targeted-UI screenshot
- [x] 440x280 promotional tile
- [x] Optional 1400x560 marquee image
- [x] Source screenshots cropped to remove account name, delivery address, and other identifying header information
- [x] Capture current redesigned popup in real Chromium in light, dark, and Off states for release evidence
- [ ] Produce/select the final 1280x800 or 640x400 store screenshot that includes the current toolbar-popup experience

The Chrome Web Store graphics are distributed as a separate submission bundle rather than inside the runtime extension ZIP. See `docs/ASSETS.md`.

## Listing copy

- [x] Full listing draft in `docs/STORE_LISTING.md`
- [x] Single-purpose statement drafted
- [x] Site-access justification drafted
- [x] `storage` permission justification drafted
- [x] Remote-code declaration drafted
- [x] Data-use disclosure drafted, including the local `enabled` setting
- [x] Local DOM-processing behavior disclosed
- [x] Unofficial/non-affiliation statement drafted
- [x] Public support URL selected
- [x] Public repository privacy-policy fallback selected
- [x] Pages-ready privacy-policy route prepared at `docs/privacy/index.html`
- [x] Re-reviewed single-purpose, permissions/data-use, listing-image, 2-Step Verification, and current Web Store API guidance on 2026-09-07
- [ ] Enable/verify the optional polished GitHub Pages privacy-policy URL before Web Store submission, or keep the public repository privacy URL

**Working title:** Alexa Shopping Suppressor for Amazon

**Short description:** Removes Alexa for Shopping/Rufus and its blank sidebar gutter. Open source, on/off control, no tracking.

## Legal / policy

- [x] MIT license
- [x] Privacy policy documents the local On/Off preference
- [x] Security policy documents the storage-only capability surface
- [x] Public support guidance in `SUPPORT.md`
- [x] Repository fallback privacy URL: https://github.com/JohnnyZLi/amazon-alexa-shopping-suppressor/blob/main/PRIVACY.md
- [x] Support URL: https://github.com/JohnnyZLi/amazon-alexa-shopping-suppressor/issues
- [x] GitHub Pages landing/privacy files prepared under `docs/`
- [x] Current policy review confirms the extension remains a narrow single-purpose product and requests no unrelated Chrome API permissions
- [x] Current data-use review confirms no analytics, telemetry, remote transmission, sale, or sharing of user data
- [ ] Enable/verify GitHub Pages if using the polished Pages URL instead of the repository privacy URL
- [ ] Confirm Chrome Web Store developer account
- [ ] Confirm 2-Step Verification on the publisher Google account
- [ ] Pay/confirm the one-time Chrome Web Store developer registration fee (currently $5 for a new publisher account)

## Manual actions that still require the publisher

The following require the publisher's authenticated Amazon/Google/Chrome session or repository settings not exposed by the current connector:

1. Signed-in Amazon acceptance for actual Orders, Account, Checkout, and Returns controls.
2. Enabling GitHub Pages if the polished Pages privacy URL is desired; the public repository privacy URL is already a viable fallback.
3. Chrome Web Store developer registration/payment if not already complete.
4. Publisher identity/account settings and 2-Step Verification.
5. Uploading the final ZIP and store graphics to the Web Store dashboard.
6. Completing/confirming the dashboard Store Listing and Privacy declarations.
7. Clicking the final submission/publish controls.

## Release procedure

1. Confirm all normal CI gates are green.
2. Complete the deep live Amazon US acceptance pass and record any Amazon-runner limitations separately from extension failures.
3. Complete the signed-in Orders / Account / Checkout / Returns checks in the publisher's normal Chrome session.
4. Resolve any regression found by those checks.
5. Confirm the final store screenshot and privacy-policy URL.
6. Update `manifest.json` to `1.0.0` and finalize `CHANGELOG.md` / README release status.
7. Run static validation, synthetic Chromium regressions, adversarial Chromium regressions, and deterministic packaging.
8. Download and inspect the exact `extension-candidate-<commit SHA>` artifact from the final candidate commit.
9. Extract that exact ZIP and perform the final install smoke check.
10. Merge the final release preparation commit(s) to `main`.
11. Tag the exact release commit as `v1.0.0`.
12. The release workflow re-validates, re-tests, packages, verifies the tag/version match, and creates the GitHub Release with ZIP + SHA-256.
13. Submit that exact ZIP and the separate Web Store graphics bundle to the Chrome Web Store.
