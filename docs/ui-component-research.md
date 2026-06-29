# UI Component Library Research & Adoption Plan

> Deliverable for [issue #10 — spike: Research and Evaluate UI Component Libraries for Food & Nutrition Intelligence](https://github.com/evanmei87/meal-planner/issues/10).
> Date: 2026-06-26 · Status: recommendation for review

## TL;DR

Adopt **shadcn/ui running on the Base UI engine** as the core component library, and re-skin the app incrementally on top of it. Add three complementary, single-purpose libraries as specific roadmap needs arrive: **@dnd-kit** (drag-and-drop), **Tremor** (nutrition/calorie charts), and optionally **MagicUI** (animation polish). The principal alternative considered, **Mantine**, is faster to "done" but conflicts with our Tailwind-native, low-lock-in priorities.

This effort is research + decision + an adoption plan only. It deliberately stops short of writing component code.

---

## 1. Premise correction: this is a React-only codebase

Issue #10 frames the evaluation around a frontend "ecosystem [that] involves both React and Vue." The repository does not match that premise. `web/package.json` declares React 18, `react-router-dom`, `@tanstack/react-query`, and **Tailwind CSS 4**, built with Vite and tested with Vitest. There is no Vue anywhere in the tree, and both `CLAUDE.md` and the existing exercise issues (#28) describe a single React + TypeScript SPA.

Consequence: the decisive evaluation axis is **React + Tailwind fit**, not framework-agnosticism. Web Components and "wrappers for both React and Vue" — emphasized in the original ticket — are not requirements. This correction materially narrows and clarifies the field.

## 2. What we are optimizing for

In priority order, agreed during design:

1. **Visual polish out-of-the-box** — the UI is functional but plain; we want it to look designed with minimal styling effort.
2. **Developer velocity** — low friction with the existing Tailwind setup; easy to customize.
3. **Small bundle / low lock-in** — minimal runtime, easy to remove or swap, no proprietary CSS system.
4. **AI/agent-friendliness** — predictable structure and strong ecosystem coverage so a coding agent can scaffold and extend components reliably.

Accessibility is valued but was not ranked as the headline priority; it is treated as a tie-breaker and a baseline expectation rather than the deciding factor.

## 3. Evaluation dimensions

Per #10's acceptance criteria, each kit below is assessed on:

- **Overview** — design aesthetic and philosophy.
- **React + Tailwind fit** — how cleanly it integrates with our React 18 + Tailwind 4 stack (this replaces the original "React and Vue compatibility" dimension, per §1).
- **Customizability** — how easy it is to theme or override styles.
- **Accessibility (a11y)** — out-of-the-box keyboard nav, ARIA, screen-reader support.
- **Licensing / Cost** — open-source vs premium.
- **Bundle / lock-in** — runtime weight and how hard it is to remove or replace.

GitHub star counts are approximate, Q2 2026.

---

## 4. The field (9 kits evaluated)

### 4.1 shadcn/ui  ★ ~114k — *recommended core*

- **Overview:** Not a dependency but a CLI that copies fully-styled component source into your repo. Modern, neutral aesthetic. Built on a headless primitive engine (Radix historically; **Base UI since Jan 2026**) with Tailwind styling and `class-variance-authority` variants.
- **React + Tailwind fit:** Native. It *is* Tailwind — no parallel CSS system, no coexistence cost. Drops directly onto our existing config.
- **Customizability:** Maximum. The component code lives in our tree (`web/src/components/ui/...`); we edit it like our own. Theming via CSS variables / Tailwind tokens.
- **a11y:** Inherited from the underlying primitives (Base UI / Radix) — strong keyboard and ARIA behavior for dialogs, menus, etc.
- **Licensing:** MIT, free.
- **Bundle / lock-in:** Lowest lock-in in the field — you own the files and can delete any of them; only the headless primitives are runtime deps, and they tree-shake per component.
- **Note:** Most-starred React UI library in the ecosystem and the single most AI-agent-friendly option (deterministic `npx shadcn add <component>`, predictable file layout, largest training-data footprint).

### 4.2 Base UI  ★ ~rising (MUI team) — *the engine we choose*

- **Overview:** Headless, unstyled primitives from the MUI + former Radix maintainers — the actively-maintained successor to Radix's primitive layer.
- **React + Tailwind fit:** Excellent — unstyled, so Tailwind owns all presentation.
- **Customizability:** Total; you bring every style.
- **a11y:** Strong, with cleaner APIs than Radix for complex interactions (combobox, multi-select, nested menus).
- **Licensing:** MIT, free.
- **Bundle / lock-in:** Low; headless primitives only.
- **Note:** Better-resourced maintenance than Radix (dedicated MUI engineers). We adopt it *as the engine under shadcn/ui*, not as a standalone build-everything-yourself layer.

### 4.3 Radix UI  ★ ~mature (WorkOS)

- **Overview:** The original headless primitive set that shadcn was historically built on; AAA-minded accessibility.
- **React + Tailwind fit:** Excellent (unstyled).
- **Customizability:** Total.
- **a11y:** Best-in-class, widely cited as the reference.
- **Licensing:** MIT, free.
- **Bundle / lock-in:** Low.
- **Note:** Still solid, but maintained by a small core team — the one durable risk that choosing Base UI as the engine avoids. Documented here as the fallback engine if a needed component is Radix-only.

### 4.4 Headless UI  ★ ~26k (Tailwind Labs)

- **Overview:** ~12 unstyled-but-behavioral components (Dialog, Menu, Combobox, Listbox, etc.).
- **React + Tailwind fit:** Native — same vendor as Tailwind.
- **Customizability:** Total; you style everything.
- **a11y:** Good for the components it covers.
- **Licensing:** MIT, free.
- **Bundle / lock-in:** Very low.
- **Why not core:** Catalog is too small to be the primary system — anything beyond the ~12 components is hand-built. Weaker on the visual-polish priority.

### 4.5 React Aria  ★ (Adobe)

- **Overview:** Accessibility-first hooks (and unstyled components) covering a very broad behavior surface.
- **React + Tailwind fit:** Good (bring your own styles).
- **Customizability:** Total.
- **a11y:** Best-in-class — the gold standard.
- **Licensing:** Apache-2.0, free.
- **Bundle / lock-in:** Low–moderate.
- **Why not core:** Most hand-work of any option; optimized for teams where a11y is the top priority, which is not our ranked weighting.

### 4.6 Mantine  ★ ~30k — *principal alternative*

- **Overview:** Batteries-included styled library: 120+ components, 100+ hooks, including its own drag-and-drop, date pickers, notifications, spotlight search, rich-text editor.
- **React + Tailwind fit:** Workable but not native — ships its own CSS/PostCSS system that coexists awkwardly with Tailwind (two styling models in one app).
- **Customizability:** Strong via its theme object, but you customize *its* system rather than owning the components.
- **a11y:** Good.
- **Licensing:** MIT, free.
- **Bundle / lock-in:** Higher — components are imports you don't own; removing Mantine later is a real migration.
- **Community read:** *"Mantine if you want things done and lead a happy life; shadcn if you want to customize a lot and occasionally think about killing yourself."* Captures the velocity-vs-ownership trade-off exactly. Strong choice if velocity outranked ownership — but for us it doesn't.

### 4.7 MUI (Material UI)  ★ ~95k

- **Overview:** The most widely adopted styled React library; enormous catalog; Material Design aesthetic.
- **React + Tailwind fit:** Poor — Emotion/CSS-in-JS runtime that conflicts with Tailwind; opinionated Material look is hard to neutralize.
- **Customizability:** Powerful theming, but heavyweight.
- **a11y:** Good.
- **Licensing:** MIT core; premium tiers (MUI X / Pro) for advanced data grid, pickers.
- **Bundle / lock-in:** Large bundle, high lock-in.
- **Why not:** Conflicts with both the Tailwind and low-lock-in priorities.

### 4.8 Ant Design  ★ ~97k

- **Overview:** Enterprise-grade, 60+ components, dense data-heavy aesthetic.
- **React + Tailwind fit:** Poor — own design system + CSS-in-JS, Tailwind friction.
- **Customizability:** Theming exists but fights the strong default look.
- **a11y:** Moderate.
- **Licensing:** MIT.
- **Bundle / lock-in:** Largest bundle in the field; high lock-in.
- **Why not:** Enterprise-dashboard styling and bundle weight are wrong for a lean personal nutrition app.

### 4.9 DaisyUI  ★ ~36k

- **Overview:** A Tailwind *plugin* adding semantic, themeable component classes (`btn`, `card`, `modal`).
- **React + Tailwind fit:** Native — pure Tailwind plugin, zero JS runtime.
- **Customizability:** Easy theming via CSS variables.
- **a11y:** Minimal — provides classes only, **no JS behavior or ARIA** (you wire interaction/focus yourself).
- **Licensing:** MIT, free.
- **Bundle / lock-in:** Essentially zero runtime.
- **Why not core:** No behavioral/accessibility layer for dialogs, menus, comboboxes — exactly the interactive pieces #6 needs. Viable as a lightweight *styling supplement*, not as the system.

---

## 5. Decision

**Core library: shadcn/ui on the Base UI engine.**

It is the only option that wins on all four ranked priorities:

| Priority | shadcn/ui (Base UI) | Mantine (alternative) |
|---|---|---|
| Visual polish OOTB | Strong, modern defaults | Strong, more components ready |
| Developer velocity | High (Tailwind-native, zero conflict) | High (but parallel CSS system) |
| Small bundle / low lock-in | **Best** — own the files, headless deps | Weaker — imports you don't own |
| AI/agent-friendliness | **Best** — deterministic CLI, largest coverage | Good |
| a11y (tie-breaker) | Strong (Base UI primitives) | Good |

Choosing **Base UI** as the underlying engine (now officially supported by shadcn as of January 2026) removes shadcn's one durable weakness — reliance on Radix's small maintenance team — by moving to a primitive layer with dedicated MUI engineering behind it.

**Mantine** is the documented runner-up: pick it only if "fastest to done" later outranks ownership and Tailwind-nativeness. That is not our current weighting.

## 6. Adoption plan (mapped to the roadmap)

Scope: structure and sequence only. No component code is written as part of issue #10.

| Need | Provided by | Notes |
|---|---|---|
| **Foundation** | shadcn/ui init (Base UI) + design tokens | `npx shadcn init`; define color/spacing/typography tokens; then incrementally re-skin existing `web/src/components/` (`Card`, `Table`, `ErrorBanner`, `Spinner`) |
| **#6 click-into-meals** (recipe steps, serving sizes, macros) | shadcn **Dialog / Drawer** | The clearest direct win — a real modal pattern replaces the plain table click-through |
| **#38 color-coded exercise types** | design tokens + `cva` variants | Centralized color tokens keep the palette consistent across calendar + lists |
| **#28 / #37 weekly & monthly calendar** | ⚠️ custom Tailwind grid | **No library solves this** — shadcn's "Calendar" is a date *picker*, not an event calendar. Honest call-out: this stays bespoke |
| **#36 drag-and-drop reordering** | **@dnd-kit** (complementary) | The standard React DnD primitive; not provided by any general component library we'd pick |
| **Nutrition intelligence — macro/calorie charts** | **Tremor** (complementary) | Tailwind-native charts / KPI cards / metric tiles; the natural fit for the "Food & Nutrition intelligence" data-viz the product is named for |
| **Optional animation polish** | **MagicUI** (complementary) | Framer-Motion + Tailwind effects that layer on top of shadcn; adopt only if/when polish is wanted |

### Sequencing

1. **Foundation first** — init + tokens + re-skin the four existing shared components. This lands *before* the exercise suite (#28–38) so every new screen is built on the system from day one instead of retrofitted.
2. **Per-feature thereafter** — pull in Dialog for #6, color tokens for #38, @dnd-kit for #36, Tremor for nutrition charts, as those issues are scheduled.

## 7. Out of scope & risks

- **No mass rewrite.** Re-skin is incremental and component-by-component; the app stays shippable throughout.
- **Calendar layout remains bespoke** — do not expect the library to provide it (§6).
- **Base UI vs Radix APIs differ** — relevant if a future component is only available for Radix; documented so contributors aren't surprised.
- **Bundle discipline** — add components on demand via the CLI; do not bulk-import.
- **Complementary deps are additive** — @dnd-kit, Tremor, MagicUI are independent, single-purpose, and individually removable.

## 8. Recommendation summary

> Adopt **shadcn/ui (Base UI engine)** as the core component system. Establish the foundation (init + tokens + re-skin existing components) before the exercise feature suite lands. Add **@dnd-kit**, **Tremor**, and optionally **MagicUI** as discrete, complementary dependencies when their specific features are scheduled. Reconsider **Mantine** only if future priorities flip from ownership toward maximum out-of-the-box velocity.

## Sources

- [14 Best React UI Component Libraries in 2026 — Untitled UI](https://www.untitledui.com/blog/react-component-libraries)
- [The best React UI component libraries of 2026 — Croct](https://blog.croct.com/post/best-react-ui-component-libraries)
- [shadcn/ui — Base UI changelog (Jan 2026)](https://ui.shadcn.com/docs/changelog/2026-01-base-ui)
- [shadcn vs Radix vs Base UI: Which One Should a Junior Pick in 2026? — dev.to](https://dev.to/edriso/shadcn-vs-radix-vs-base-ui-which-one-should-a-junior-pick-in-2026-1jml)
- [ShadCN UI vs Mantine (2026) — BSWEN](https://docs.bswen.com/blog/2026-03-22-shadcn-vs-mantine-comparison/)
- [11+ Best Shadcn Alternatives — Tailgrids](https://tailgrids.com/blog/shadcn-alternatives)
