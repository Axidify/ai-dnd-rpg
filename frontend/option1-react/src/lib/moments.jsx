import {
  AlertTriangle, Coins, Eye, HeartHandshake, MessageCircleHeart, Package, ScrollText,
  ShoppingBag, Sparkles, Swords, Trophy, UserPlus,
} from 'lucide-react'

/**
 * Game events arrive from the server as their own paragraphs, each starting
 * with an emoji ("💰 Received 10 gold (Total: 33)"). The story shows them as
 * moments: small chips under the narration, so prose stays prose.
 */
const MOMENTS = [
  { marker: '💰', kind: 'gold', icon: Coins, tone: 'var(--gold)' },
  { marker: '📦', kind: 'item', icon: Package, tone: 'var(--gold)' },
  { marker: '⭐', kind: 'xp', icon: Sparkles, tone: 'var(--gold-bright)' },
  { marker: '🛒', kind: 'buy', icon: ShoppingBag, tone: 'var(--ink-2)' },
  { marker: '💸', kind: 'pay', icon: Coins, tone: 'var(--ink-2)' },
  { marker: '🔍', kind: 'discovery', icon: Eye, tone: 'var(--sage)' },
  { marker: '📜', kind: 'quest', icon: ScrollText, tone: 'var(--sage)' },
  { marker: '🏆', kind: 'quest-done', icon: Trophy, tone: 'var(--gold-bright)' },
  { marker: '🎉', kind: 'joined', icon: UserPlus, tone: 'var(--sage)' },
  { marker: '💭', kind: 'memory', icon: MessageCircleHeart, tone: 'var(--memory)' },
  { marker: '⚔️', kind: 'combat', icon: Swords, tone: 'var(--ember)' },
  { marker: '⚔', kind: 'combat', icon: Swords, tone: 'var(--ember)' },
  { marker: '⚠️', kind: 'warning', icon: AlertTriangle, tone: 'var(--ember)' },
]

const ATTITUDE_ICON = HeartHandshake

function matchMoment(paragraph) {
  const text = paragraph.trim()
  return MOMENTS.find((m) => text.startsWith(m.marker))
}

const VARIATION_SELECTOR = new RegExp('^' + String.fromCharCode(0xfe0f))

/** A moment's text without its emoji (and the celebratory one after LEVEL UP). */
function momentText(paragraph, marker) {
  return paragraph
    .trim()
    .slice(marker.length)
    .replace(VARIATION_SELECTOR, '')
    .replace(/🎉/g, '')
    .trim()
}

/**
 * Split narration into prose and moments. Moments are pulled from anywhere
 * in the text (the server appends them after the narration).
 */
export function splitMoments(content) {
  const prose = []
  const moments = []
  for (const paragraph of (content || '').split(/\n{2,}/)) {
    const m = matchMoment(paragraph)
    if (m) {
      moments.push({ ...m, text: momentText(paragraph, m.marker) })
    } else {
      prose.push(paragraph)
    }
  }
  return { prose: prose.join('\n\n').trim(), moments }
}

/** **bold** inside a moment */
function inline(text) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part
  )
}

export function Moment({ moment }) {
  const isAttitude = moment.kind === 'memory' && /warms|cools/.test(moment.text)
  const Icon = isAttitude ? ATTITUDE_ICON : moment.icon
  return (
    <span className="moment" style={{ '--tone': moment.tone }} data-kind={moment.kind}>
      <Icon size={15} aria-hidden />
      <span>{inline(moment.text)}</span>
    </span>
  )
}

export function MomentList({ moments }) {
  if (!moments?.length) return null
  return (
    <ul className="mt-5 flex flex-col items-start gap-2" aria-label="What changed">
      {moments.map((m, i) => (
        <li key={i}>
          <Moment moment={m} />
        </li>
      ))}
    </ul>
  )
}
