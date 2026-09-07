# 1.0.0 release test plan

Use this plan to distinguish what is already covered automatically from what still requires a real signed-in Amazon/Chrome session before the first public release.

## Automated release gates

Every push and pull request runs:

1. `python scripts/validate.py` — Manifest V3 scope, exact Amazon hosts, storage-only permission/API policy, popup assets, JavaScript syntax, selector/sensitive-flow invariants, exact icon dimensions, and required 128px store-icon padding.
2. `python scripts/browser_smoke.py` — synthetic Chromium regression suite.
3. `python scripts/adversarial_smoke.py` — adversarial Chromium state/mutation suite.
4. `python scripts/package.py` — deterministic extension ZIP + SHA-256.

The tag-driven release workflow repeats these gates and verifies that the `vX.Y.Z` tag exactly matches the manifest version before creating a GitHub Release.

### Synthetic coverage

The production content/popup scripts are exercised in Chromium fixtures for:

- immediate soft-hide and later hard-hide,
- guarded Rufus candidate suppression,
- Amazon page-shell protection,
- restoration when a managed element loses Rufus/Alexa identity,
- re-suppression after Amazon-like inline-style rewrites,
- explicit Rufus dock-state repair,
- preservation of unrelated large body padding,
- inactivity on known checkout/returns paths,
- restoration entering sensitive flows and resumption returning safe,
- saved-Off startup,
- Off restoration and On resumption without reload,
- popup preference persistence.

### Adversarial coverage

The permanent adversarial suite additionally covers:

- more than 120 rapid On/Off state changes,
- propagation to two already-open Amazon-shaped tabs,
- repeated toggling while checkout/returns are active,
- style-rewrite fights across multiple On/Off cycles,
- restoration to a new baseline established while Off,
- accelerated long-lived mutation/fallback churn with repeated Rufus panel replacement and dock-state reassertion.

## Real Chromium persistence evidence

The actual unpacked extension has also been exercised in a persistent Chromium profile with real `chrome.storage.local` and `chrome.storage.onChanged` across complete browser-process termination and restart.

That testing found the v0.3.0 saved-Off startup race and verified the v0.3.1+ fix. Saved Off and saved On both survive process restarts, and real storage change propagation works across open tabs.

## Live marketplace evidence

The real unpacked extension has been exercised on live pages across all 23 supported Amazon storefronts.

- 20 storefronts passed homepage + search + dynamically discovered product page + Off/On propagation in the first sweep.
- Germany and France returned Amazon challenge/apology responses to the CI runner's exact `/s` request; Poland's `/s` response was handled as a download by Chromium.
- A fresh-runner retry exercised those three storefronts with alternate live browse pages plus known direct product pages; all three passed extension activation, visible page-shell checks, and Off/On propagation.
- No marketplace produced an extension-side failure.

All 23 marketplaces therefore remain in the intended 1.0.0 scope. Do not describe the exact automated `/s` request on DE/FR/PL as having rendered successfully; the alternate live-page retry is the evidence for those three.

## Deep Amazon US pre-release acceptance

Before the final tag, run the dedicated live acceptance job against the current release line. It covers, where Amazon permits anonymous CI access:

- homepage,
- search,
- product page,
- cart,
- direct product URL in a fresh tab,
- external site → Amazon,
- Amazon → Amazon navigation,
- browser Back / Forward,
- multiple viewport sizes,
- two open live Amazon tabs with Off/On propagation,
- a fresh live Amazon tab while Off is saved,
- public/unauthenticated account and order routes,
- direct sensitive checkout/returns routes where the route remains reachable,
- live Rufus style rewrite / identity restoration when Amazon exposes a matching candidate,
- an actual 30-minute live Amazon tab with one health checkpoint per minute.

Amazon bot/challenge responses must be recorded as runner limitations, not extension passes or failures. Any real extension assertion failure is a release blocker.

## Final publisher setup

For the final candidate:

1. Disable Adios Alexa or any other Alexa/Rufus suppressor.
2. Remove experimental Alexa/Rufus uBlock cosmetic filters. uBlock Origin Lite itself can remain enabled normally.
3. Extract the **exact CI candidate ZIP** from the intended release commit.
4. Open `chrome://extensions`, enable Developer mode, and Load unpacked from that extracted candidate.
5. Confirm Chrome shows version `1.0.0`.
6. Confirm the toolbar popup renders, follows the current light/dark theme, and defaults to **On** on a brand-new extension profile.
7. Keep private Amazon/order/payment information out of any public screenshots or issue comments.

## Signed-in Amazon acceptance

These checks cannot be truthfully replaced by an anonymous CI runner and remain the publisher's final manual gate.

### Normal/account flows

- [ ] Homepage — signed-in header and page controls intact.
- [ ] Search results — results full width; Rufus suppressed while On.
- [ ] Product detail — product controls intact; Rufus suppressed while On.
- [ ] Cart — cart controls and layout intact.
- [ ] Your Orders — order controls intact.
- [ ] Account pages — account controls intact.

### Sensitive flows

- [ ] Enter actual checkout from a real cart and confirm suppression is inactive and checkout behaves normally.
- [ ] Return from checkout to a normal Amazon page and confirm suppression resumes if saved On.
- [ ] Enter an actual returns flow and confirm suppression is inactive and return controls behave normally.
- [ ] Return from returns to a normal Amazon page and confirm suppression resumes if saved On.
- [ ] Repeat one normal→sensitive→normal transition with saved Off and confirm suppression stays Off.

Do not perform artificial DOM mutation experiments on checkout, returns, or any transaction-sensitive page.

### Toggle sanity on the exact final candidate

- [ ] On a normal page where Rufus is available, toggle Off: Rufus/sidecar and recorded dock state return immediately.
- [ ] Toggle On: Rufus is suppressed and the gutter is reclaimed again without reload.
- [ ] With Off saved, open one new live Amazon tab: extension leaves it untouched.
- [ ] Open two normal Amazon tabs and toggle once: both converge to the selected state.

These behaviors have already passed prior user/live/real-Chromium testing; this short pass confirms the exact final 1.0.0 candidate bytes.

## Pass criteria

The final release passes only when all applicable conditions hold:

- Rufus does not become meaningfully visible on supported non-sensitive pages while On.
- No Rufus-created blank left/right gutter remains while On.
- Main Amazon content keeps normal width and alignment.
- Normal page controls remain usable.
- Off restores extension-managed Rufus styles and recorded dock state.
- The saved preference survives popup/browser restart.
- Sensitive checkout/returns flows are left untouched.
- No page-shell/primary content container is hidden.
- No recurring extension console exception or obvious high-idle-CPU loop is present.
- Static, synthetic, adversarial, and deterministic-package CI gates are green.
- The exact release ZIP corresponds to the exact tagged commit.

## Store evidence

Before submission, confirm the separate Web Store asset bundle contains:

- 128x128 install icon with 96x96 artwork / 16px transparent padding,
- at least one 1280x800 or 640x400 screenshot,
- current popup screenshot experience,
- required 440x280 promotional image,
- optional 1400x560 marquee if used,
- no account name, delivery address, order/payment information, cookies, tokens, or other private data.

## Regression evidence

For any failure, record only non-sensitive information:

- marketplace and safe path,
- Chrome version,
- extension version/commit,
- saved toggle state,
- sanitized screenshot,
- whether disabling the extension or toggling Off changes the problem,
- relevant `[AlexaSuppressor]` debug messages,
- exact selector/body class/style involved when known.

Never post order numbers, addresses, payment information, account identifiers, cookies, tokens, or other private Amazon data in a public issue.
