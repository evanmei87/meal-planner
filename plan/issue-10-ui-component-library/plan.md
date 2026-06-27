# UI Component Library Spike — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> Originating issue: [#10 — spike: Research and Evaluate UI Component Libraries](https://github.com/evanmei87/meal-planner/issues/10)

**Goal:** Land the UI component library research/decision document and open a PR for review, satisfying issue #10's acceptance criteria.

**Architecture:** This is a documentation-only spike. The deliverable `docs/ui-component-research.md` is already authored and committed on branch `spike/10-ui-component-library`. No application code, tests, or dependency changes are in scope (per the design decision: "decision + adoption plan, stops short of writing component code"). The remaining work is verification of acceptance criteria and PR creation.

**Tech Stack:** Markdown docs; `git`; GitHub CLI (`gh`).

## Global Constraints

- React-only codebase — the doc must not reintroduce the inaccurate "React + Vue" premise (corrected in §1 of the doc).
- Plan files under `plan/` are always committed to git (per `CLAUDE.md`).
- Branch: `spike/10-ui-component-library`. Base branch for PR: `main`.
- No application code, no `web/package.json` changes, no component scaffolding in this spike.

---

### Task 1: Verify the research doc satisfies issue #10 acceptance criteria

**Files:**
- Verify: `docs/ui-component-research.md`
- (No test files — documentation deliverable.)

**Interfaces:**
- Consumes: the committed `docs/ui-component-research.md`.
- Produces: a verified doc ready for PR; no code symbols.

- [ ] **Step 1: Check each acceptance criterion against the doc**

Confirm every item below is present in `docs/ui-component-research.md`:

  - A Markdown file exists at a sensible docs path (`docs/ui-component-research.md`). ✓ created.
  - At least 7 UI kits evaluated. → doc has **9** (§4.1–4.9).
  - Each kit includes all five required sub-dimensions: **Overview**, stack compatibility (reframed as **React + Tailwind fit**, per the React-only correction), **Customizability**, **Accessibility (a11y)**, **Licensing/Cost**. (Doc adds a sixth, Bundle/lock-in.)
  - A final recommendation / top choice with developer-experience-vs-polish weighing. → §5 + §8.
  - (PR creation is Task 2.)

- [ ] **Step 2: Confirm the doc does not reintroduce the Vue premise**

Read §1 and §4. Verify the doc states the repo is React-only and reframes the compatibility dimension accordingly. If any "React and Vue" requirement language leaked into the evaluation, fix it inline and amend the commit:

```bash
git add docs/ui-component-research.md
git commit --amend --no-edit
```

Expected: §1 "Premise correction" present; no kit evaluated on Vue compatibility.

- [ ] **Step 3: Confirm the plan file is committed**

Run:
```bash
git add plan/issue-10-ui-component-library/plan.md
git commit -m "docs: commit plan for issue #10 UI component library spike (#10)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```
Expected: plan file committed on `spike/10-ui-component-library`.

---

### Task 2: Open the pull request

**Files:**
- None modified — this task only pushes and opens a PR.

**Interfaces:**
- Consumes: committed branch `spike/10-ui-component-library` (doc + plan).
- Produces: an open PR against `main` referencing issue #10.

- [ ] **Step 1: Push the branch**

Run:
```bash
git push -u origin spike/10-ui-component-library
```
Expected: branch published to origin.

- [ ] **Step 2: Open the PR with a summary that maps to the acceptance criteria**

Run (PowerShell here-string for the body, or `gh` with `--body-file`):
```bash
gh pr create --base main --head spike/10-ui-component-library \
  --title "docs: UI component library research & adoption plan (#10)" \
  --body "Closes #10.

Research + decision + adoption plan for the Food & Nutrition Intelligence UI.

- Corrects the inaccurate React+Vue premise — the repo is React-only.
- Evaluates 9 kits on Overview / React+Tailwind fit / Customizability / a11y / Licensing / bundle.
- Recommends **shadcn/ui on the Base UI engine**; Mantine documented as the principal alternative.
- Adoption plan maps the choice to upcoming issues (#6 meal detail Dialog, #38 color tokens, #28/#37 calendar, #36 @dnd-kit) plus Tremor for nutrition charts.
- Honest call-out: the calendar layout is not solved by any library and stays bespoke.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```
Expected: PR URL returned.

- [ ] **Step 3: Confirm the PR is open**

Run:
```bash
gh pr view --json url,state,title
```
Expected: `"state": "OPEN"` with the title above.

---

## Self-Review

**Spec coverage:** Every #10 acceptance criterion maps to a step — markdown file (already created), ≥7 kits with five sub-dimensions (Task 1 Step 1), final recommendation (in doc §5/§8, verified Task 1), PR opened (Task 2). ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases" — every step has an exact command. ✓

**Type consistency:** N/A — no code symbols in this docs-only plan. ✓
