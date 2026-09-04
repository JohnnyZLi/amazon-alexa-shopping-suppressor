# Security Policy

## Supported versions

Security fixes are applied to the current release line. Older versions should be upgraded rather than relied on for ongoing fixes.

## Reporting a vulnerability

If GitHub's private vulnerability reporting flow is available for this repository, use **Report a vulnerability** in the repository Security tab.

If private reporting is unavailable, open a minimal GitHub issue requesting a private contact channel. Do not include exploit details, private Amazon account information, credentials, or other sensitive data in a public issue.

## Security design

The extension intentionally has a narrow capability surface:

- exactly one Chrome API permission: `storage`;
- `chrome.storage.local` is used only for the boolean `enabled` on/off preference;
- no background/service worker;
- no network access;
- no telemetry;
- no remote code or runtime dependencies;
- no `tabs`, `scripting`, `activeTab`, history, downloads, cookies, or webRequest permissions;
- isolated Manifest V3 content-script execution;
- explicit HTTPS-only Amazon retail host scope;
- fail-open candidate validation before broad Rufus/Alexa suppression;
- automatic restoration of inline styles if a managed dynamic element stops matching the safety policy;
- user-triggered disable restores extension-managed element styles and recorded Rufus dock state;
- no operation on recognized checkout and returns routes.

Changes that add network access, additional persisted state, remote code, broader site access, or any Chrome permission beyond `storage` require explicit documentation and security review.
