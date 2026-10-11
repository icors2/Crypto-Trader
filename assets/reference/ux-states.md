# UX states and accessibility

Every primary view needs intentional states — blank screens look broken.

## States

| State | Expectation |
| --- | --- |
| Loading | Skeleton or spinner; do not layout-shift violently |
| Empty | Explain what goes here + primary action to create |
| Error | Human message + retry when safe; no raw stacks in UI |
| Success | Confirm destructive or paid actions |

Forms: inline validation, disable double-submit, preserve input on error when possible.

Optimistic updates: OK for low-risk toggles; reconcile on failure.

## Accessibility baseline

- Interactive elements keyboard-reachable (`Tab` / `Enter` / `Space`)
- Controls have accessible names (label, `aria-label`, or labelledby)
- Visible focus styles (do not `outline: none` without a replacement)
- Text and UI contrast sufficient against background
- Images that convey meaning have `alt`; decorative images empty `alt`
- Do not rely on color alone for errors

## See also

- `assets/checklists/ui-polish.md`
- Globbed rule: `.cursor/rules/30-frontend.mdc`
