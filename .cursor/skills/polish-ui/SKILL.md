---
name: polish-ui
description: Pre-ship UI polish pass — responsive, a11y, empty/error states, favicon/OG. Use before deploy-app for user-facing web changes or when the user asks to polish the UI.
---

# Polish UI

Looks matter to vibe users. Run this before a public URL.

## When to use

- Before `deploy-app` for a user-visible web app
- After a feature that adds screens or flows
- User asks to polish, clean up UI, or fix empty states

## Preconditions

- App runnable locally (or preview URL)
- Read `assets/checklists/ui-polish.md`, `assets/reference/ui-design.md`, `assets/reference/ux-states.md`, `assets/reference/seo-and-metadata.md`

## Steps

1. Walk `assets/checklists/ui-polish.md`.
2. Browser-check the demo moment at ~375px, ~768px, and ~1280px.
3. Toggle dark mode if the app supports it.
4. Keyboard-only: reach and activate the primary CTA.
5. Confirm loading / empty / error paths for the main view (force empty by clearing data or using a fresh account when needed).
6. Confirm favicon and document title; for public marketing pages, sanity-check OG tags.
7. If the app is public-facing and legal templates were copied, confirm footer links.
8. Fix gaps or list what remains for the user.

## Verify

- Checklist items either done or explicitly deferred with reason
- Viewport widths you actually opened are stated

## Failure modes

- "Looks fine on my laptop width" only → check mobile
- Shipping blank lists without empty states → add copy + CTA
- Mixing a second component library during polish → don't
