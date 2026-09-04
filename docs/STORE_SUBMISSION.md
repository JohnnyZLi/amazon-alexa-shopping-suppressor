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
- [x] Toggle Off restores managed element styles and recorded Rufus dock state
- [x] Toggle On resumes suppression without a reload on non-sensitive pages
- [x] Broad selectors routed through fail-open JavaScript validation
- [x] Managed inline styles are restorable if element identity changes
- [x] Dock-padding repair requires explicit Rufus dock evidence
- [x] Recognized checkout/returns routes are intentionally inactive
- [x] Deterministic packaging script includes popup runtime assets
- [x] Static/security CI validation
- [x] Synthetic Chromium regression suite
- [x] Synthetic tests cover startup-disabled, live Off/On, and popup persistence behavior
- [x] CI uploads the exact candidate ZIP + SHA-256 artifact
- [x] Tag-driven GitHub release packaging
- [x] Release workflow re-runs static and synthetic browser checks before publishing
- [x] Manifest icon set: 16, 32, 48, 128 px
- [x] Validator checks icon presence and exact PNG dimensions
- [x] Manual browser regression plan documented in `docs/TEST_PLAN.md`
- [ ] Complete live Amazon browser regression matrix on the exact release ZIP
- [ ] Complete live toolbar toggle matrix on the exact release ZIP
- [ ] Decide whether all 23 storefronts remain in the first Web Store release or only validated marketplaces

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
- [ ] Capture one current release screenshot showing the toolbar popup and On/Off switch

The Chrome Web Store graphics are distributed as a separate submission bundle rather than inside the runtime extension ZIP. See `docs/ASSETS.md`.

## Listing copy

- [x] Full listing draft in `docs/STORE_LISTING.md`
- [x] Single-purpose statement drafted
- [x] Site-access justification drafted
- [x] `storage` permission justification drafted
- [x] Remote-code declaration drafted
- [x] Data-use disclosure drafted, including the local `enabled` setting
- [x] Unofficial/non-affiliation statement drafted
- [x] Public support URL selected
- [x] Pages-ready privacy-policy route prepared at `docs/privacy/index.html`
- [ ] Enable/verify the final public privacy-policy URL before Web Store submission

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
- [ ] Enable/verify GitHub Pages (or another stable HTTPS host) for the polished privacy URL
- [ ] Confirm Chrome Web Store developer account
- [ ] Confirm 2-Step Verification on the publisher Google account
- [ ] Pay/confirm Chrome Web Store developer registration fee
- [ ] Review final listing and `storage` permission disclosure against current Chrome Web Store policies immediately before submission

## Manual actions that cannot be automated from this repository

The following require the publisher's authenticated Google/Chrome session or repository settings that are not exposed by the current connector:

1. Live Amazon regression testing in the publisher's normal Chrome session.
2. Live verification of the toolbar popup, persisted Off state across a Chrome restart, and propagation to already-open Amazon tabs.
3. Final first-release marketplace-scope decision based on those live tests.
4. Capturing the final real-browser popup screenshot for the store listing.
5. Enabling/verifying GitHub Pages if repository settings require an account-level action.
6. Chrome Web Store developer registration/payment.
7. Publisher identity/account settings and 2-Step Verification.
8. Uploading the final ZIP and store graphics to the Web Store dashboard.
9. Completing the dashboard privacy/permission declarations.
10. Clicking the final submission/publish controls.

## Release procedure

1. Confirm CI is green, including `scripts/browser_smoke.py`.
2. Download the `extension-candidate-<commit SHA>` CI artifact for the exact candidate commit.
3. Complete `docs/TEST_PLAN.md` against that exact candidate ZIP in live Amazon, including the On/Off toggle matrix.
4. Resolve regressions, if any.
5. Decide first-release marketplace scope.
6. Capture the current toolbar-popup screenshot.
7. Update `manifest.json` version to `1.0.0`.
8. Update `CHANGELOG.md` and README status.
9. Run `python scripts/validate.py`.
10. Run `python scripts/browser_smoke.py`.
11. Run `python scripts/package.py`.
12. Test the exact ZIP from `dist/` by extracting it and loading that extracted copy unpacked.
13. Commit and push.
14. Tag the exact commit as `v1.0.0`.
15. The release workflow validates, browser-smoke-tests, packages, and creates the GitHub Release with ZIP + SHA-256.
16. Submit that exact ZIP and the separate Web Store graphics bundle to the Chrome Web Store.
