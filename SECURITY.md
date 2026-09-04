# Security Policy

## Supported versions

Security fixes are applied to the current release line. Older versions should be upgraded rather than relied on for ongoing fixes.

## Reporting a vulnerability

If GitHub's private vulnerability reporting flow is available for this repository, use **Report a vulnerability** in the repository Security tab.

If private reporting is unavailable, open a minimal GitHub issue requesting a private contact channel. Do not include exploit details, private Amazon account information, credentials, or other sensitive data in a public issue.

## Security design

The extension intentionally has a narrow capability surface:

- no privileged Chrome API permissions;
- no background/service worker;
- no network access;
- no storage or telemetry;
- no remote code or runtime dependencies;
- isolated Manifest V3 content-script execution;
- explicit HTTPS-only Amazon retail host scope;
- fail-open candidate validation before broad Rufus/Alexa suppression;
- automatic restoration of inline styles if a managed dynamic element stops matching the safety policy;
- no operation on recognized checkout and returns routes.

Changes that add network access, storage, remote code, broader site access, or privileged Chrome permissions require explicit documentation and security review.
