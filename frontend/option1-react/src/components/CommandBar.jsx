import { forwardRef } from 'react'
import { ArrowRight, Eye, Footprints, MessageCircle, Sword, ShieldHalf, Wind } from 'lucide-react'

const SUGGESTIONS = [
  { label: 'Look around', action: 'I look carefully around me.', icon: Eye },
  { label: 'Press on', action: 'I continue onward.', icon: Footprints },
  { label: 'Speak', action: 'I speak up.', icon: MessageCircle },
]

const CommandBar = forwardRef(function CommandBar(
  {
    input,
    setInput,
    onSubmit,
    onSuggestion,
    isLoading,
    inCombat,
    combatStatus,
    onAttack,
    onDefend,
    onFlee,
  },
  ref
) {
  const enemies = combatStatus?.enemies || []

  return (
    <div className="relative z-20 shrink-0 border-t border-[var(--line)] bg-[var(--bg)]/85 backdrop-blur-md">
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
        ) : (
          !input.trim() && (
            <div className="flex flex-wrap gap-2 mb-3 justify-center">
              {SUGGESTIONS.map((s) => {
                const Icon = s.icon
                return (
                  <button
                    key={s.label}
                    type="button"
                    disabled={isLoading}
                    onClick={() => onSuggestion?.(s.action)}
                    className="focus-ring inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[var(--line-strong)] text-[var(--ink-2)] text-[0.8rem] font-ui hover:text-[var(--gold)] hover:border-[var(--gold)] hover:bg-[var(--gold-soft)] transition disabled:opacity-40"
                  >
                    <Icon size={13} aria-hidden />
                    {s.label}
                  </button>
                )
              })}
            </div>
          )
        )}

        <form onSubmit={onSubmit}>
          <div className="group flex items-end gap-3 border-b border-[var(--line-strong)] focus-within:border-[var(--gold)] transition-colors pb-2">
            <label htmlFor="player-action" className="sr-only">
              Describe your action
            </label>
            <input
              id="player-action"
              ref={ref}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={inCombat ? 'Or describe your move…' : 'What do you do?'}
              className="field flex-1 text-[1.05rem] py-1.5 font-read"
              disabled={isLoading}
              autoComplete="off"
              autoFocus
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              aria-label="Send"
              className="focus-ring shrink-0 mb-0.5 w-9 h-9 grid place-items-center rounded-full transition disabled:opacity-30 text-[var(--gold)] hover:bg-[var(--gold-soft)] enabled:hover:scale-105"
            >
              {isLoading ? (
                <span className="w-4 h-4 rounded-full border-2 border-[var(--ink-3)] border-t-[var(--gold)] animate-spin" />
              ) : (
                <ArrowRight size={20} />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
})

export default CommandBar
