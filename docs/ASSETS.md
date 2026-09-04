# Release / Web Store assets

## Extension icons

Runtime icons are in `icons/` and are included in the extension package through `manifest.json`:

- `icon-16.png`
- `icon-32.png`
- `icon-48.png`
- `icon-128.png`

They are generated deterministically by `scripts/generate_icons.py` using only the Python standard library. The icon is original artwork: a generic chat bubble with a suppression slash. It intentionally does not use Amazon, Alexa, or Rufus logos.

## Chrome Web Store artwork

The Chrome Web Store listing graphics are kept in a separate submission bundle rather than the runtime extension ZIP:

- `promo-440x280.png`
- `marquee-1400x560.png`
- `screenshot-1-before-after-1280x800.png`
- `screenshot-2-full-width-1280x800.png`
- `screenshot-3-targeted-ui-1280x800.png`

The screenshots were built from real browser captures of the original Amazon sidebar failure. Account name, delivery location, and other identifying header information were removed by cropping. The promotional artwork does not use Amazon/Alexa/Rufus logos.

v0.3.0 adds a user-facing toolbar popup. Before Web Store submission, capture one current real-Chrome screenshot showing the popup's **Suppressor On/Off** switch. Keep the screenshot free of account-specific Amazon information and use it to supplement, not replace, the existing before/after evidence.

Before public submission, inspect every image once at full resolution to confirm that no account-specific information is visible and that the screenshots still accurately represent current Amazon behavior.
