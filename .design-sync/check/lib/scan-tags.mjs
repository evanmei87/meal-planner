/**
 * Extract JSX open-tags for the given element names.
 *
 * A regex like `<input[^>]*>` cannot be used here: JSX props contain arrow
 * functions, and the `>` in `=>` closes the character class before reaching
 * className. This scans forward tracking brace depth instead, so it survives
 * both arrow functions and newlines.
 *
 * @param {string} src source text
 * @param {string[]} names element names, e.g. ['input', 'select']
 * @returns {Array<{name: string, text: string, index: number}>} open tags
 */
export function extractTags(src, names) {
  const tags = []
  const opener = new RegExp(`<(${names.join('|')})\\b`, 'g')
  let match
  while ((match = opener.exec(src))) {
    const end = findTagEnd(src, match.index + match[0].length)
    tags.push({
      name: match[1],
      text: src.slice(match.index, end + 1),
      index: match.index,
    })
  }
  return tags
}

/** Index of the `>` closing this tag, skipping any `>` nested inside braces. */
function findTagEnd(src, start) {
  let depth = 0
  for (let i = start; i < src.length; i++) {
    const char = src[i]
    if (char === '{') depth++
    else if (char === '}') depth--
    else if (char === '>' && depth === 0) return i
  }
  return src.length - 1
}
