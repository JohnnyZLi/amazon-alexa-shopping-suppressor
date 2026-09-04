# v0.3.0 release-candidate test plan

Run these checks against the exact release candidate before promoting it to `1.0.0`. Test with the extension loaded unpacked from a clean checkout or from the extracted CI candidate ZIP.

## Automated preflight

Every push and pull request runs two layers of automated validation:

1. `python scripts/validate.py` — Manifest V3 scope, icons, popup assets, JavaScript syntax, storage-only permission/API policy, sensitive-flow hardening markers, and selector safety invariants.
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
- restoration when navigating into a sensitive flow and resumption when navigating back to a safe flow,
- startup while the saved toggle preference is Off,
- live Off behavior restoring managed elements and recorded dock state,
- live On behavior resuming suppression without a reload,
- popup persistence of the local `enabled` preference.

These tests intentionally accelerate production timers and inject test-only state/path hooks into in-memory copies of the runtime scripts. The runtime source included in the packaged extension is not modified.

Automated tests reduce regression risk but do **not** replace the live Amazon checks below, because only a real Amazon session can validate current production DOM behavior, account/cart/order pages, checkout/returns flows, international variants, Chrome toolbar popup integration, and long-lived-tab behavior.

## Test setup

1. Disable Adios Alexa or any other Alexa/Rufus suppressor.
2. Remove experimental Alexa/Rufus uBlock cosmetic filters. uBlock Origin Lite itself can remain enabled normally.
3. Load this extension from `chrome://extensions`.
4. Confirm the extension version shown by Chrome is `0.3.0`.
5. Pin the extension or open its toolbar menu and confirm a **Suppressor** On/Off switch appears.
6. Confirm the switch initially reads **On** unless you previously saved it Off.
7. Open a fresh Amazon tab after reloading the extension.
8. Keep DevTools Console open for at least one run with `DEBUG: true`; repeat the final normal-browsing smoke test with `DEBUG: false`.

## Pass criteria

A scenario passes only when all applicable conditions hold:

- With the suppressor On, Alexa for Shopping / Rufus does not become meaningfully visible.
- No blank left or right sidebar gutter remains while On.
- Main page content keeps normal width and alignment.
- Normal page controls remain clickable and usable.
- With the suppressor Off, extension-managed Rufus styling/dock state is restored and Amazon is otherwise left alone.
- The saved On/Off preference survives closing/reopening the popup and restarting Chrome.
- No recurring console exceptions come from the extension.
- No obvious high idle CPU usage or rapid layout oscillation occurs.
- Sensitive flows remain untouched.

## On / off toggle matrix

Run these on a normal, non-sensitive Amazon page where Rufus/Alexa would otherwise be present.

- [ ] Open the popup — switch renders and reports **On**.
- [ ] Toggle **Off** — Rufus/Alexa is allowed to return; extension-injected `aas-*` styles are removed.
- [ ] If the page had Rufus dock classes/width/padding that the extension removed, confirm they return when toggled Off.
- [ ] Toggle **On** again — suppression resumes without reloading the page and the blank gutter is repaired.
- [ ] Toggle Off, close the popup, reopen it — switch still reports Off.
- [ ] With Off saved, open a fresh Amazon tab — extension leaves Rufus/Alexa and dock state untouched.
- [ ] Restart Chrome with Off saved — preference remains Off.
- [ ] Toggle On after restart — suppression resumes normally.
- [ ] Toggle state propagates to two already-open Amazon tabs.
- [ ] Toggle Off while on checkout/returns — no visible page modification or breakage occurs.

## Amazon US core matrix

Run the normal-browsing items below with the suppressor On.

- [ ] Homepage — launcher/sidebar absent; layout intact.
- [ ] Search results — Rufus suggestion surfaces absent; results retain full width.
- [ ] Product detail page — Ask/Rufus widgets absent; product content intact.
- [ ] Cart — cart controls and layout intact.
- [ ] Checkout — extension remains inactive; checkout behaves as if suppression were not running.
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

The synthetic suite exercises both restoration and re-suppression mechanisms; this section confirms them against Amazon's live DOM.

- [ ] Open DevTools Elements and identify a guarded Rufus container.
- [ ] Temporarily remove one of the extension-applied inline suppression properties.
- [ ] Confirm the extension reapplies suppression without breaking the page.
- [ ] On a non-sensitive test page, temporarily alter a guarded test element so it no longer has Rufus identity.
- [ ] Confirm previously managed inline styles are restored rather than left stuck on the element.

Do not perform DOM mutation experiments on checkout, returns, or any other transactional flow.

## Sensitive-flow transition checks

- [ ] Navigate from a normal Amazon page into checkout and confirm any extension-managed inline changes are restored and injected styles are removed.
- [ ] Navigate back from checkout to a normal Amazon page and confirm suppression resumes when the saved toggle is On.
- [ ] Repeat the same transition into and out of a recognized returns path.
- [ ] Repeat one transition with the saved toggle Off and confirm suppression does not resume until you explicitly turn it On.

## International smoke tests

At minimum before claiming broad marketplace validation:

- [ ] `amazon.co.uk` — home / search / product + popup Off/On once.
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
- saved toggle state,
- screenshot,
- whether the problem disappears when the extension is disabled or the suppressor is toggled Off,
- relevant `[AlexaSuppressor]` debug messages,
- exact DOM selector or body class/style involved when known.

Do not post order numbers, addresses, payment information, account identifiers, or other personal Amazon data in public issues.
