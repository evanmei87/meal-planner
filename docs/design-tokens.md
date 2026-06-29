# Design Tokens

> Foundation for issue #41. Tokens are CSS variables in `web/src/index.css`, mapped to Tailwind utilities via `@theme inline`. Consume these tokens — do not re-derive raw colors in feature code.

## Color — semantic (shadcn, neutral base)

Standard shadcn tokens drive the app surface. Use the Tailwind utilities they generate:

| Token utility | Use for |
|---|---|
| `bg-background` / `text-foreground` | page surface + body text |
| `bg-card` / `text-card-foreground` | card surfaces |
| `bg-muted` / `text-muted-foreground` | subdued fills + secondary text |
| `bg-primary` / `text-primary-foreground` | primary actions and **active/selected state** |
| `bg-accent` / `text-accent-foreground` | hover/active accents |
| `border-border`, `bg-input`, `ring-ring` | borders, inputs, focus rings |
| `text-destructive`, `bg-destructive` | errors / destructive actions |

**Active/selected state:** map to `bg-primary text-primary-foreground`. #28 (today highlight), #38 (selected day), and the nav active link all converge on this token when their issues migrate. (Those screens are out of scope for #41 and still use hard-coded green for now.)

## Color — exercise-type palette (for #38)

Each type has a strong value (border) and a subtle tint (background):

| Type | Strong (`--color-exercise-<type>`) | Subtle (`-subtle`) |
|---|---|---|
| running | green-600 | green-50 |
| walking | blue-500 | blue-50 |
| biking | orange-500 | orange-50 |
| swimming | cyan-500 | cyan-50 |
| strength | purple-500 | purple-50 |

Utilities: `border-exercise-running`, `bg-exercise-running-subtle`, etc. #38 builds `cva` variants on top of these rather than hard-coding Tailwind classes.

## Spacing & shape

- **Spacing:** use Tailwind's default spacing scale (`p-2`, `gap-3`, `space-y-6`, …). No custom spacing variables.
- **Radius:** `--radius` (shadcn default) with `rounded-sm` / `rounded-md` / `rounded-lg` derived from it.

## Typography

- **Font:** `--font-sans` (system sans stack from Tailwind 4 / shadcn default).
- **Type scale:** Tailwind's default `text-xs … text-2xl` with their paired line-heights. Headings in the app use `text-lg font-semibold`; body uses `text-sm`.
