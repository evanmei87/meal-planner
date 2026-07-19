#!/usr/bin/env node
import { readFileSync, writeFileSync, globSync } from 'node:fs'
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
    for (const { id, was, now } of regressions) {
      const rule = RULES.find((r) => r.id === id)
      console.error(`  ${id}: ${was} -> ${now}  (${rule?.describe ?? 'unknown rule'})`)
      for (const hit of violations[id].slice(-(now - was))) {
        console.error(`    ${hit.file}:${hit.line}  ${hit.text}`)
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
