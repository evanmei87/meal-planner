import { test } from 'node:test'
import assert from 'node:assert/strict'
import { extractClassNames, currentStamp } from './stamp.mjs'

test('extracts a quoted className', () => {
  assert.deepEqual(extractClassNames('<div className="p-4 gap-2" />'), ['"p-4 gap-2"'])
})

test('extracts a braced template-literal className', () => {
  const values = extractClassNames('<div className={`p-4 ${x}`} />')
  assert.equal(values.length, 1)
  assert.match(values[0], /p-4/)
})

test('extracts a braced call expression className', () => {
  const values = extractClassNames('<div className={cn("p-4", other)} />')
  assert.equal(values.length, 1)
  assert.match(values[0], /cn\("p-4", other\)/)
})

test('handles nested braces inside a braced className', () => {
  const values = extractClassNames('<div className={`w-${sizes[{a:1}.a]}`} />')
  assert.equal(values.length, 1, 'must not end at the first inner closing brace')
})

test('collapses whitespace so reformatting does not count as visual change', () => {
  const inline = extractClassNames('<div className={cn("a", "b")} />')
  const wrapped = extractClassNames('<div className={cn(\n  "a",\n  "b",\n)} />')
  assert.equal(inline[0].replace(/,\s*\)/, ')'), wrapped[0].replace(/,\s*\)/, ')'))
})

test('ignores non-className attributes', () => {
  assert.deepEqual(extractClassNames('<div id="p-4" data-x="gap-2" />'), [])
})

test('currentStamp is stable across repeated calls', () => {
  assert.equal(currentStamp(), currentStamp())
})

test('currentStamp is a 16-char hex digest', () => {
  assert.match(currentStamp(), /^[0-9a-f]{16}$/)
})
