# Amazon Alexa for Shopping Suppressor

**Version:** 0.2.0  
**Status:** public-release candidate / hardening  
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

The extension does **not** remove Amazon DOM nodes. It suppresses UI with styling and repairs layout state so Amazon's own scripts can continue to find elements they expect.

## Security / privacy model

v0.2.0 intentionally has a small attack surface:

- Manifest V3
- **No privileged Chrome API permissions** (`permissions`, `optional_permissions`, and `host_permissions` are absent)
- Content-script site access limited to explicitly listed Amazon retail hosts over HTTPS
- No background/service worker
- No popup
- No extension storage
- No network requests
- No remote code or runtime dependencies
- No analytics or telemetry
- No cookies/history/downloads/webRequest access
- No privileged Chrome APIs
- One static content script running at `document_start` in the isolated world
- No wildcard access to arbitrary Amazon subdomains
- Broad selectors require fail-open JavaScript validation
- Inline changes made by guarded suppression are tracked and reversible
- Generic numeric dock padding is changed only with explicit Rufus dock evidence
- Recognized checkout and returns routes are intentionally inactive

See [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md), and [SUPPORT.md](SUPPORT.md).

## Supported Amazon storefronts

v0.2.0 is scoped to 23 retail domains: United States, Canada, Mexico, Brazil, United Kingdom, Germany, France, Italy, Spain, Netherlands, Belgium, Sweden, Poland, Ireland, Turkey, United Arab Emirates, Saudi Arabia, Egypt, South Africa, Japan, India, Singapore, and Australia.

Each marketplace is limited to its bare retail hostname and `www` hostname over HTTPS. International domains are supported by scope, but are **not yet claimed to be functionally validated on every marketplace**.

## Sensitive-flow safeguard

The extension intentionally remains inactive when the Amazon path matches a recognized checkout or returns route, including the common `/gp/buy/`, `/checkout/`, `/hz/checkout/`, `/spr/returns/`, `/hz/returns/`, and `/gp/your-account/returns/` families.

If a browser navigation signal reaches one of these paths in the same document, the extension deactivates, disconnects observers/timers, removes its injected styles, and restores tracked inline styles on managed elements.

The safeguard favors false negatives over modifying transaction-sensitive pages.

## Install locally in Chrome

1. Clone or download the repository.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select the repository folder containing `manifest.json`.
6. Disable/remove any other Alexa/Rufus suppressor so two extensions are not fighting each other.
7. Remove experimental Alexa/Rufus custom rules previously added to uBlock Origin Lite. uBO Lite itself can remain enabled normally.
8. Close existing Amazon tabs and open a fresh Amazon tab for testing.

## Validation and deterministic packaging

No runtime package manager or build system is required.

```bash
python scripts/validate.py
python scripts/package.py
```

`validate.py` checks the Manifest V3 capability surface, exact HTTPS Amazon host scope, JavaScript syntax, forbidden network/storage/extension API patterns, sensitive-flow safeguards, and selector-hardening invariants.

`package.py` produces a deterministic Chrome extension ZIP in `dist/` and a matching SHA-256 file. Only runtime files referenced by the manifest are included.

GitHub Actions runs the same validation on pushes and pull requests. Pushing a matching `vX.Y.Z` tag validates the code again, creates the deterministic ZIP, verifies the tag matches the manifest version, and publishes the ZIP + checksum as a GitHub Release.

## Debugging

Set `DEBUG: true` near the top of `content.js`, reload the extension, then open Amazon DevTools → **Console**. Messages are prefixed with `[AlexaSuppressor]`.

## Test matrix

Legend: ✅ confirmed · ⬜ not yet tested · ⚠️ regression · ➖ intentionally inactive

v0.1.0 was user-confirmed on the original Amazon US failure case. v0.2.0 changes candidate restoration, selector guarding, dock evidence, fallback timing, and sensitive-flow behavior, so this release candidate should be revalidated before 1.0.0.

| Scenario | v0.2.0 | Expected behavior |
|---|---:|---|
| Current Amazon US layout / normal browsing | ⬜ | Alexa/Rufus suppressed; normal page width; no blank sidebar gutter |
| Homepage | ⬜ | No Alexa launcher/sidebar; page layout intact |
| Search results | ⬜ | No Alexa/Rufus suggestion surfaces; results retain full usable width |
| Product detail page | ⬜ | Ask/Rufus widgets suppressed; product content intact |
| Cart | ⬜ | Cart functionality and layout intact |
| Checkout | ➖ | Extension inactive; checkout untouched |
| Your Orders | ⬜ | Orders UI intact |
| Returns workflow | ➖ | Extension inactive on recognized return routes |
| Account pages | ⬜ | Account UI intact |
| Direct product URL / fresh tab | ⬜ | No startup gutter or visible Alexa flash |
| External site → Amazon | ⬜ | No startup gutter or visible Alexa flash |
| Amazon → Amazon navigation | ⬜ | Rufus remains suppressed after navigation |
| Browser Back / Forward | ⬜ | Layout repaired correctly; sensitive routes deactivate |
| Window resize | ⬜ | No stale dock offset |
| Long-lived Amazon tab | ⬜ | Rufus does not reappear; no runaway CPU/observer activity |
| Dynamic Rufus element changes identity | ⬜ | Extension restores its prior inline changes |
| Amazon rewrites managed element style | ⬜ | Managed style is re-applied while element remains a safe candidate |

International smoke tests should include at least `amazon.co.uk`, `amazon.de`, `amazon.co.jp`, `amazon.in`, and `amazon.com.au` before 1.0.0.

The detailed manual procedure is in [docs/TEST_PLAN.md](docs/TEST_PLAN.md). The open regression tracker is GitHub issue #2.

## Acceptance criteria for 1.0.0

- Alexa for Shopping / Rufus never becomes meaningfully visible on supported non-sensitive pages.
- No left/right blank gutter remains after Rufus suppression.
- Main Amazon page content retains its normal width and position.
- Late-injected Rufus components remain suppressed.
- Dynamic candidates that stop being Rufus/Alexa are restored.
- Product/search/cart/account layouts remain usable.
- Checkout and recognized returns flows remain untouched.
- No page-shell or primary content container is hidden.
- No persistent state is written.
- No network access or remote dependency is introduced.
- No new Chrome permission is added without a documented reason.
- No recurring console exceptions or obvious idle CPU loop is introduced.
- The exact release ZIP passes the regression matrix.

## Chrome Web Store preparation

The runtime engine and release infrastructure are now in release-candidate shape. Remaining work is primarily browser regression testing, original visual assets/icons, final marketplace scope decisions, and Web Store listing/policy setup.

- [Chrome Web Store checklist](docs/STORE_SUBMISSION.md)
- [Store listing draft](docs/STORE_LISTING.md)
- [Manual regression plan](docs/TEST_PLAN.md)
- [Release notes template](docs/RELEASE_NOTES_TEMPLATE.md)
- [Static privacy-policy page](docs/PRIVACY_POLICY.html)

## License

MIT. See [LICENSE](LICENSE).

## Versioning policy

- `0.2.x` — public-release candidate hardening and compatibility fixes
- `1.0.0` — after required regression testing and Web Store packaging/branding are complete

Keep the previous known-good commit/release available for rollback rather than rewriting working release history.
