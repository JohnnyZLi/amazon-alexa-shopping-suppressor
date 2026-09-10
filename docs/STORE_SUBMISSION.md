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
- [x] Known post-purchase thank-you/order-confirmation routes resume suppression and gutter repair
- [x] Sensitive-route deactivation restores recorded Rufus dock state
- [x] Same-document pushState/replaceState route changes are observed through the Chromium Navigation API
- [x] Deterministic packaging script includes popup runtime assets
- [x] Static/security CI validation
- [x] Synthetic Chromium regression suite
- [x] Adversarial Chromium regression suite
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
- [x] Deep Amazon US acceptance on the 1.0.0 release tree: homepage, search, product, cart, direct/external navigation, Back/Forward, resize, two-tab toggle, saved-Off fresh tab, public account/orders routes, checkout/returns route inactivity, popup light/dark behavior, and live-tab stability all passed
- [x] Earlier 30-minute live Amazon tab acceptance passed; the final 1.0.0-tree rerun used a shorter live-tab interval because the runtime delta was already covered by release CI and confirmation-route regression tests
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
- [x] 1280x800 current popup-control screenshot
- [x] 440x280 promotional tile
- [x] Optional 1400x560 marquee image
- [x] Source screenshots cropped to remove account name, delivery address, and other identifying header information
- [x] Current redesigned popup captured in real Chromium in light, dark, and Off states for release evidence

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
- [x] Current Web Store requirements re-reviewed before release handoff
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

The remaining manual gate is intentionally small:

1. In a fresh Chrome profile, load the exact final ZIP once and confirm the new install defaults to Suppressor **On**.
2. In the normal signed-in Amazon session, smoke-test actual Orders, Account, Checkout, and Returns controls; exercise normal→checkout→normal and normal→returns→normal once, and repeat one sensitive transition while the suppressor is saved Off.
3. A live signed-in post-purchase confirmation retest can wait until the next natural purchase; do not place an order solely for testing.
4. Register/verify the Chrome Web Store publisher account, enable Google 2-Step Verification, upload the final ZIP and separate store assets, complete Store Listing + Privacy + Distribution, and submit for review.
5. GitHub Pages is optional; the public repository privacy-policy URL is already a viable fallback.

## Release procedure

1. `1.0.0` release preparation is merged to `main` and main CI is green.
2. Complete the short publisher-only signed-in Amazon smoke test above.
3. Resolve any regression found by that check.
4. Tag the exact accepted `main` commit as `v1.0.0`.
5. The release workflow re-validates, re-tests, packages, verifies the tag/version match, and creates the GitHub Release with ZIP + SHA-256.
6. Submit that exact release ZIP and the separate Web Store graphics bundle to the Chrome Web Store.
