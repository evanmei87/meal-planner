# Design Sync Notes

## Known render warns

- Dialog, DialogClose, DialogContent, DialogDescription, DialogTitle: `[RENDER_THIN]` "DOM content present but rendered height is 0px" — benign. `@base-ui/react` dialog renders content in a DOM portal with fixed positioning, which escapes the playwright measurement container. `cardMode: single` applied to all five. Previews confirmed via screenshot to render correctly (backdrop + modal visible, full content captured in `.render-check.json` texts).
