# Release / Web Store assets

## Extension icons

Runtime icons are in `icons/` and are included in the extension package through `manifest.json`:

- `icon-16.png`
- `icon-32.png`
- `icon-48.png`
- `icon-128.png`

They are generated deterministically by `scripts/generate_icons.py` using only the Python standard library. The icon is original artwork: a generic chat bubble with a suppression slash. It intentionally does not use Amazon, Alexa, or Rufus logos.

For the 128x128 install/Web Store icon, the generator centers square artwork in a 96x96 region with 16 transparent pixels on each side to follow Chrome Web Store square-icon sizing guidance. Smaller runtime icons retain their existing sizing for legibility.

## Chrome Web Store artwork

The Chrome Web Store listing graphics are kept in a separate submission bundle rather than the runtime extension ZIP:

- `promo-440x280.png`
- `marquee-1400x560.png`
- `screenshot-1-before-after-1280x800.png`
- `screenshot-2-full-width-1280x800.png`
- `screenshot-3-targeted-ui-1280x800.png`
- `screenshot-4-popup-control-1280x800.png`

The first three screenshots were built from real browser captures of the original Amazon sidebar failure. Account name, delivery location, and other identifying header information were removed by cropping. The promotional artwork does not use Amazon/Alexa/Rufus logos.

`screenshot-4-popup-control-1280x800.png` uses a current real-Chromium capture of the shipped popup UI over the already-sanitized Amazon search-result evidence. It shows the current Suppressor On state and contains no Amazon account header, address, order, payment, cookie, or credential information.

Separate raw release evidence also captures the popup in light, dark, and Off states. Those raw popup captures are validation evidence rather than additional Web Store screenshots.

Before public submission, inspect every image once at full resolution to confirm that no account-specific information is visible and that the screenshots still accurately represent current extension behavior.
