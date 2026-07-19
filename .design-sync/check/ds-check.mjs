#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { pathToFileURL, fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { RULES } from './lib/rules.mjs'
import { scopedFiles } from './lib/files.mjs'

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

function runGate(violations) {
  const counts = countsOf(violations)
  const baseline = JSON.parse(readFileSync(BASELINE_PATH, 'utf8'))
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
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const violations = collectViolations()
  if (process.argv.includes('--gate')) runGate(violations)
  else if (process.argv.includes('--json')) console.log(JSON.stringify(countsOf(violations), null, 2))
  else reportToConsole(violations)
}
