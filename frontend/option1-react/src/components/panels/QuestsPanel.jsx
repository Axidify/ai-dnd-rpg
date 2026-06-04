import { CheckCircle2, Circle, XCircle, Scroll } from 'lucide-react'

function isComplete(s) {
  return s === 'COMPLETE' || s === 'completed'
}
function isFailed(s) {
  return s === 'FAILED' || s === 'failed'
}

export default function QuestsPanel({ quests = [] }) {
  if (!quests.length) {
    return (
      <div className="text-center py-10 text-[var(--ink-3)]">
        <Scroll size={36} className="mx-auto mb-3 opacity-50" aria-hidden />
        <p className="font-read italic">No tales to pursue yet.</p>
        <p className="text-sm mt-1">Speak with those you meet to uncover quests.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {quests.map((quest, idx) => {
        const done = isComplete(quest.status)
        const failed = isFailed(quest.status)
        return (
          <div
            key={quest.id || idx}
            className={`panel-inset rounded-xl p-4 ${
              done ? 'border-[var(--sage)]/40' : failed ? 'border-[var(--ember)]/40' : ''
            }`}
          >
            <div className="flex items-start gap-3">
              <span className="mt-0.5 shrink-0">
                {done ? (
                  <CheckCircle2 size={18} className="text-[var(--sage)]" aria-hidden />
                ) : failed ? (
                  <XCircle size={18} className="text-[var(--ember)]" aria-hidden />
                ) : (
                  <Circle size={18} className="text-[var(--gold)]" aria-hidden />
                )}
              </span>
              <div className="flex-1 min-w-0">
                <h3 className="font-display text-lg text-[var(--ink)] leading-tight">{quest.name}</h3>
                {quest.description && (
                  <p className="text-sm text-[var(--ink-2)] mt-1 font-read leading-relaxed">{quest.description}</p>
                )}

                {Array.isArray(quest.objectives) && quest.objectives.length > 0 && (
                  <ul className="mt-3 space-y-1">
                    {quest.objectives.map((obj, i) => {
                      const cur = obj.current_count ?? obj.current
                      const req = obj.required_count ?? obj.required
                      return (
                        <li key={i} className="flex items-center gap-2 text-sm">
                          {obj.completed ? (
                            <CheckCircle2 size={13} className="text-[var(--sage)] shrink-0" aria-hidden />
                          ) : (
                            <Circle size={13} className="text-[var(--ink-3)] shrink-0" aria-hidden />
                          )}
                          <span className={obj.completed ? 'line-through text-[var(--ink-3)]' : 'text-[var(--ink-2)]'}>
                            {obj.description}
                            {cur !== undefined && req !== undefined && (
                              <span className="text-[var(--gold)] ml-1 tabular-nums">({cur}/{req})</span>
                            )}
                          </span>
                        </li>
                      )
                    })}
                  </ul>
                )}

                {quest.rewards && (
                  <div className="mt-3 flex flex-wrap gap-3 text-xs font-ui">
                    {quest.rewards.gold && <span className="text-[var(--gold)]">{quest.rewards.gold} gold</span>}
                    {quest.rewards.xp && <span className="text-[var(--ink-2)]">{quest.rewards.xp} xp</span>}
                    {Array.isArray(quest.rewards.items) && quest.rewards.items.length > 0 && (
                      <span className="text-[var(--ink-3)]">{quest.rewards.items.join(', ')}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
