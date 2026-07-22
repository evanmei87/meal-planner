#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { pathToFileURL, fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { RULES } from './lib/rules.mjs'
import { scopedFiles, REPO_ROOT } from './lib/files.mjs'
import { reviewIsStale } from './lib/stamp.mjs'

export { scopedFiles }

/** All violations, keyed by rule id. */
export function collectViolations() {
  const result = Object.fromEntries(RULES.map((rule) => [rule.id, []]))
  for (const file of scopedFiles()) {
    const src = readFileSync(file, 'utf8')
    for (const rule of RULES) {
      for (const hit of rule.find(src, file)) {
        result[rule.id].push({ file, line: hit.line, text: hit.text })
      }
    }
  }
  return result
}

export function countsOf(violations) {
  return Object.fromEntries(Object.entries(violations).map(([id, hits]) => [id, hits.length]))
}

const BASELINE_PATH = join(dirname(fileURLToPath(import.meta.url)), 'baseline.json')

// Stored in baseline.json alongside the rule counts. Prefixed with `_` so it
// reads unambiguously as metadata, not a rule ceiling — and it never can be
// mistaken for one in code, either: evaluateGate only ever looks up
// baseline[id] for ids drawn from `counts`, which is built from RULES and so
// never contains this key.
const SCOPED_FILE_COUNT_KEY = '_scopedFiles'

/**
 * Refuse to trust a scan whose file count can't support ratcheting the
 * baseline: an empty scan (e.g. wrong working directory) or a shrunken one
 * (files deleted or moved out of scope since the baseline was recorded)
 * must fail loudly rather than silently "improve" the baseline to numbers
 * that can never regress again. Pure function — the caller does the I/O.
 */
export function scopeFloorError(fileCount, expectedFileCount) {
  if (fileCount === 0) {
    return (
      'Design system check found 0 in-scope source files. Refusing to evaluate or update the ' +
      'baseline — this usually means the scan ran from an unexpected working directory. ' +
      `(expected ${expectedFileCount} files)`
    )
  }
  if (fileCount < expectedFileCount) {
    return (
      `Design system check found ${fileCount} in-scope source files, fewer than the ` +
      `${expectedFileCount} recorded in baseline.json. Refusing to ratchet the baseline down — ` +
      `if files were intentionally removed, update "${SCOPED_FILE_COUNT_KEY}" in baseline.json deliberately.`
    )
  }
  return null
}

/**
 * Compare counts to the baseline.
 *
 * A rule absent from the baseline has a ceiling of 0, so a newly added rule
 * cannot pass unnoticed. Pure function — the caller does the I/O.
 */
export function evaluateGate(counts, baseline) {
  const regressions = []
  const improvements = []
  for (const [id, now] of Object.entries(counts)) {
    const was = baseline[id] ?? 0
    if (now > was) regressions.push({ id, was, now })
    else if (now < was) improvements.push({ id, was, now })
  }
  return { ok: regressions.length === 0, regressions, improvements }
}

/** Repo-relative paths of files changed vs HEAD, or null if git is unavailable. */
function changedFiles() {
  try {
    const out = execFileSync('git', ['diff', '--name-only', 'HEAD'], { encoding: 'utf8' })
    return new Set(out.split('\n').map((line) => line.trim()).filter(Boolean))
  } catch {
    return null
  }
}

function reportToConsole(violations) {
  const counts = countsOf(violations)
  for (const rule of RULES) {
    console.log(`${counts[rule.id].toString().padStart(4)}  ${rule.id}  — ${rule.describe}`)
  }
  console.log(`${Object.values(counts).reduce((a, b) => a + b, 0).toString().padStart(4)}  TOTAL`)
}

function runGate(violations, fileCount) {
  const counts = countsOf(violations)
  const baseline = JSON.parse(readFileSync(BASELINE_PATH, 'utf8'))

  const floorError = scopeFloorError(fileCount, baseline[SCOPED_FILE_COUNT_KEY] ?? 0)
  if (floorError) {
    console.error(floorError)
    process.exit(1)
  }

  const { ok, regressions, improvements } = evaluateGate(counts, baseline)

  if (!ok) {
    console.error('Design system check failed — new violations introduced.\n')
    const changed = changedFiles()
    for (const { id, was, now } of regressions) {
      const rule = RULES.find((r) => r.id === id)
      console.error(`  ${id}: ${was} -> ${now}  (${rule?.describe ?? 'unknown rule'})`)
      const localized = changed ? violations[id].filter((hit) => changed.has(hit.file)) : []
      if (localized.length > 0) {
        console.error('    New violations in files you changed:')
        for (const hit of localized) {
          console.error(`    ${hit.file}:${hit.line}  ${hit.text}`)
        }
      } else {
        console.error(
          `    Could not localize the new violation(s). Run \`node .design-sync/check/ds-check.mjs\` to see all ${now} locations for this rule.`,
        )
      }
    }
    console.error('\nSee .design-sync/north-star.md for the invariants.')
    process.exit(1)
  }

  if (improvements.length > 0) {
    for (const { id, was, now } of improvements) {
      baseline[id] = now
      console.log(`Design system baseline ratcheted: ${id} ${was} -> ${now}`)
    }
    writeFileSync(BASELINE_PATH, `${JSON.stringify(baseline, null, 2)}\n`)
    console.log('Updated .design-sync/check/baseline.json — commit it with your change.')
  }

  // Advisory only — never exits non-zero. Tier 2 needs servers, a browser and
  // judgment, so a hook can report that review is overdue but cannot perform it.
  if (reviewIsStale()) {
    console.log('Tier 2 visual review is stale — page styling changed since the last /ds-review.')
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  // scopedFiles() resolves its scan root from its own module location, so it
  // returns correct repo-relative paths regardless of cwd. But everything
  // downstream (collectViolations' readFileSync here, and stamp.mjs's
  // currentStamp) reads those repo-relative paths back off disk assuming
  // cwd is the repo root. Normalize cwd once, up front, so the whole run is
  // consistent no matter which directory the CLI was invoked from.
  process.chdir(REPO_ROOT)
  const violations = collectViolations()
  if (process.argv.includes('--gate')) runGate(violations, scopedFiles().length)
  else if (process.argv.includes('--json')) console.log(JSON.stringify(countsOf(violations), null, 2))
  else reportToConsole(violations)
}
