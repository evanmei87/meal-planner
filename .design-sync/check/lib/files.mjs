import { globSync } from 'node:fs'

const SCOPE = 'web/src/features/*/*.tsx'

/** In-scope source files, repo-relative with forward slashes. */
export function scopedFiles() {
  return globSync(SCOPE)
    .map((f) => f.replace(/\\/g, '/'))
    .filter((f) => !f.endsWith('.test.tsx'))
    .sort()
}
