# UI polish checklist

Use with the `polish-ui` skill before claiming a user-facing change is shippable.

## Layout and design

- [ ] One component library only
- [ ] Spacing/type look consistent with `assets/reference/ui-design.md`
- [ ] No obvious horizontal overflow on mobile (~375px)

## States

- [ ] Loading state for async primary views
- [ ] Empty state with a next action
- [ ] Error state without stack traces
- [ ] Forms: validation feedback + no double-submit footgun

## Responsive and theme

- [ ] Checked ~375 / ~768 / ~1280 widths
- [ ] Dark mode (if supported) readable

## Accessibility

- [ ] Keyboard can reach primary actions
- [ ] Buttons/inputs have labels or aria-names
- [ ] Focus visible

## Metadata (public apps)

- [ ] Title + favicon present
- [ ] OG tags if the page will be shared
- [ ] Footer links to Privacy / Terms when those templates are in use (`assets/templates/legal/`)

## Seed / demo

- [ ] Main list is not a confusing blank (seed or intentional empty state)
