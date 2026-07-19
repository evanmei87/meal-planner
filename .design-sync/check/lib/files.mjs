import { globSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SCOPE = 'web/src/features/*/*.tsx'

// This file lives at <repo>/.design-sync/check/lib/files.mjs, so the repo
// root is three directories up. Resolving from the module's own location
// (rather than process.cwd()) means the scan finds the same files no matter
// where the CLI is invoked from.
export const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..')

/** In-scope source files, repo-relative with forward slashes. */
export function scopedFiles() {
  return globSync(SCOPE, { cwd: REPO_ROOT })
    .map((f) => f.replace(/\\/g, '/'))
    .filter((f) => !f.endsWith('.test.tsx'))
    .sort()
}
