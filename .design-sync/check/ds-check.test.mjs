import { test } from 'node:test'
import assert from 'node:assert/strict'
import { join } from 'node:path'
import { collectViolations, countsOf, scopedFiles, scopeFloorError } from './ds-check.mjs'

// Verified independently against the tree on 2026-07-19. If a refactor
// legitimately changes these, update baseline.json in the same commit.
const EXPECTED = {
  'no-raw-palette': 69,
  'no-bare-button': 9,
  'no-adhoc-input': 11,
  'no-inline-style': 0,
}

test('scans exactly the 8 in-scope feature files', () => {
  const files = scopedFiles()
  assert.equal(files.length, 8, 'scope must cover exactly the 8 non-test feature files')
  for (const file of files) {
    assert.match(file, /^web\/src\/features\/[^/]+\/[^/]+\.tsx$/)
    assert.doesNotMatch(file, /\.test\.tsx$/)
  }
})

test('every violation points at an in-scope file', () => {
  const violations = collectViolations()
  const files = new Set(Object.values(violations).flat().map((v) => v.file))
  assert.ok(files.size > 0, 'violation set must not be empty — an empty set means a broken scan')
  for (const file of files) {
    assert.match(file, /^web\/src\/features\/[^/]+\/[^/]+\.tsx$/)
    assert.doesNotMatch(file, /\.test\.tsx$/)
  }
})

test('reports the verified counts for the current tree', () => {
  assert.deepEqual(countsOf(collectViolations()), EXPECTED)
})

test('no rule silently matches nothing', () => {
  const counts = countsOf(collectViolations())
  // no-inline-style is legitimately 0 (its only occurrence is allowlisted).
  const mustBeNonZero = ['no-raw-palette', 'no-bare-button', 'no-adhoc-input']
  for (const id of mustBeNonZero) {
    assert.ok(counts[id] > 0, `${id} returned 0 — likely a broken pattern, not a clean tree`)
  }
})

test('violations carry a usable file and line', () => {
  const hit = collectViolations()['no-bare-button'][0]
  assert.ok(hit.file.endsWith('.tsx'))
  assert.ok(Number.isInteger(hit.line) && hit.line > 0)
})

test('scopedFiles() resolves the scan root from its own module location, not process.cwd()', () => {
  const repoRoot = process.cwd()
  process.chdir(join(repoRoot, 'web'))
  try {
    const files = scopedFiles()
    assert.equal(files.length, 8, 'must still find all 8 in-scope files when cwd is web/')
    for (const file of files) {
      assert.match(file, /^web\/src\/features\/[^/]+\/[^/]+\.tsx$/)
    }
  } finally {
    process.chdir(repoRoot)
  }
})

test('scopeFloorError refuses an empty scan', () => {
  const error = scopeFloorError(0, 8)
  assert.ok(error, 'an empty scan must be rejected')
  assert.match(error, /0 in-scope source files/)
})

test('scopeFloorError refuses a scan that found fewer files than the baseline expects', () => {
  const error = scopeFloorError(5, 8)
  assert.ok(error, 'a shrunken scan must be rejected')
  assert.match(error, /5 in-scope source files/)
  assert.match(error, /8/)
})

test('scopeFloorError allows a scan at or above the expected file count', () => {
  assert.equal(scopeFloorError(8, 8), null)
  assert.equal(scopeFloorError(9, 8), null)
})
