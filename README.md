# Amazon Alexa for Shopping Suppressor

**Version:** 1.0.0 release preparation  
**Status:** pre-release acceptance / Chrome Web Store preparation  
**Platform:** Chrome / Chromium, Manifest V3  
**Purpose:** suppress Amazon's Alexa for Shopping / Rufus UI without leaving the large blank docked-sidebar gutter.

This is an unofficial open-source browser extension and is not affiliated with, endorsed by, or sponsored by Amazon.

## Why this exists

Static cosmetic blocking can remove the visible Alexa/Rufus panel before Amazon finishes initializing its own layout state. On affected Amazon layouts, that can leave the page shifted to the right with a large empty gutter where the sidebar would have been.

This extension takes a state-aware approach:

1. **Soft-hide immediately at `document_start`.** Exact Alexa/Rufus surfaces are made invisible and non-interactive without immediately collapsing their dimensions.
2. **Let Amazon initialize.** The extension gives the page a conservative initialization window so Amazon can finish constructing/measuring Rufus.
3. **Hard-hide after initialization.** Once initialization is safely underway, the extension collapses the Alexa/Rufus UI.
4. **Repair explicit dock state.** It removes Rufus docking classes, Rufus-specific width variables, and large body padding only when explicit Rufus dock evidence exists.
5. **Keep repairing dynamically.** Mutation observers catch Amazon re-injecting Rufus UI or restoring dock state, with a slower fallback scan as a safety net.
6. **Fail open.** Broad Rufus matches are candidates only and must pass safety checks before being hidden. Structural Amazon page containers are explicitly protected.
7. **Restore dynamic elements.** If an element previously managed by the extension later stops matching the Rufus/Alexa safety policy, the extension restores the inline style values it replaced.
8. **Stay out of sensitive flows.** Recognized checkout and returns routes are intentionally left untouched.
9. **Give the user an immediate off switch.** The toolbar popup stores one local `enabled` boolean. Turning the suppressor off restores managed Rufus element styles and the dock state removed by the extension; turning it back on resumes suppression without reloading the page.

The extension does **not** remove Amazon DOM nodes. It suppresses UI with styling and repairs layout state so Amazon's own scripts can continue to find elements they expect.

## On / off toggle

Click the extension icon in the Chrome toolbar and switch **Suppressor** on or off.

- **On** is the default.
- The preference persists across Chrome restarts using `chrome.storage.local`.
- The only stored value is a boolean named `enabled`.
- Turning it off immediately disconnects the suppressor, removes its injected styles, restores managed inline styles, and restores Rufus dock classes/styles that the extension had removed on that page.
- Turning it back on immediately resumes normal suppression on non-sensitive Amazon pages.
- Checkout and recognized returns routes remain untouched regardless of the toggle state.
- The popup automatically follows the browser/system light or dark color scheme; no extra theme setting or permission is stored.

## Security / privacy model

The 1.0 release line intentionally keeps a small capability surface:

- Manifest V3
- Exactly one Chrome API permission: **`storage`**, used only to remember the local on/off preference
- Content-script site access limited to explicitly listed Amazon retail hosts over HTTPS
- One toolbar action with a local popup
- No background/service worker
- No network requests
- No remote code or runtime dependencies
- No analytics or telemetry
- No cookies/history/downloads/webRequest access
- No `tabs`, `scripting`, `activeTab`, or other privileged Chrome APIs
- No `localStorage`, `sessionStorage`, IndexedDB, or page-cookie persistence
- The only extension-persisted state is the local `enabled` boolean
- One static content script running at `document_start` in the isolated world
- No wildcard access to arbitrary Amazon subdomains
- Broad selectors require fail-open JavaScript validation
- Inline changes made by guarded suppression are tracked and reversible
- User-triggered disable also restores dock classes/styles removed by the extension
- Generic numeric dock padding is changed only with explicit Rufus dock evidence
- Recognized checkout and returns routes are intentionally inactive

See [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md), and [SUPPORT.md](SUPPORT.md).

## Supported Amazon storefronts

The first public release is scoped to 23 retail domains: United States, Canada, Mexico, Brazil, United Kingdom, Germany, France, Italy, Spain, Netherlands, Belgium, Sweden, Poland, Ireland, Turkey, United Arab Emirates, Saudi Arabia, Egypt, South Africa, Japan, India, Singapore, and Australia.

Each marketplace is limited to its bare retail hostname and `www` hostname over HTTPS.

The real unpacked extension has been exercised on live pages across **all 23 supported storefronts**. Twenty storefronts passed homepage + search + product + Off/On propagation in the first automated live sweep. Amazon challenged the runner's exact `/s` request on Germany/France and treated Poland's `/s` response as a download, so those three were retried from a fresh runner using alternate live browse pages plus direct product pages; all three passed extension activation and Off/On behavior. No supported marketplace produced an extension-side failure.

## Sensitive-flow safeguard

The extension intentionally remains inactive when the Amazon path matches a recognized checkout or returns route, including the common `/gp/buy/`, `/checkout/`, `/hz/checkout/`, `/spr/returns/`, `/hz/returns/`, and `/gp/your-account/returns/` families.

If a browser navigation signal reaches one of these paths in the same document, the extension deactivates, disconnects observers/timers, removes its injected styles, and restores tracked inline styles and recorded dock state. Returning to a normal Amazon page resumes suppression when the saved toggle is On.

The safeguard favors false negatives over modifying transaction-sensitive pages.

## Install locally in Chrome

1. Clone or download the repository, or extract the exact candidate/release ZIP.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select the folder containing `manifest.json`.
6. Disable/remove any other Alexa/Rufus suppressor so two extensions are not fighting each other.
7. Remove experimental Alexa/Rufus custom rules previously added to uBlock Origin Lite. uBO Lite itself can remain enabled normally.
8. Close existing Amazon tabs and open a fresh Amazon tab for testing.
9. Click the extension toolbar icon to confirm the **Suppressor** toggle is available and defaults to **On**.

## Validation and deterministic packaging

The runtime extension has no package manager, build system, or third-party runtime dependency.

Static validation and packaging require only Python + Node:

```bash
python scripts/validate.py
python scripts/package.py
```

For the browser regression suites used by CI:

```bash
python -m pip install -r requirements-dev.txt
python scripts/browser_smoke.py
python scripts/adversarial_smoke.py
```

`validate.py` checks the Manifest V3 capability surface, exact HTTPS Amazon host scope, storage-only permission policy, popup assets, JavaScript syntax, forbidden network/persistence/API patterns, sensitive-flow safeguards, selector-hardening invariants, exact icon dimensions, and Chrome Web Store padding for the 128px install icon.

`browser_smoke.py` executes the production `content.js` logic inside real Chromium DOM fixtures with test-only accelerated timers. It covers soft/hard suppression, guarded candidate safety, page-shell protection, dynamic style restoration, style rewrite re-suppression, dock repair, sensitive-route inactivity, transitions into/out of sensitive flows, disabled-at-start behavior, live Off/On restoration and resumption, and popup preference persistence.

`adversarial_smoke.py` adds toggle storms, two-tab state propagation, repeated sensitive-flow interleaving, Amazon-like inline-style fights across On/Off cycles, and accelerated long-lived mutation/dock churn.

`package.py` produces a deterministic Chrome extension ZIP in `dist/` and a matching SHA-256 file. It includes only the manifest-referenced runtime files plus local assets referenced by the popup.

GitHub Actions runs static validation, both Chromium regression suites, and deterministic packaging on pushes and pull requests. Each successful CI run uploads the exact candidate ZIP + SHA-256 as an artifact. Pushing a matching `vX.Y.Z` tag repeats the gates, verifies the tag matches the manifest version, and publishes the ZIP + checksum as a GitHub Release.

Real-browser evidence also includes persistent-profile testing with actual `chrome.storage.local` across full Chromium process restarts and live marketplace testing across all 23 storefronts. See [docs/VALIDATION.md](docs/VALIDATION.md).

## Debugging

Set `DEBUG: true` near the top of `content.js`, reload the extension, then open Amazon DevTools → **Console**. Messages are prefixed with `[AlexaSuppressor]`.

## Test matrix

Legend: ✅ confirmed · ⬜ still requires final acceptance · ⚠️ regression · ➖ intentionally inactive

| Scenario | 1.0 prep | Evidence / expected behavior |
|---|---:|---|
| Original Amazon US Rufus/sidebar failure | ✅ | User-confirmed suppression and gutter repair |
| Toggle Off on live Amazon | ✅ | Rufus + sidecar/dock state restore immediately |
| Toggle On again on live Amazon | ✅ | Suppression resumes without reload |
| Chrome restart with toggle Off | ✅ | Real persistent Chromium profile keeps Off |
| Chrome restart with toggle On | ✅ | Real persistent Chromium profile keeps On |
| Two open tabs / preference propagation | ✅ | Real storage API + permanent adversarial regression |
| All 23 supported marketplaces | ✅ | Live real-extension sweep + DE/FR/PL focused retries |
| Homepage/search/product general behavior | ✅ | Live marketplace sweep; exact DE/FR/PL `/s` requests were Amazon-runner-limited and retried on alternate live pages |
| Dynamic Rufus element changes identity | ✅ | Synthetic Chromium regression restores prior inline changes |
| Amazon rewrites managed element style | ✅ | Synthetic/adversarial regressions re-apply suppression while safe |
| Rapid repeated toggle changes | ✅ | 120+ state-change adversarial regression |
| Long-lived mutation/dock churn | ✅ | Accelerated adversarial regression |
| Deep Amazon US navigation/resize/30-minute tab pass | ⬜ | Dedicated live acceptance run required before final tag |
| Your Orders — authenticated | ⬜ | Publisher's signed-in Amazon session required |
| Account pages — authenticated | ⬜ | Publisher's signed-in Amazon session required |
| Checkout — authenticated | ➖ | Suppressor must remain inactive; signed-in acceptance required |
| Returns — authenticated | ➖ | Suppressor must remain inactive; signed-in acceptance required |

The detailed procedure is in [docs/TEST_PLAN.md](docs/TEST_PLAN.md). The live acceptance tracker is GitHub issue #2.

## Acceptance criteria for 1.0.0

- Alexa for Shopping / Rufus never becomes meaningfully visible on supported non-sensitive pages while the suppressor is On.
- No left/right blank gutter remains after Rufus suppression.
- Main Amazon page content retains its normal width and position.
- Late-injected Rufus components remain suppressed.
- Dynamic candidates that stop being Rufus/Alexa are restored.
- Product/search/cart/account layouts remain usable.
- Checkout and recognized returns flows remain untouched.
- No page-shell or primary content container is hidden.
- Turning the suppressor Off restores extension-managed element styles and recorded dock state on the current page.
- The Off preference persists across Chrome restarts and leaves Amazon untouched on new pages.
- The only persisted extension state is the local `enabled` boolean.
- No network access or remote dependency is introduced.
- No Chrome API permission beyond `storage` is added without a documented reason and fresh review.
- No recurring console exceptions or obvious idle CPU loop is introduced.
- Static validation plus synthetic and adversarial Chromium regression checks are green.
- Live marketplace validation remains green across the supported scope.
- Authenticated Amazon transaction/account flows receive a final publisher smoke test before Web Store submission.

## Chrome Web Store preparation

Code hardening, release automation, live 23-marketplace coverage, icons, store graphics, listing copy, legal/privacy documentation, popup light/dark evidence, synthetic/adversarial regression automation, and the user-facing On/Off control are prepared.

The 128x128 install/Web Store icon follows Chrome Web Store square-icon sizing guidance with a 96x96 artwork box and 16px transparent padding. Store screenshots are 1280x800, the required small promotional tile is 440x280, and an optional 1400x560 marquee is prepared.

Remaining release gates are the deep Amazon US acceptance run, the publisher's signed-in Orders/Account/Checkout/Returns smoke tests, and authenticated Chrome Web Store account/dashboard/submission actions. GitHub Pages is optional because the public repository privacy-policy URL is already usable as a stable fallback.

- [Chrome Web Store checklist](docs/STORE_SUBMISSION.md)
- [Store listing draft](docs/STORE_LISTING.md)
- [Manual regression plan](docs/TEST_PLAN.md)
- [Validation evidence](docs/VALIDATION.md)
- [Release notes template](docs/RELEASE_NOTES_TEMPLATE.md)
- [Pages-ready privacy route](docs/privacy/index.html)

## License

MIT. See [LICENSE](LICENSE).

## Versioning policy

- `0.x` — pre-release hardening and compatibility development
- `1.0.0` — first public release after final acceptance and Chrome Web Store submission checks
- `1.x` — compatibility, safety, and UX updates that preserve the narrow single purpose

Keep previous known-good releases available for rollback rather than rewriting working release history.
