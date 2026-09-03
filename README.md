# Amazon Alexa for Shopping Suppressor

**Version:** 0.1.1  
**Status:** current / security-hardened  
**Platform:** Chrome / Chromium, Manifest V3  
**Purpose:** suppress Amazon's Alexa for Shopping / Rufus UI without leaving the large blank docked-sidebar gutter.

This repository tracks the current hardened release. The original **v0.1.0 known-good baseline** remains available in Git history for regression comparison.

## Why this exists

Static cosmetic blocking can remove the visible Alexa/Rufus panel before Amazon finishes initializing its own layout state. On affected Amazon layouts, that can leave the page shifted to the right with a large empty gutter where the sidebar would have been.

This extension takes a different approach:

1. **Soft-hide immediately at `document_start`.** Known Alexa/Rufus surfaces are made invisible and non-interactive without immediately collapsing their dimensions.
2. **Let Amazon initialize.** The extension gives the page a conservative initialization window so Amazon can finish constructing/measuring Rufus.
3. **Hard-hide after initialization.** Once initialization is safely underway, the extension collapses the Alexa/Rufus UI.
4. **Repair dock state.** It removes Rufus docking classes, Rufus-specific width variables, and suspicious Rufus-linked body padding that can create the blank gutter.
5. **Keep repairing dynamically.** Mutation observers catch Amazon re-injecting Rufus UI or restoring dock state, with a low-frequency fallback scan as a safety net.
6. **Fail open.** Broad `rufus` matches are treated only as candidates and must pass safety checks before being hidden. Structural Amazon page containers are explicitly protected.

The extension does **not** remove Amazon DOM nodes. It suppresses UI with styling and repairs layout state so Amazon's own scripts can continue to find elements they expect.

## Security / privacy model

v0.1.1 intentionally has a very small attack surface:

- Manifest V3
- **No privileged Chrome API permissions** (`permissions` and `optional_permissions` are absent)
- Content-script site access is limited to explicitly listed Amazon retail hosts over HTTPS
- No background/service worker
- No popup
- No extension storage
- No network requests
- No remote code or dependencies
- No analytics or telemetry
- No cookies/history/downloads/webRequest access
- No privileged Chrome APIs
- One static content script running at `document_start`
- No wildcard access to arbitrary Amazon subdomains

Everything the extension does is visible in `content.js` and `manifest.json`.

## Supported Amazon storefronts

v0.1.1 explicitly includes 23 retail domains:

- United States — `amazon.com`
- Canada — `amazon.ca`
- Mexico — `amazon.com.mx`
- Brazil — `amazon.com.br`
- United Kingdom — `amazon.co.uk`
- Germany — `amazon.de`
- France — `amazon.fr`
- Italy — `amazon.it`
- Spain — `amazon.es`
- Netherlands — `amazon.nl`
- Belgium — `amazon.com.be`
- Sweden — `amazon.se`
- Poland — `amazon.pl`
- Ireland — `amazon.ie`
- Turkey — `amazon.com.tr`
- United Arab Emirates — `amazon.ae`
- Saudi Arabia — `amazon.sa`
- Egypt — `amazon.eg`
- South Africa — `amazon.co.za`
- Japan — `amazon.co.jp`
- India — `amazon.in`
- Singapore — `amazon.sg`
- Australia — `amazon.com.au`

Each marketplace is limited to its bare retail hostname and `www` hostname over HTTPS; arbitrary subdomains and HTTP are excluded. International domains are supported by scope, but **v0.1.1 is not claimed to be functionally validated on every marketplace**. See the test matrix below.

## Install in Chrome

1. Keep this folder somewhere permanent. Chrome needs the folder to remain available after loading it unpacked.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select this exact folder — the one containing `manifest.json`.
6. Disable/remove Adios Alexa if it is still installed, so two suppressors are not fighting each other.
7. Remove experimental Alexa/Rufus custom rules previously added to uBlock Origin Lite. uBO Lite itself can remain enabled normally.
8. Close existing Amazon tabs and open a fresh Amazon tab for the first test.

## Updating after code changes

If you edit `content.js` or `manifest.json`:

1. Open `chrome://extensions`.
2. Find **Amazon Alexa for Shopping Suppressor**.
3. Click **Reload**.
4. Reload/open a fresh Amazon tab.

Do not edit a known-good release in place when experimenting. Use a new branch/version and keep the previous commit available for rollback.

## Debugging

At the top of `content.js`:

```js
DEBUG: false,
```

Change it to:

```js
DEBUG: true,
```

Then reload the extension from `chrome://extensions` and open Amazon DevTools → **Console**.

Messages are prefixed with:

```text
[AlexaSuppressor]
```

Useful debug events include initialization timing, hidden candidates, rejected unsafe candidates, removed dock classes, and body-layout repairs.

## Test matrix

Legend:

- ✅ = confirmed
- ⬜ = not yet tested
- ⚠️ = regression / needs investigation

The same core behavior was user-confirmed on v0.1.0; v0.1.1 should be revalidated after the selector-hardening change before marking rows confirmed.

### Core Amazon US regression matrix

| Scenario | v0.1.1 | Expected behavior |
|---|---:|---|
| Current Amazon US layout / normal browsing | ⬜ | Alexa/Rufus suppressed; normal page width; no blank sidebar gutter |
| Homepage | ⬜ | No Alexa launcher/sidebar; page layout intact |
| Search results | ⬜ | No Alexa/Rufus suggestion surfaces; results retain full usable width |
| Product detail page | ⬜ | Ask/Rufus widgets suppressed; product content intact |
| Cart | ⬜ | Cart functionality and layout intact |
| Checkout | ⬜ | **No interference whatsoever** |
| Your Orders | ⬜ | Orders UI intact |
| Returns workflow | ⬜ | Return controls intact, especially Rufus-named return components |
| Account pages | ⬜ | Account UI intact |
| Direct product URL / fresh tab | ⬜ | No startup gutter or visible Alexa flash |
| External site → Amazon | ⬜ | No startup gutter or visible Alexa flash |
| Amazon → Amazon navigation | ⬜ | Rufus remains suppressed after navigation |
| Browser Back / Forward | ⬜ | Layout repaired correctly |
| Window resize | ⬜ | No stale dock offset |
| Long-lived Amazon tab | ⬜ | Rufus does not reappear; no runaway CPU/observer activity |

### International smoke-test matrix

| Storefront | v0.1.1 | Suggested pages |
|---|---:|---|
| `amazon.co.uk` | ⬜ | home / search / product |
| `amazon.de` | ⬜ | home / search / product |
| `amazon.co.jp` | ⬜ | home / search / product |
| `amazon.in` | ⬜ | home / search / product |
| `amazon.com.au` | ⬜ | home / search / product |
| Remaining supported storefronts | ⬜ | smoke test as encountered |

## Acceptance criteria for future versions

A revision should not replace this baseline unless all applicable checks pass:

- Alexa for Shopping / Rufus never becomes meaningfully visible.
- No left/right blank gutter remains after Rufus suppression.
- Main Amazon page content retains its normal width and position.
- Late-injected Rufus components remain suppressed.
- Product/search/cart/account layouts remain usable.
- Checkout remains untouched.
- Returns remain untouched.
- No page-shell or primary content container is hidden.
- No persistent state is written.
- No network access or remote dependency is introduced.
- No new Chrome permission is added without a documented reason.
- No recurring console exceptions or obvious idle CPU loop is introduced.

## Architecture notes

The implementation deliberately separates three concerns:

### 1. Known UI suppression

Only exact, Rufus/Alexa-specific selectors are hidden directly by CSS. Substring selectors and generic attribute matches are guarded: they are used only to discover candidates and must pass `isSafeRufusCandidate()` before inline suppression is applied.

### 2. Dock-state repair

A dedicated observer watches `<body>` class/style mutations and removes Amazon's Rufus docking state when it reappears. This specifically targets the failure mode where the visible sidebar is gone but Amazon still reserves its width.

### 3. Dynamic reinjection handling

A document observer watches for newly inserted nodes and relevant class/id changes. Work is debounced rather than rescanning for every individual mutation. A slower periodic targeted scan is retained as a fallback.

This is intentionally more stateful than a static ad-block cosmetic rule because the Amazon failure is itself stateful and timing-dependent.

## Rollback

To return to stock Amazon behavior:

1. Open `chrome://extensions`.
2. Disable or remove this extension.
3. Reload Amazon.

There is no stored extension state to clean up and no Amazon DOM nodes are permanently altered.

## Versioning policy

Use semantic-ish patch versions for maintenance:

- `0.1.x` — selector/compatibility fixes with the same architecture
- `0.2.0` — material behavior or architecture change
- `1.0.0` — after broader regression and international validation

Always keep the last known-good commit/release available instead of editing history in place.
