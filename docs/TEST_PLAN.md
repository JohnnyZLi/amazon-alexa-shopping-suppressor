# v0.2.0 release-candidate test plan

Run these checks against the exact release candidate before promoting it to `1.0.0`. Test with the extension loaded unpacked from a clean checkout or from the extracted CI candidate ZIP.

## Automated preflight

Every push and pull request now runs two layers of automated validation:

1. `python scripts/validate.py` — Manifest V3 scope, icons, JavaScript syntax, forbidden capability checks, sensitive-flow hardening markers, and selector safety invariants.
2. `python scripts/browser_smoke.py` — synthetic regression checks inside a real headless Chromium DOM.

The synthetic Chromium suite covers:

- immediate soft-hide and later hard-hide behavior,
- guarded Rufus candidate suppression,
- Amazon page-shell protection,
- restoration when a managed element loses Rufus/Alexa identity,
- re-suppression after an inline-style rewrite,
- explicit dock-state repair,
- preservation of unrelated large body padding,
- inactivity on known checkout/returns paths,
- restoration when navigating into a sensitive flow and resumption when navigating back to a safe flow.

These tests intentionally accelerate production timers and inject a test-only pathname hook into an in-memory copy of `content.js`. The runtime source included in the packaged extension is not modified.

Automated tests reduce regression risk but do **not** replace the live Amazon checks below, because only a real Amazon session can validate current production DOM behavior, account/cart/order pages, checkout/returns flows, international variants, and long-lived-tab behavior.

## Test setup

1. Disable Adios Alexa or any other Alexa/Rufus suppressor.
2. Remove experimental Alexa/Rufus uBlock cosmetic filters. uBlock Origin Lite itself can remain enabled normally.
3. Load this extension from `chrome://extensions`.
4. Confirm the extension version shown by Chrome is `0.2.0`.
5. Open a fresh Amazon tab after reloading the extension.
6. Keep DevTools Console open for at least one run with `DEBUG: true`; repeat the final normal-browsing smoke test with `DEBUG: false`.

## Pass criteria

A scenario passes only when all applicable conditions hold:

- Alexa for Shopping / Rufus does not become meaningfully visible.
- No blank left or right sidebar gutter remains.
- Main page content keeps normal width and alignment.
- Normal page controls remain clickable and usable.
- No recurring console exceptions come from the extension.
- No obvious high idle CPU usage or rapid layout oscillation occurs.
- Sensitive flows remain untouched.

## Amazon US core matrix

- [ ] Homepage — launcher/sidebar absent; layout intact.
- [ ] Search results — Rufus suggestion surfaces absent; results retain full width.
- [ ] Product detail page — Ask/Rufus widgets absent; product content intact.
- [ ] Cart — cart controls and layout intact.
- [ ] Checkout — extension remains inactive; checkout behaves as if extension were disabled.
- [ ] Your Orders — order controls intact.
- [ ] Returns — extension remains inactive on recognized returns flow; all return controls intact.
- [ ] Account pages — account UI intact.
- [ ] Direct product URL in a fresh tab — no startup gutter or visible Rufus flash.
- [ ] External site -> Amazon — no startup gutter or visible Rufus flash.
- [ ] Amazon -> Amazon navigation — suppression survives navigation.
- [ ] Browser Back / Forward — layout remains repaired.
- [ ] Window resize — no stale dock offset or horizontal jitter.
- [ ] Long-lived tab (30-60 minutes) — Rufus does not reappear; no runaway observer/timer behavior.

## Dynamic mutation checks

These are especially important for v0.2.0 because the code now restores and reapplies managed inline styles. The synthetic suite exercises both mechanisms; this section confirms them against Amazon's live DOM.

- [ ] Open DevTools Elements and identify a guarded Rufus container.
- [ ] Temporarily remove one of the extension-applied inline suppression properties.
- [ ] Confirm the extension reapplies suppression without breaking the page.
- [ ] On a non-sensitive test page, temporarily alter a guarded test element so it no longer has Rufus identity.
- [ ] Confirm previously managed inline styles are restored rather than left stuck on the element.

Do not perform DOM mutation experiments on checkout, returns, or any other transactional flow.

## Sensitive-flow transition checks

- [ ] Navigate from a normal Amazon page into checkout and confirm any extension-managed inline changes are restored and injected styles are removed.
- [ ] Navigate back from checkout to a normal Amazon page and confirm suppression resumes.
- [ ] Repeat the same transition into and out of a recognized returns path.

## International smoke tests

At minimum before claiming broad marketplace validation:

- [ ] `amazon.co.uk` — home / search / product.
- [ ] `amazon.de` — home / search / product.
- [ ] `amazon.co.jp` — home / search / product.
- [ ] `amazon.in` — home / search / product.
- [ ] `amazon.com.au` — home / search / product.

For marketplaces not manually tested, describe them as supported by manifest scope but not validated.

## Exact-candidate evidence

On each CI run, the validation workflow uploads the deterministic ZIP and its SHA-256 file as an `extension-candidate-<commit SHA>` artifact. Use the artifact from the exact commit being considered for `1.0.0` so the manually tested bytes are the same bytes promoted to release.

## Regression evidence

For each failed item, record:

- marketplace and full path (omit private query/order information),
- Chrome version,
- extension version/commit,
- screenshot,
- whether the problem disappears when the extension is disabled,
- relevant `[AlexaSuppressor]` debug messages,
- exact DOM selector or body class/style involved when known.

Do not post order numbers, addresses, payment information, account identifiers, or other personal Amazon data in public issues.
