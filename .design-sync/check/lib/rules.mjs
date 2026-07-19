import { extractTags } from './scan-tags.mjs'

/** 1-indexed line number for a character offset. */
export function lineOf(src, index) {
  let line = 1
  for (let i = 0; i < index && i < src.length; i++) {
    if (src[i] === '\n') line++
  }
  return line
}

const PALETTE_FAMILIES = ['gray', 'green', 'blue', 'amber', 'red', 'slate', 'zinc', 'orange', 'cyan', 'purple']
const PALETTE = new RegExp(
  `\\b(?:bg|text|border|ring|from|to|via)-(?:${PALETTE_FAMILIES.join('|')})-\\d{2,3}\\b`,
  'g',
)

/** Files permitted to use inline style, with the reason. */
const INLINE_STYLE_ALLOWLIST = [
  // Percentage bar width is a runtime value and cannot be a Tailwind class.
  'web/src/features/meals/MacroDisplay.tsx',
]

const matchAll = (src, regex) =>
  [...src.matchAll(regex)].map((m) => ({ line: lineOf(src, m.index), text: m[0] }))

const tagsContaining = (src, names, needle) =>
  extractTags(src, names)
    .filter((tag) => needle.test(tag.text))
    .map((tag) => ({ line: lineOf(src, tag.index), text: `<${tag.name}>` }))

export const RULES = [
  {
    id: 'no-raw-palette',
    describe: 'Tailwind palette literal; use a semantic token',
    find: (src) => matchAll(src, PALETTE),
  },
  {
    id: 'no-bare-button',
    describe: 'bare <button>; use the Button primitive',
    find: (src) => extractTags(src, ['button']).map((tag) => ({ line: lineOf(src, tag.index), text: '<button>' })),
  },
  {
    id: 'no-adhoc-input',
    describe: 'ad-hoc styled input; use a shared Input primitive',
    find: (src) => tagsContaining(src, ['input', 'select', 'textarea'], /border-/),
  },
  {
    id: 'no-inline-style',
    describe: 'inline style prop; use tokens and Tailwind classes',
    find: (src, file) => {
      const normalized = file.replace(/\\/g, '/')
      if (INLINE_STYLE_ALLOWLIST.some((allowed) => normalized.endsWith(allowed))) return []
      return matchAll(src, /style=\{\{/g)
    },
  },
]
