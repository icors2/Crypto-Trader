# UI design reference

For web UIs. Prefer one coherent system over novelty.

## Tokens

- Define spacing, radii, and type sizes once (Tailwind theme or CSS variables).
- Prefer a small type scale (e.g. xs/sm/base/lg/xl) over one-off pixel sizes.
- Color: primary, muted, destructive, background, foreground — map to CSS variables for dark mode.

## Component library

- **One kit only** (e.g. shadcn/ui). Do not mix with Material + Chakra + custom duplicates.
- Compose primitives; avoid one-off styled copies of the same button.

## Layout and responsive

- Mobile-first. Check ~375px, ~768px, and ~1280px.
- Avoid horizontal scroll on mobile for primary flows.
- Use consistent page padding and max-width for readable content.

## Dark mode

- If the app supports dark mode, tokens must cover both; do not hard-code light-only greys for critical text.

## See also

- `assets/reference/ux-states.md`
- `assets/checklists/ui-polish.md`
- `.cursor/skills/polish-ui/SKILL.md`
