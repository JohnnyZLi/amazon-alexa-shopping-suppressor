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
- [ ] Complete browser regression matrix on the exact release ZIP
- [ ] Decide whether all 23 storefronts remain in the first Web Store release or only validated marketplaces

## Branding / listing assets

Do not use Amazon, Alexa, or Rufus logos as extension artwork.

- [ ] Original 16x16 PNG icon
- [ ] Original 32x32 PNG icon
- [ ] Original 48x48 PNG icon
- [ ] Original 128x128 PNG icon
- [ ] Add manifest `icons` entries
- [ ] 1280x800 screenshots showing normal-width Amazon pages with Alexa/Rufus suppressed
- [ ] 440x280 promotional tile
- [ ] Optional 1400x560 marquee image

## Suggested listing copy

**Working title:** Alexa Shopping Suppressor for Amazon

**Short description:** Removes Alexa for Shopping/Rufus and fixes its blank sidebar gutter. Open source, local-only, no tracking.

**Single purpose:** Suppress Amazon's Alexa for Shopping/Rufus interface and repair page layout space reserved for its docked sidebar.

**Site-access justification:** The extension must read and modify DOM elements on supported Amazon retail pages to identify Alexa/Rufus interface surfaces, hide them, and remove Rufus-specific dock layout state. Processing is local to the browser.

**Remote code:** No.

**Data collection:** None.

Include prominently in the listing: **Unofficial; not affiliated with or endorsed by Amazon.**

## Legal / policy

- [x] MIT license
- [x] Privacy policy in repository
- [x] Security policy in repository
- [ ] Publish privacy policy at a stable public URL suitable for the Web Store dashboard
- [ ] Confirm developer account and 2-Step Verification
- [ ] Pay/confirm Chrome Web Store developer registration fee
- [ ] Review final listing against current Chrome Web Store policies before submission

## Release procedure

1. Update `manifest.json` version.
2. Update `CHANGELOG.md` and README status.
3. Run `python scripts/validate.py`.
4. Run `python scripts/package.py`.
5. Test the exact ZIP from `dist/` by loading it unpacked from an extracted copy.
6. Complete the regression matrix.
7. Commit and push.
8. Tag the exact commit as `vX.Y.Z`.
9. The release workflow validates, packages, and creates the GitHub Release with the ZIP and SHA-256 file.
10. Submit that exact ZIP to the Chrome Web Store.
