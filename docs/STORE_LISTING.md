# Chrome Web Store listing draft

This is the working listing copy for the first public release. Keep wording factual and aligned with the shipped code.

## Name

**Alexa Shopping Suppressor for Amazon**

Alternative if the store name needs to be shorter:

**Amazon Alexa Shopping Suppressor**

## Short description

Removes Alexa for Shopping/Rufus and fixes its blank sidebar gutter. Open source, local-only, no tracking.

## Detailed description

Amazon can inject its Alexa for Shopping / Rufus assistant into shopping pages as a docked sidebar, launcher, inline widget, or suggestion surface. On some layouts, simply blocking the visible panel can leave Amazon reserving space for the sidebar, which creates a large empty gutter and shifts the page.

Alexa Shopping Suppressor for Amazon handles both parts of that problem:

- suppresses known Alexa for Shopping / Rufus interface surfaces,
- repairs Rufus-specific dock classes, layout variables, and associated page offsets,
- watches for Amazon dynamically reinjecting the UI,
- deliberately avoids recognized checkout and returns flows,
- runs entirely in the browser with no analytics, telemetry, remote code, or network requests.

The extension uses a conservative fail-open design. Broad Rufus-like DOM matches are treated only as candidates and must pass safety checks before being modified. If a dynamically managed element stops looking like Alexa/Rufus UI, the extension restores the inline styles it changed.

### Privacy

The extension does not collect, transmit, sell, or share user data. It does not use analytics, extension storage, cookies, browsing-history APIs, or background network requests. Amazon page DOM information is processed locally only to identify and suppress Alexa/Rufus UI and repair related layout state.

### Permissions

The extension requests no privileged Chrome API permissions. Its only site access is the set of explicitly listed Amazon retail storefronts in the manifest, where the content script needs to read and modify the page DOM to perform suppression and layout repair.

### Open source

Source code, privacy policy, security policy, and release history are public in the project repository.

**Unofficial; not affiliated with or endorsed by Amazon. Amazon, Alexa, Rufus, and related names are trademarks of their respective owner.**

## Single-purpose statement

Suppress Amazon's Alexa for Shopping/Rufus interface and repair page layout space reserved for its docked sidebar.

## Site-access justification

The extension must read and modify DOM elements on supported Amazon retail pages to identify Alexa/Rufus interface surfaces, hide them, and remove Rufus-specific dock layout state. Processing is local to the browser. The extension does not transmit page contents or account data.

## Remote code declaration

**No.** All executable code is packaged with the extension. There are no remote scripts, dynamic imports, remote dependencies, or remotely hosted executable resources.

## Data-use disclosure

**Data collected:** None.

**Data transmitted:** None.

**Data sold/shared:** None.

**Analytics/telemetry:** None.

**Local processing:** The content script examines DOM element identity, attributes, structure, inline layout state, and limited text presence locally to determine whether Alexa/Rufus has initialized and whether an element is safe to suppress. This information is not retained after the page/session and is not sent anywhere.

## Support URL

Use the GitHub repository or issue tracker until a dedicated support page exists.

## Privacy policy URL

Use a stable public rendering of `PRIVACY.md` or a GitHub Pages copy of the same policy.

## Screenshot shot list

Use real browser screenshots with private/account information removed. Do not fabricate Amazon UI.

1. **Normal product page** — full-width product page with no Alexa/Rufus sidebar or blank gutter.
2. **Search results** — full-width search page with Rufus suggestion surfaces suppressed.
3. **Before/after explanation graphic** — only if the “before” screenshot contains no personal information and accurately represents stock Amazon behavior.
4. **Open-source/privacy graphic** — optional promotional graphic stating “Open source · Local only · No tracking”; do not imply Amazon endorsement.

Recommended screenshot annotation should be minimal and must not obscure the actual extension behavior.

## Promotional tile copy

**Headline:** Remove Alexa. Keep the page.

**Subhead:** Open-source Amazon sidebar suppression with no tracking.

Do not use Amazon, Alexa, or Rufus logos or reproduce Amazon trade dress in the artwork.
