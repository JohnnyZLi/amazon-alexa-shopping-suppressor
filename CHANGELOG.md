# Changelog

## 0.1.0 — 2026-09-01

Initial known-good baseline.

- Manifest V3 unpacked Chrome extension.
- No requested Chrome permissions.
- Explicit support for 23 Amazon retail storefront domains.
- Runs at `document_start` in the isolated content-script world.
- Soft-hide → initialization window → hard-hide lifecycle.
- Dedicated Rufus dock-state repair.
- Body class/style mutation observer.
- General DOM reinjection observer with debounced rescanning.
- Low-frequency targeted fallback scan.
- Protected Amazon page-shell and main-content structures.
- Explicit exclusions for Rufus-named components that may belong to returns/other legitimate flows.
- No node deletion, storage, network access, telemetry, background worker, popup, or remote code.
- User-confirmed working on the current Amazon US layout that previously exhibited the blank-sidecar failure.
