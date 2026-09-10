# Validation evidence

This document records release evidence separately from the manual test procedure in `TEST_PLAN.md`.

## Runtime architecture

- Manifest V3.
- Exactly one Chrome API permission: `storage`.
- `chrome.storage.local` persists only the boolean `enabled` On/Off preference.
- No service worker/background page, network requests, remote code, analytics, telemetry, cookies, browsing-history access, or privileged tabs/scripting APIs.
- Content-script scope is limited to the exact HTTPS bare/`www` retail hosts for 23 Amazon marketplaces.
- Recognized active checkout and returns paths are intentionally fail-open/inactive.
- Known post-purchase thank-you/order-confirmation paths are explicitly non-sensitive so suppression and gutter repair resume after the transaction is complete.

## Automated regression gates

Normal push/PR CI runs static manifest/source/security validation, the synthetic Chromium regression suite, the adversarial Chromium regression suite, deterministic packaging, SHA-256 generation, and exact candidate artifact upload. The tag-driven release workflow repeats those gates before publishing a GitHub Release.

The synthetic suite covers soft/hard suppression, selector safety, page-shell protection, dynamic identity restoration, inline-style rewrite recovery, dock repair, unrelated-padding preservation, sensitive-route inactivity, post-purchase confirmation activation, safe/sensitive transitions, saved-Off startup, live Off/On behavior, and popup persistence.

The adversarial suite additionally covers rapid toggle storms, two already-open tabs, toggle/sensitive-flow interleaving, repeated Amazon-like inline rewrites across On/Off cycles, and accelerated long-lived mutation/dock churn.

## Real Chromium persistence evidence

The real unpacked extension was exercised in a persistent Chromium profile using real `chrome.storage.local` and `chrome.storage.onChanged` across complete browser-process termination and restart. That testing exposed the v0.3.0 saved-Off startup race, which was fixed in v0.3.1. After the fix, saved Off survived restart, a fresh Amazon-shaped HTTPS page remained untouched while Off, switching On resumed suppression immediately, saved On survived another restart, and two open tabs received real storage-change propagation.

## Live Amazon marketplace evidence

A live Chromium sweep exercised the real unpacked extension across **all 23 supported Amazon retail storefronts**.

The first sweep produced 20/23 complete passes on homepage, search, dynamically discovered product page, and real Off/On propagation. Germany and France returned Amazon challenge/apology responses for the automated `/s` search request, while Poland's `/s` response was treated as a download by Chromium. Fresh-runner retries exercised Germany, France, and Poland with alternate live browse pages plus known live direct product pages; all three passed extension activation, visible page-shell checks, and Off/On propagation.

**Result: no supported marketplace produced an extension-side failure.** All 23 storefronts remain in the 1.0.0 scope.

## Deep Amazon US evidence

A dedicated live-Amazon Chromium acceptance suite covers homepage, search, product, cart, direct product startup, external→Amazon navigation, Amazon history Back/Forward, resize, two-tab toggle propagation, a fresh page while saved Off, public account/orders routes, recognized checkout/returns route inactivity, dynamic mutation checks when Rufus is exposed by the runner, popup light/dark behavior, and a live-tab stability interval.

An earlier run completed an actual **30-minute live Amazon tab** and passed every functional runtime item; its only reported failure was an outdated popup-theme probe that targeted retired popup markup.

The same acceptance suite was then rerun against the final 1.0.0 release tree. After correcting only the test-harness selector from retired `.toggle-row` markup to current `.control-card`, the final-tree run passed **every check**: popup light/dark, homepage, search, product, cart, direct product, external→Amazon, Back/Forward, resize, two-tab toggle, saved-Off fresh tab, dynamic mutation handling, public account/orders routes, checkout/returns inactivity, and live-tab stability. The final-tree rerun used a shorter live-tab interval because 30-minute stability had already been established and the release-tree runtime delta was separately covered by CI and confirmation-route tests.

## Post-purchase confirmation regression evidence

Signed-in testing exposed a real regression on Amazon's order-confirmation page: the old blanket `/gp/buy/` fail-open rule treated the completed-order thank-you page as active checkout, leaving Rufus and its stale dock gutter untouched.

The fix keeps active checkout fail-open but explicitly treats known thank-you/order-confirmation routes as non-sensitive. Permanent Chromium regression tests now cover direct confirmation-page activation and checkout→confirmation same-document transitions.

The exact packaged 1.0.0 candidate was also exercised in a real Chromium process against the actual Amazon confirmation pathname with a controlled DOM reproducing the observed stuck-dock state. The extension suppressed Rufus, repaired the gutter on load and reload, recovered from Amazon-like dock reassertion, restored Amazon state when switched Off, repaired the reported stuck state when switched back On, and correctly transitioned between active checkout and post-purchase confirmation.

A literal live signed-in confirmation-page retest can wait until the publisher's next natural purchase rather than requiring another order solely for testing.

## Popup evidence

The redesigned toolbar popup is tested in real Chromium in both light and dark color schemes. The On state reports `Rufus hidden · sidebar space reclaimed`; the Off state reports `Amazon left untouched`. Dark mode follows `prefers-color-scheme` without adding another stored preference or permission.

## Chrome Web Store image compliance

The 128x128 manifest/store icon generator centers the artwork in a 96x96 region with 16 transparent pixels on each side. Store screenshots are 1280x800, the small promotional tile is 440x280, and the optional marquee image is 1400x560.

## Remaining acceptance limits

Public or controlled browser testing cannot substitute for the publisher's authenticated Amazon account session. Before Web Store submission, the publisher should still smoke-test actual Orders, Account, Checkout, and Returns controls and one normal↔sensitive transition. The live signed-in order-confirmation retest can wait until the next natural purchase.

Chrome Web Store developer registration, publisher 2-Step Verification, dashboard disclosures, package/asset upload, and final submission also require the publisher's authenticated Google session.
