# Meal Planner UI — Design Conventions

**Stack:** React + TypeScript, Tailwind v4, `@base-ui/react` primitives.

**Tokens:** All colors and radii come from CSS custom properties (`--color-*`, `--radius-*`) defined in `src/index.css`. Never hardcode hex values; use semantic token names (`bg-card`, `text-foreground`, `border-border`, `text-destructive`, etc.).

**Styling:** Use `cva` (class-variance-authority) for multi-variant components. Compose with `cn()` (clsx + tailwind-merge). Never write inline `style` props for themeable values.

**Spacing & sizing:** Use Tailwind spacing scale. Prefer `gap-*` and `p-*` over margins. Icon button sizes follow the `size` variants on Button: `icon-xs`, `icon-sm`, `icon`, `icon-lg`.

**Interactive elements:** Buttons use `@base-ui/react/button` for accessibility. Dialogs use `@base-ui/react/dialog`; content renders through a portal — always wrap `DialogContent` inside `Dialog`.

**Typography:** Geist Variable font loaded via `@fontsource-variable/geist`. Body text uses `text-foreground`; secondary/muted uses `text-muted-foreground`; destructive text uses `text-destructive`.

**Component shape:** Simple wrapper components (Card, ErrorBanner, Spinner) accept `className` for extension. Complex components (Button, Dialog) expose variant props. Table accepts typed `Column[]` and generic `rows`.
