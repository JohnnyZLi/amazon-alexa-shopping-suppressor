# Chrome Web Store listing draft

Use this copy for the first public release. Keep wording aligned with the shipped code.

## Name

**Alexa Shopping Suppressor for Amazon**

## Short description

Removes Alexa for Shopping/Rufus and its blank sidebar gutter. Open source, on/off control, no tracking.

## Detailed description

Amazon can inject its Alexa for Shopping / Rufus assistant into shopping pages as a docked sidebar, launcher, inline widget, or suggestion surface. On some layouts, simply blocking the visible panel can leave Amazon reserving space for the sidebar, creating a large empty gutter and shifting the page.

Alexa Shopping Suppressor for Amazon handles both parts of that problem:

- suppresses known Alexa for Shopping / Rufus interface surfaces,
- repairs Rufus-specific dock classes, layout variables, and associated page offsets,
- watches for Amazon dynamically reinjecting the UI,
- provides a toolbar On/Off switch and remembers that preference locally,
- restores extension-managed Rufus styles and dock state when turned Off,
- follows the browser/system light or dark color scheme in its popup,
- deliberately avoids recognized checkout and returns flows,
- runs entirely in the browser with no analytics, telemetry, remote code, or network requests.

The extension uses a conservative fail-open design. Broad Rufus-like DOM matches are treated only as candidates and must pass safety checks before being modified. If a dynamically managed element stops looking like Alexa/Rufus UI, the extension restores the inline styles it changed.

The first release supports 23 Amazon retail storefronts. The real unpacked extension has been exercised on live pages across all 23 supported marketplaces; Amazon-side automated-access challenges on a small number of search requests were separately retried with alternate live browse and direct product pages.

### Privacy

The extension does not collect, transmit, sell, or share personal data. Amazon page DOM information is processed locally only to identify and suppress Alexa/Rufus UI and repair related layout state. The only persisted extension state is one local boolean named `enabled`, used to remember whether the user turned the suppressor On or Off. That preference is never transmitted.

### Permissions

The extension requests exactly one Chrome API permission: **Storage**. It is used only to remember the local On/Off preference. The extension does not request tabs, scripting, activeTab, history, downloads, cookies, webRequest, or background permissions.

Its site access is limited to the explicitly listed Amazon retail storefronts in the manifest, where the content script needs to read and modify page DOM to perform suppression and layout repair.

### Open source

Source code, privacy policy, security policy, support information, release history, automated regression tests, validation evidence, and deterministic packaging tools are public in the project repository.

**Unofficial; not affiliated with or endorsed by Amazon. Amazon, Alexa, Rufus, and related names are trademarks of their respective owner.**

## Single-purpose statement

Suppress Amazon's Alexa for Shopping/Rufus interface and repair page layout space reserved for its docked sidebar, with a user-controlled On/Off switch.

## Site-access justification

The extension must read and modify DOM elements on supported Amazon retail pages to identify Alexa/Rufus interface surfaces, hide them, and remove Rufus-specific dock layout state. Processing is local to the browser. The extension does not transmit page contents or account data.

## Storage permission justification

The `storage` permission is used only for one boolean setting, `enabled`, so the toolbar On/Off preference persists across popup closes and Chrome restarts. No Amazon page data, browsing history, account data, or analytics are stored.

## Remote code declaration

**No.** All executable code is packaged with the extension. There are no remote scripts, dynamic imports, remote dependencies, or remotely hosted executable resources.

## Data-use disclosure

**Personal/user data collected:** None.

**Data transmitted:** None.

**Data sold/shared:** None.

**Analytics/telemetry:** None.

**Local extension setting:** one boolean `enabled` preference stored with `chrome.storage.local`.

**Local page processing:** The content script examines DOM element identity, attributes, structure, inline layout state, and limited text presence locally to determine whether Alexa/Rufus has initialized and whether an element is safe to suppress. Page-derived information is not persisted or sent anywhere.

## Category

**Shopping**

## Support URL

https://github.com/JohnnyZLi/amazon-alexa-shopping-suppressor/issues

## Privacy policy URL

https://github.com/JohnnyZLi/amazon-alexa-shopping-suppressor/blob/main/PRIVACY.md

A Pages-ready privacy route also exists in `docs/privacy/` and can replace the repository URL after GitHub Pages is explicitly enabled and verified.

## Homepage / source URL

https://github.com/JohnnyZLi/amazon-alexa-shopping-suppressor

## Store asset filenames

The separate Web Store submission bundle contains:

- `screenshot-1-before-after-1280x800.png`
- `screenshot-2-full-width-1280x800.png`
- `screenshot-3-targeted-ui-1280x800.png`
- final current-popup screenshot at 1280x800 or 640x400
- `promo-440x280.png`
- `marquee-1400x560.png` (optional)

The screenshot sources are real browser captures from the original Amazon failure case. Identifying account/header information was cropped out. The promotional artwork is original and does not use Amazon/Alexa/Rufus logos. Current popup evidence is captured from the real unpacked extension in Chromium in light, dark, and Off states.

## Promotional copy

**Headline:** Remove Alexa. Keep the page.

**Subhead:** Open-source sidebar suppression with an instant Off switch and no tracking.
