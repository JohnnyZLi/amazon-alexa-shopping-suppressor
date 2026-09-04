# Support

For bugs, compatibility problems, or marketplace-specific regressions, open a GitHub issue in this repository.

## Before reporting a problem

1. Confirm the problem occurs with the current release.
2. Disable other Alexa/Rufus suppressors and remove experimental custom blocker rules so only one tool is modifying the page.
3. Note whether the toolbar **Suppressor** switch is On or Off.
4. Toggle the suppressor Off and check whether the problem disappears after the extension restores its managed page state.
5. If needed, also check whether the problem disappears when the extension itself is disabled from `chrome://extensions`.
6. If useful, temporarily set `DEBUG: true` in `content.js`, reload the unpacked extension, and collect `[AlexaSuppressor]` console messages.

## Include in a bug report

- Chrome/Chromium version.
- Extension version or commit SHA.
- Saved Suppressor toggle state.
- Amazon marketplace (for example, `amazon.com` or `amazon.co.uk`).
- Page type (home, search, product, cart, account, etc.).
- What happened and what you expected.
- Whether toggling the suppressor Off changes the problem.
- A screenshot if it does not expose private information.
- Relevant `[AlexaSuppressor]` debug output.

## Do not include

Do not post Amazon order numbers, names, addresses, payment information, account identifiers, session tokens, cookies, or other personal/private data in a public issue.

## Security reports

For suspected security vulnerabilities, follow `SECURITY.md` rather than posting sensitive exploit details in a normal public issue.
