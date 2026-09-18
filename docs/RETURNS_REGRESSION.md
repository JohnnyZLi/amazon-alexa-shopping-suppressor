# Amazon Returns regression — pre-1.0.0

Two separate signed-in Amazon US regressions shaped the Returns policy before 1.0.0.

The first regression came from treating the entire `/spr/returns/`, `/hz/returns/`, and `/gp/your-account/returns/` route families as sensitive and disabling the suppressor there. Rufus remained present and could leave the Returns workflow shifted by a large blank dock gutter. The policy was changed so **active checkout** remains fail-open/inactive while Returns stays suppressor-active.

A later live test exposed a subtler problem: Amazon had begun reusing Rufus components inside the functional return-reason prompt itself. The extension already excluded `rufus-web-*`, `orc-rufus-*`, Rufus text/submit controls, and known Rufus input/submit slots, but `.s-ask-rufus-mshop-suggestion-container` and `.s-suggestion-nile-desktop-container` were still in unconditional document-start suppression. That allowed functional Returns UI to disappear before JavaScript safety checks could protect it.

Comparison with the publisher's installed Adios Alexa 2.0.0 build showed those two suggestion containers were not targeted there. They are now guarded selectors and are explicitly preserved when they belong to a Returns workflow, along with the known Rufus main-view, conversation, textarea, and pill components. The separate shopping-assistant panel remains suppressible and Rufus dock-gutter repair remains active.

Permanent Chromium regression coverage verifies that:

- the Rufus shopping panel is suppressed on Returns;
- the dock gutter is repaired;
- Rufus-powered return reason, follow-up, suggestion, and textarea components remain visible and usable;
- those same shopping-suggestion surfaces remain suppressible on ordinary non-Returns pages.

The publisher live-tested the affected signed-in return prompt after the fix and confirmed it worked while Alexa/Rufus shopping suppression remained active.

Signed-in screenshots can contain account, order, and location information and are intentionally not committed to the repository.
