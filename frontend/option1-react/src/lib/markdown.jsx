/**
 * Minimal Markdown renderer for DM narration.
 *
 * Builds React elements directly (never innerHTML), so model output can't
 * inject markup. Supports what the DM and server actually emit:
 *   paragraphs, single line breaks, # headings, --- rules,
 *   "- " / "* " / "1. " lists, **bold**, *italic* / _italic_.
 *
 * While a message is still streaming, a trailing unclosed ** or * is hidden
 * rather than flashing as a literal asterisk until its partner arrives.
 */

const INLINE = /(\*\*([^*\n]+?)\*\*|__([^_\n]+?)__|\*([^*\n]+?)\*|(?<![\w])_([^_\n]+?)_(?![\w]))/g

function renderInline(text, keyPrefix) {
  const out = []
  let last = 0
  let i = 0
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) out.push(text.slice(last, m.index))
    const key = `${keyPrefix}-${i++}`
    const strong = m[2] ?? m[3]
    if (strong !== undefined) {
      out.push(<strong key={key}>{renderInline(strong, key)}</strong>)
    } else {
      out.push(<em key={key}>{m[4] ?? m[5]}</em>)
    }
    last = m.index + m[0].length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

function withBreaks(lines, keyPrefix) {
  return lines.flatMap((line, i) => {
    const parts = renderInline(line, `${keyPrefix}-${i}`)
    return i === 0 ? parts : [<br key={`${keyPrefix}-br-${i}`} />, ...parts]
  })
}

/** Hide a dangling opening marker at the very end of a streaming message. */
function trimUnclosedTail(text) {
  const start = text.lastIndexOf('\n') + 1
  let tail = text.slice(start)
  // Check ** first, then lone * (a * that isn't part of **)
  for (const [marker, re] of [['**', /\*\*/g], ['*', /(?<!\*)\*(?!\*)/g]]) {
    const hits = [...tail.matchAll(re)]
    if (hits.length % 2) {
      const at = hits[hits.length - 1].index
      tail = tail.slice(0, at) + tail.slice(at + marker.length)
    }
  }
  return text.slice(0, start) + tail
}

const HR = /^\s*([-*_])(\s*\1){2,}\s*$/
const HEADING = /^\s*(#{1,4})\s+(.*)$/
const BULLET = /^\s*[-*•]\s+(.*)$/
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/

/**
 * Render ``text`` as an array of block elements.
 * ``dropCap``: add the "dropcap" class to the first paragraph that starts
 * with a letter (so an opening emoji or heading never gets the drop cap).
 */
export function renderMarkdown(text, { streaming = false, dropCap = false } = {}) {
  if (!text) return []
  const source = streaming ? trimUnclosedTail(text) : text
  const blocks = source.replace(/\r\n/g, '\n').split(/\n{2,}/)
  const out = []
  let dropCapUsed = !dropCap

  blocks.forEach((block, b) => {
    const lines = block.split('\n').filter((l, i, arr) => l.trim() || (i > 0 && i < arr.length - 1))
    if (!lines.length) return
    const key = `b${b}`

    if (lines.length === 1 && HR.test(lines[0])) {
      out.push(<hr key={key} className="story-rule" />)
      return
    }

    const heading = lines.length === 1 && lines[0].match(HEADING)
    if (heading) {
      out.push(<p key={key} className="story-heading">{renderInline(heading[2], key)}</p>)
      return
    }

    // A block where every line is a list item
    if (lines.every((l) => BULLET.test(l)) || lines.every((l) => NUMBERED.test(l))) {
      const ordered = NUMBERED.test(lines[0])
      const items = lines.map((l, i) => (
        <li key={`${key}-${i}`}>{renderInline(l.match(ordered ? NUMBERED : BULLET)[1], `${key}-${i}`)}</li>
      ))
      out.push(ordered ? <ol key={key}>{items}</ol> : <ul key={key}>{items}</ul>)
      return
    }

    let className
    if (!dropCapUsed && /^[\s*_"'“‘(]*[A-Za-z]/.test(lines[0])) {
      className = 'dropcap'
      dropCapUsed = true
    }
    out.push(<p key={key} className={className}>{withBreaks(lines, key)}</p>)
  })
  return out
}
