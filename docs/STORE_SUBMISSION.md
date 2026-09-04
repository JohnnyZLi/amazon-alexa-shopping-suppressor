# Chrome Web Store release checklist

This document tracks the remaining work between the current release candidate and a public Chrome Web Store submission.

## Runtime / code

- [x] Manifest V3
- [x] HTTPS-only retail host scope
- [x] No privileged Chrome API permissions
- [x] No background/service worker
- [x] No storage, telemetry, network requests, or remote code
- [x] Broad selectors routed through fail-open JavaScript validation
- [x] Managed inline styles are restorable if element identity changes
- [x] Dock-padding repair requires explicit Rufus dock evidence
- [x] Recognized checkout/returns routes are intentionally inactive
- [x] Deterministic packaging script
- [x] CI validation
- [x] Tag-driven GitHub release packaging
- [x] Manifest icon set: 16, 32, 48, 128 px
- [x] Validator checks icon presence and exact PNG dimensions
- [x] Manual browser regression plan documented in `docs/TEST_PLAN.md`
- [ ] Complete browser regression matrix on the exact release ZIP
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

The Chrome Web Store graphics are distributed as a separate submission bundle rather than inside the runtime extension ZIP. See `docs/ASSETS.md`.

## Listing copy

- [x] Full listing draft in `docs/STORE_LISTING.md`
- [x] Single-purpose statement drafted
- [x] Site-access justification drafted
- [x] Remote-code declaration drafted
- [x] Data-use disclosure drafted
- [x] Unofficial/non-affiliation statement drafted
- [x] Stable public privacy-policy URL selected
- [x] Public support URL selected

**Working title:** Alexa Shopping Suppressor for Amazon

**Short description:** Removes Alexa for Shopping/Rufus and fixes its blank sidebar gutter. Open source, local-only, no tracking.

## Legal / policy

- [x] MIT license
- [x] Privacy policy in repository
- [x] Security policy in repository
- [x] Public support guidance in `SUPPORT.md`
- [x] Privacy policy URL: https://github.com/JohnnyZLi/amazon-alexa-shopping-suppressor/blob/main/PRIVACY.md
- [x] Support URL: https://github.com/JohnnyZLi/amazon-alexa-shopping-suppressor/issues
- [ ] Confirm Chrome Web Store developer account
- [ ] Confirm 2-Step Verification on the publisher Google account
- [ ] Pay/confirm Chrome Web Store developer registration fee
- [ ] Review final listing against current Chrome Web Store policies immediately before submission

## Manual actions that cannot be automated from this repository

The following require the publisher's authenticated Google/Chrome session and cannot be completed by GitHub Actions:

1. Chrome Web Store developer registration/payment.
2. Publisher identity/account settings and 2-Step Verification.
3. Uploading the final ZIP and store graphics to the Web Store dashboard.
4. Completing the dashboard privacy/permission declarations.
5. Clicking the final submission/publish controls.

## Release procedure

1. Complete `docs/TEST_PLAN.md` on the exact candidate build.
2. Resolve regressions, if any.
3. Decide first-release marketplace scope.
4. Update `manifest.json` version to `1.0.0`.
5. Update `CHANGELOG.md` and README status.
6. Run `python scripts/validate.py`.
7. Run `python scripts/package.py`.
8. Test the exact ZIP from `dist/` by extracting it and loading that extracted copy unpacked.
9. Commit and push.
10. Tag the exact commit as `v1.0.0`.
11. The release workflow validates, packages, and creates the GitHub Release with ZIP + SHA-256.
12. Submit that exact ZIP and the separate Web Store graphics bundle to the Chrome Web Store.
