# Amazon Returns regression — pre-1.0.0

During signed-in Amazon US acceptance, the publisher reproduced the same Rufus dock-gutter failure inside the Returns Center: Alexa for Shopping remained present and the return workflow was shifted by a large blank left gutter.

Root cause: the pre-release safety policy treated the entire `/spr/returns/`, `/hz/returns/`, and `/gp/your-account/returns/` route families as sensitive and deliberately disabled the suppressor there. That policy prevented the extension from repairing Rufus even though the return controls themselves are unrelated to Rufus.

The 1.0.0 release line now keeps **active checkout** fail-open/inactive, but allows normal Rufus suppression and dock repair on return-workflow routes. Existing selector/page-shell protections still prevent non-Rufus return controls from being managed.

Permanent Chromium regression coverage verifies all three return-route families with a Rufus panel plus dock gutter present: the Rufus candidate is suppressed, the gutter is repaired, and representative return content/control elements remain visible and usable. The full static, synthetic, adversarial, and deterministic-package gates passed before the fix was committed.

The signed-in screenshot that exposed this regression contains account/location/order information and is intentionally not committed to the repository.
