import { test } from 'node:test'
import assert from 'node:assert/strict'
import { extractTags } from './scan-tags.mjs'

test('extracts a simple self-closing tag', () => {
  const tags = extractTags('<input className="a" />', ['input'])
  assert.equal(tags.length, 1)
  assert.equal(tags[0].name, 'input')
  assert.match(tags[0].text, /className="a"/)
})

test('does not stop at the > inside an arrow function', () => {
  const src = '<input onChange={(e) => set(e)} className="border-gray-300" />'
  const tags = extractTags(src, ['input'])
  assert.equal(tags.length, 1)
  assert.match(tags[0].text, /border-gray-300/, 'className after => must be captured')
})

test('spans newlines in multi-line JSX', () => {
  const src = [
    '<input',
    '  value={v}',
    '  className="border border-gray-300"',
    '/>',
  ].join('\n')
  const tags = extractTags(src, ['input'])
  assert.equal(tags.length, 1)
  assert.match(tags[0].text, /border-gray-300/)
})

test('handles nested braces in props', () => {
  const src = '<input style={{ width: `${p}%` }} className="x" />'
  const tags = extractTags(src, ['input'])
  assert.equal(tags.length, 1)
  assert.match(tags[0].text, /className="x"/)
})

test('captures non-self-closing tags such as select', () => {
  const src = '<select className="border-gray-300"><option/></select>'
  const tags = extractTags(src, ['select'])
  assert.equal(tags.length, 1)
  assert.match(tags[0].text, /border-gray-300/)
  assert.doesNotMatch(tags[0].text, /option/, 'open tag only, not children')
})

test('matches multiple names and reports each occurrence', () => {
  const src = '<input a /><textarea b /><input c />'
  const tags = extractTags(src, ['input', 'textarea'])
  assert.deepEqual(tags.map((t) => t.name), ['input', 'textarea', 'input'])
})

test('does not match a name that is a prefix of a longer tag', () => {
  const tags = extractTags('<inputGroup x />', ['input'])
  assert.equal(tags.length, 0, 'word boundary must prevent inputGroup matching input')
})

test('falls back to end of source on an unterminated tag', () => {
  // Brace depth never returns to 0, so no `>` at depth 0 is ever found.
  const src = '<input className={cn("a"'
  const tags = extractTags(src, ['input'])
  assert.equal(tags.length, 1)
  assert.equal(tags[0].index, 0)
  assert.equal(tags[0].text, src, 'documented fallback: consume to end of source')
})
