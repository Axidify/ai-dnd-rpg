import { Heart, UserPlus, Users } from 'lucide-react'

export default function PartyPanel({ party = [], availableRecruits = [], isLoading, onRecruit }) {
  return (
    <div className="space-y-6">
      <section>
        <p className="caps mb-3">Your companions</p>
        {party.length ? (
          <div className="space-y-2.5">
            {party.map((m, i) => (
              <div key={i} className="panel-inset rounded-lg p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[var(--ink)] font-medium">{m.name}</span>
                  <span className="text-xs text-[var(--ink-3)]">{m.class || m.role}</span>
                </div>
                {m.hp !== undefined && (
                  <div className="mt-1.5 flex items-center gap-1.5 text-xs text-[var(--ember)]">
                    <Heart size={11} aria-hidden />
                    <span className="tabular-nums">{m.hp}/{m.max_hp || m.hp}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-[var(--ink-3)]">
            <Users size={30} className="mx-auto mb-2 opacity-50" aria-hidden />
            <p className="font-read italic">You travel alone.</p>
          </div>
        )}
      </section>

      <section>
        <p className="caps mb-3">Recruits</p>
        {availableRecruits.length ? (
          <div className="space-y-2.5">
            {availableRecruits.map((npc, i) => (
              <div key={i} className="panel-inset rounded-lg p-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-[var(--ink)] font-medium truncate">{npc.name}</div>
                  <p className="text-xs text-[var(--ink-2)] font-read">{npc.description || npc.class}</p>
                  {npc.requirement && (
                    <p className="text-[11px] text-[var(--gold)] mt-0.5">Requires: {npc.requirement}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => onRecruit?.(npc.name)}
                  disabled={isLoading || !npc.can_recruit}
                  className="focus-ring shrink-0 inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border border-[var(--line-strong)] text-[var(--ink-2)] hover:text-[var(--gold)] hover:border-[var(--gold)] transition disabled:opacity-40"
                >
                  <UserPlus size={13} aria-hidden /> Recruit
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--ink-3)] font-read italic">No one here will join you.</p>
        )}
      </section>
    </div>
  )
}
