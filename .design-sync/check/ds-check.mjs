#!/usr/bin/env node
import { readFileSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
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

function reportToConsole(violations) {
  const counts = countsOf(violations)
  for (const rule of RULES) {
    console.log(`${counts[rule.id].toString().padStart(4)}  ${rule.id}  — ${rule.describe}`)
  }
  console.log(`${Object.values(counts).reduce((a, b) => a + b, 0).toString().padStart(4)}  TOTAL`)
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const violations = collectViolations()
  if (process.argv.includes('--json')) {
    console.log(JSON.stringify(countsOf(violations), null, 2))
  } else {
    reportToConsole(violations)
  }
}
