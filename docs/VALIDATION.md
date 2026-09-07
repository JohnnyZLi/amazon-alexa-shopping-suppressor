# Validation evidence

This document records release evidence separately from the manual test procedure in `TEST_PLAN.md`.

## Runtime architecture

- Manifest V3.
- Exactly one Chrome API permission: `storage`.
- `chrome.storage.local` persists only the boolean `enabled` On/Off preference.
- No service worker/background page, network requests, remote code, analytics, telemetry, cookies, browsing-history access, or privileged tabs/scripting APIs.
- Content-script scope is limited to the exact HTTPS bare/`www` retail hosts for 23 Amazon marketplaces.
- Recognized checkout and returns paths are intentionally fail-open/inactive.

## Automated regression gates

Normal push/PR CI runs:

1. static manifest/source/security validation,
2. the synthetic Chromium regression suite,
3. the adversarial Chromium regression suite,
4. deterministic packaging and SHA-256 generation.

The tag-driven release workflow repeats the same gates before publishing a GitHub Release.

The synthetic suite covers soft/hard suppression, selector safety, page-shell protection, dynamic identity restoration, inline-style rewrite recovery, dock repair, unrelated-padding preservation, sensitive-route inactivity, safe/sensitive transitions, saved-Off startup, live Off/On behavior, and popup persistence.

The adversarial suite additionally covers rapid toggle storms, two already-open tabs, toggle/sensitive-flow interleaving, repeated Amazon-like inline rewrites across On/Off cycles, and accelerated long-lived mutation/dock churn.

## Real Chromium persistence evidence

The real unpacked extension was exercised in a persistent Chromium profile using real `chrome.storage.local` and `chrome.storage.onChanged` across complete browser-process termination and restart.

That testing exposed the v0.3.0 saved-Off startup race, which was fixed in v0.3.1. After the fix:

- saved Off survived a full process restart,
- a fresh Amazon-shaped HTTPS page remained untouched while Off,
- switching On resumed suppression immediately,
- saved On survived another full process restart,
- two open tabs received real storage change propagation.

## Live Amazon marketplace evidence

A live Chromium sweep exercised the real unpacked extension across **all 23 supported Amazon retail storefronts**.

The first sweep produced 20/23 complete passes on homepage, search, dynamically discovered product page, and real Off/On propagation. Germany and France returned Amazon challenge/apology responses for the automated `/s` search request, while Poland's `/s` response was treated as a download by Chromium. Those were Amazon/runner access behaviors rather than extension failures.

A fresh-runner retry then exercised Germany, France, and Poland with alternate live browse pages plus known live direct product pages. All three passed extension activation, visible page-shell checks, and Off/On propagation.

**Result: no supported marketplace produced an extension-side failure.** All 23 storefronts remain in the intended 1.0.0 scope.

Raw CI report artifacts are retained with the corresponding GitHub Actions runs and summarized in GitHub issue #2.

## Popup evidence

The redesigned v0.3.2 toolbar popup is tested in real Chromium in both light and dark color schemes. The On state reports `Rufus hidden · sidebar space reclaimed`; the Off state reports `Amazon left untouched`. Dark mode follows `prefers-color-scheme` without adding another stored preference or permission.

## Chrome Web Store image compliance

The 128x128 manifest/store icon generator now follows Chrome Web Store square-icon sizing guidance by centering the artwork in a 96x96 region with 16 transparent pixels on each side. The 16/32/48 runtime icons retain their existing visual sizing.

Store screenshots are 1280x800, the small promotional tile is 440x280, and the optional marquee image is 1400x560.

## Remaining acceptance limits

Public unauthenticated live testing cannot substitute for the publisher's authenticated Amazon account session. Before final submission, signed-in validation should still cover actual Orders, Account, Checkout, and Returns controls and confirm no interaction problem appears in those account-bound flows.

Chrome Web Store developer registration, publisher 2-Step Verification, dashboard disclosures, package/asset upload, and final submission also require the publisher's authenticated Google session.
