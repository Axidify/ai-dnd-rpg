import { forwardRef, useLayoutEffect, useRef } from 'react'
import { ArrowRight, Eye, Footprints, Sword, ShieldHalf, Wind } from 'lucide-react'

const MODES = [
  { id: 'do', label: 'Do', placeholder: 'What do you do?' },
  { id: 'say', label: 'Say', placeholder: 'What do you say?' },
]

const SUGGESTIONS = [
  { label: 'Look around', action: 'I look carefully around me.', icon: Eye },
  { label: 'Press on', action: 'I continue onward.', icon: Footprints },
]

const CommandBar = forwardRef(function CommandBar(
  {
    input,
    setInput,
    mode = 'do',
    setMode,
    onSubmit,
    onSuggestion,
    isLoading,
    inCombat,
    gameOver,
    combatStatus,
    onAttack,
    onDefend,
    onFlee,
  },
  ref
) {
  const enemies = combatStatus?.enemies || []
  const localRef = useRef(null)
  const setRefs = (el) => {
    localRef.current = el
    if (typeof ref === 'function') ref(el)
    else if (ref) ref.current = el
  }
  const current = MODES.find((m) => m.id === mode) || MODES[0]

  // Grow with the text, up to about six lines
  useLayoutEffect(() => {
    const el = localRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 168)}px`
  }, [input])

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      onSubmit?.(e)
    }
  }

  return (
    <div className="relative z-20 shrink-0 border-t border-[var(--line)] bg-[color-mix(in_srgb,var(--bg)_85%,transparent)] backdrop-blur-md">
      <div className="max-w-[42rem] mx-auto px-4 py-3 md:py-4">
        {inCombat ? (
          <div className="mb-3">
            {enemies.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3 justify-center">
                {enemies.map((e, i) => {
                  const cur = e.hp ?? e.current_hp ?? 0
                  const max = e.max_hp ?? e.hp ?? 1
                  const pct = max > 0 ? Math.max(0, (cur / max) * 100) : 0
                  return (
                    <div
                      key={i}
                      className="panel-inset px-3 py-1.5 rounded-lg min-w-[7rem]"
                    >
                      <div className="flex items-center justify-between gap-3 text-xs">
                        <span className="text-[var(--ink)] truncate">{e.name || `Enemy ${i + 1}`}</span>
                        <span className="text-[var(--ink-3)] tabular-nums">{cur}/{max}</span>
                      </div>
                      <div className="mt-1 h-1 rounded-full bg-[var(--line-strong)] overflow-hidden">
                        <div className="h-full bg-[var(--ember)]" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
            <div className="flex gap-2 justify-center">
              <button type="button" onClick={() => onAttack?.()} disabled={isLoading} className="btn btn-ghost focus-ring flex items-center gap-2 px-4 py-2 text-sm" style={{ borderColor: 'rgba(199,107,74,0.5)', color: 'var(--ember)' }}>
                <Sword size={16} aria-hidden /> Attack
              </button>
              <button type="button" onClick={() => onDefend?.()} disabled={isLoading} className="btn btn-ghost focus-ring flex items-center gap-2 px-4 py-2 text-sm">
                <ShieldHalf size={16} aria-hidden /> Defend
              </button>
              <button type="button" onClick={() => onFlee?.()} disabled={isLoading} className="btn btn-ghost focus-ring flex items-center gap-2 px-4 py-2 text-sm">
                <Wind size={16} aria-hidden /> Flee
              </button>
            </div>
          </div>
        ) : gameOver ? (
          <p className="text-center text-sm text-[var(--ink-3)] font-ui mb-3">
            Your adventure has ended.
          </p>
        ) : null}

        {!inCombat && !gameOver && (
        <form onSubmit={onSubmit}>
          <div className="flex items-center justify-between mb-2">
            <div className="mode-switch" role="group" aria-label="Action type">
              {MODES.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  aria-pressed={mode === m.id}
                  onClick={() => { setMode?.(m.id); localRef.current?.focus() }}
                  className="focus-ring"
                >
                  {m.label}
                </button>
              ))}
            </div>
            {input.trim() ? (
              <span className="hidden sm:inline font-ui text-[0.7rem] text-[var(--ink-3)]">
                Enter to send · Shift+Enter for a new line
              </span>
            ) : (
              <div className="flex gap-1.5">
                {SUGGESTIONS.map((sug) => {
                  const Icon = sug.icon
                  return (
                    <button
                      key={sug.label}
                      type="button"
                      disabled={isLoading}
                      onClick={() => onSuggestion?.(sug.action)}
                      className="focus-ring inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[var(--ink-3)] text-[0.78rem] font-ui hover:text-[var(--gold)] hover:bg-[var(--gold-soft)] transition disabled:opacity-40"
                    >
                      <Icon size={13} aria-hidden />
                      {sug.label}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
          <div className="group flex items-end gap-3 rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] focus-within:border-[var(--gold)] transition-colors pl-4 pr-1.5 py-1.5">
            <label htmlFor="player-action" className="sr-only">
              {current.placeholder}
            </label>
            <textarea
              id="player-action"
              ref={setRefs}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={current.placeholder}
              className="field flex-1 resize-none text-[1.05rem] leading-relaxed py-1.5 font-read"
              disabled={isLoading}
              autoComplete="off"
              autoFocus
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              aria-label="Send"
              className="focus-ring shrink-0 w-9 h-9 grid place-items-center rounded-lg transition disabled:opacity-30 text-[var(--on-gold)] bg-[var(--gold)] enabled:hover:bg-[var(--gold-bright)]"
            >
              {isLoading ? (
                <span className="w-4 h-4 rounded-full border-2 border-[color-mix(in_srgb,var(--on-gold)_40%,transparent)] border-t-[var(--on-gold)] animate-spin" />
              ) : (
                <ArrowRight size={18} />
              )}
            </button>
          </div>
        </form>
        )}
      </div>
    </div>
  )
})

export default CommandBar
