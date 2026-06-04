import { motion } from 'framer-motion'

function RollCard({ roll }) {
  if (!roll || typeof roll !== 'object') return null

  const formatted = roll.formatted || null
  const skill = roll.skill || 'Check'
  const success = roll.success
  const isNat20 = roll.is_nat_20
  const isNat1 = roll.is_nat_1

  let outcomeLabel = success ? 'Success' : 'Failure'
  if (isNat20) outcomeLabel = 'Critical success'
  if (isNat1) outcomeLabel = 'Critical failure'

  const mod = roll.modifier ?? 0
  const modStr = mod >= 0 ? `+${mod}` : String(mod)

  return (
    <div
      className="mb-5 panel-inset rounded-xl px-4 py-3 border border-[var(--line-strong)]"
      role="status"
      aria-live="polite"
    >
      <p className="caps-muted mb-1.5">{skill}</p>
      {formatted ? (
        <p className="font-ui text-sm text-[var(--ink)] tabular-nums">{formatted}</p>
      ) : (
        <p className="font-ui text-sm text-[var(--ink)] tabular-nums">
          d20 {roll.roll} {modStr} = {roll.total}
          <span className="text-[var(--ink-3)]"> · DC {roll.dc}</span>
        </p>
      )}
      <p
        className="mt-1.5 text-xs font-ui font-medium uppercase tracking-wider"
        style={{ color: isNat1 ? 'var(--ember)' : isNat20 ? 'var(--gold-bright)' : success ? 'var(--sage)' : 'var(--ink-3)' }}
      >
        {outcomeLabel}
      </p>
    </div>
  )
}

export default function StoryEntry({ message, isOpening }) {
  const reduce =
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  if (message.type === 'player') {
    return (
      <motion.div
        initial={reduce ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="interlude"
      >
        <span className="interlude-rule" aria-hidden />
        <p className="interlude-text">{message.content}</p>
      </motion.div>
    )
  }

  const hasRoll = message.rollResult && typeof message.rollResult === 'object'
  const prose = (message.content || '').trim()
  const awaitingNarration = message.isStreaming && hasRoll && !prose

  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {hasRoll && <RollCard roll={message.rollResult} />}

      {awaitingNarration ? (
        <p className="font-read italic text-[var(--ink-2)] text-base" aria-live="polite">
          The Dungeon Master weighs the outcome
          <span className="caret" aria-hidden />
        </p>
      ) : prose ? (
        <p className={`story-prose ${isOpening ? 'story-prose--opening' : ''}`}>
          {message.content}
          {message.isStreaming && <span className="caret" aria-hidden />}
        </p>
      ) : message.isStreaming ? (
        <p className="font-read italic text-[var(--ink-2)]" aria-live="polite">
          <span className="caret" aria-hidden />
        </p>
      ) : null}
    </motion.div>
  )
}
