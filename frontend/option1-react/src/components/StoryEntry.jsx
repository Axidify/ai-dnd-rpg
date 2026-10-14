import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { renderMarkdown } from '../lib/markdown'

const TUMBLE_MS = 700

/** The die face: tumbles through random numbers, then lands on the natural roll. */
function useTumble(finalValue, animate) {
  const [face, setFace] = useState(animate ? 1 + Math.floor(Math.random() * 20) : finalValue)
  const [landed, setLanded] = useState(!animate)
  useEffect(() => {
    if (!animate) return undefined
    const tick = setInterval(() => setFace(1 + Math.floor(Math.random() * 20)), 60)
    const stop = setTimeout(() => {
      clearInterval(tick)
      setFace(finalValue)
      setLanded(true)
    }, TUMBLE_MS)
    return () => { clearInterval(tick); clearTimeout(stop) }
  }, [animate, finalValue])
  return [face, landed]
}

function RollCard({ roll, fresh }) {
  const reduce =
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  // Only a roll arriving live tumbles; history and reloads show the result
  const [animate] = useState(Boolean(fresh) && !reduce)
  const [face, landed] = useTumble(roll?.roll, animate)

  if (!roll || typeof roll !== 'object') return null

  const skill = (roll.skill || 'Check').replace(/_/g, ' ')
  const { success, is_nat_20: isNat20, is_nat_1: isNat1 } = roll
  const mod = roll.modifier ?? 0
  const modStr = mod >= 0 ? `+ ${mod}` : `− ${Math.abs(mod)}`

  let outcome = success ? 'Success' : 'Failure'
  if (isNat20) outcome = 'Natural 20'
  if (isNat1) outcome = 'Natural 1'
  const tone = isNat1 ? 'var(--ember)' : isNat20 ? 'var(--gold-bright)' : success ? 'var(--sage)' : 'var(--ember)'

  return (
    <div
      className="mb-5 panel-inset rounded-xl px-4 py-3.5 border border-[var(--line-strong)] flex items-center gap-4"
      role="status"
      aria-live="polite"
      aria-label={landed ? `${skill} check: rolled ${roll.roll} ${modStr}, total ${roll.total} against DC ${roll.dc}. ${outcome}.` : `Rolling ${skill}`}
    >
      <div
        className={`roll-die ${landed ? 'roll-die--landed' : 'roll-die--tumbling'}`}
        style={landed ? { borderColor: tone, color: tone } : undefined}
        aria-hidden
      >
        <span className="tabular-nums">{face}</span>
      </div>

      <div className="flex-1 min-w-0">
        <p className="caps-muted">
          {skill} <span className="text-[var(--ink-3)]">· DC {roll.dc}</span>
        </p>
        <p className="font-ui text-[var(--ink)] tabular-nums mt-0.5" aria-hidden>
          {landed ? (
            <>
              <span className="text-[var(--ink-3)]">{roll.roll} {modStr} =</span>{' '}
              <span className="text-xl font-semibold">{roll.total}</span>
              <span className="text-[var(--ink-3)]"> vs {roll.dc}</span>
            </>
          ) : (
            <span className="text-[var(--ink-3)]">Rolling…</span>
          )}
        </p>
      </div>

      <p
        className={`font-ui text-xs font-semibold uppercase tracking-wider shrink-0 transition-opacity duration-300 ${landed ? 'opacity-100' : 'opacity-0'}`}
        style={{ color: tone }}
        aria-hidden
      >
        {outcome}
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
      {hasRoll && <RollCard roll={message.rollResult} fresh={message.isStreaming} />}

      {awaitingNarration ? (
        <p className="font-read italic text-[var(--ink-2)] text-base" aria-live="polite">
          The Dungeon Master weighs the outcome
          <span className="caret" aria-hidden />
        </p>
      ) : prose ? (
        <div className="story-prose">
          {renderMarkdown(prose, { streaming: message.isStreaming, dropCap: isOpening })}
          {message.isStreaming && <span className="caret" aria-hidden />}
        </div>
      ) : message.isStreaming ? (
        <p className="font-read italic text-[var(--ink-2)]" aria-live="polite">
          <span className="caret" aria-hidden />
        </p>
      ) : null}
    </motion.div>
  )
}
