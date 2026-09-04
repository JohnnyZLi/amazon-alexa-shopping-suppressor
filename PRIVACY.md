# Privacy Policy

Amazon Alexa for Shopping Suppressor does not collect, transmit, sell, or share personal data.

The extension runs locally in the browser on explicitly supported Amazon retail storefronts. It reads limited page DOM information only to identify Alexa for Shopping / Rufus interface elements, determine when that interface has initialized, hide those elements, and repair Rufus-specific dock layout state.

The extension stores exactly one local preference through `chrome.storage.local`: a boolean named `enabled` that remembers whether the user has turned the suppressor On or Off. This preference is extension configuration, not Amazon page data, and is not transmitted anywhere.

The extension:

- makes no network requests;
- contains no analytics or telemetry;
- stores only the local `enabled` boolean used by the toolbar toggle;
- does not use `localStorage`, `sessionStorage`, page cookies, or IndexedDB;
- does not access browsing history, downloads, tabs, account credentials, payment information, or Amazon purchase data through privileged browser APIs;
- does not send page contents, DOM data, or the toggle preference anywhere;
- does not load remote code or remote dependencies.

The extension is intentionally inactive on recognized Amazon checkout and returns routes.

No personal data is collected or retained. The local `enabled` preference remains in Chrome's extension storage until the user changes it, clears the extension's data, or removes the extension.

This project is unofficial and is not affiliated with, endorsed by, or sponsored by Amazon.
