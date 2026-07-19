import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { scopedFiles } from './files.mjs'

const STAMP_PATH = join(dirname(fileURLToPath(import.meta.url)), '..', 'review-stamp.json')

/**
 * Every className attribute value in `src`, quoted or braced.
 *
 * Only className is hashed, not whole files: a logic refactor must not make a
 * visual review overdue, or the notice gets ignored within a week. Changing
 * `p-4` to `p-6` must.
 */
export function extractClassNames(src) {
  const values = []
  const attr = /className=/g
  let match
  while ((match = attr.exec(src))) {
    const start = match.index + match[0].length
    if (src[start] === '"') {
      const end = src.indexOf('"', start + 1)
      values.push(src.slice(start, end + 1))
    } else if (src[start] === '{') {
      values.push(
        src
          .slice(start, findBraceEnd(src, start) + 1)
          .replace(/\s+/g, ' ')
          .replace(/\(\s+/g, '(')
          .replace(/\s+\)/g, ')')
      )
    }
  }
  return values
}

/** Index of the brace closing the one at `start`. */
function findBraceEnd(src, start) {
  let depth = 0
  for (let i = start; i < src.length; i++) {
    if (src[i] === '{') depth++
    else if (src[i] === '}' && --depth === 0) return i
  }
  return src.length - 1
}

export function currentStamp() {
  const parts = scopedFiles().map((file) => `${file}\n${extractClassNames(readFileSync(file, 'utf8')).join('\n')}`)
  return createHash('sha256').update(parts.join('\n')).digest('hex').slice(0, 16)
}

export function readStamp() {
  if (!existsSync(STAMP_PATH)) return null
  return JSON.parse(readFileSync(STAMP_PATH, 'utf8')).stamp ?? null
}

export function writeStamp(hash) {
  writeFileSync(STAMP_PATH, `${JSON.stringify({ stamp: hash }, null, 2)}\n`)
}

export function reviewIsStale() {
  return readStamp() !== currentStamp()
}
