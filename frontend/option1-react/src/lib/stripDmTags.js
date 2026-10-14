/** Mirror of backend CONTROL_TAG_PATTERN — strip internal DM directives from visible text */
const CONTROL_TAG_PATTERN =
  /\[(?:ROLL|COMBAT|ITEM|GOLD|XP|BUY|PAY|RECRUIT)\b[^\]]*\]/gi

export function stripDmTags(text, { trim = false } = {}) {
  if (!text) return ''
  let cleaned = text
    .replace(CONTROL_TAG_PATTERN, '')
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/ +\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
  return trim ? cleaned.trim() : cleaned
}
