import { Circle, MessageCircleHeart, Users } from 'lucide-react'

const ATTITUDES = {
  hostile: { label: 'Hostile', tone: 'var(--ember)', level: 1 },
  unfriendly: { label: 'Wary', tone: 'var(--ember)', level: 2 },
  neutral: { label: 'Neutral', tone: 'var(--ink-3)', level: 3 },
  friendly: { label: 'Friendly', tone: 'var(--sage)', level: 4 },
  trusted: { label: 'Trusts you', tone: 'var(--gold)', level: 5 },
}

function AttitudeMeter({ attitude }) {
  const a = ATTITUDES[attitude] || ATTITUDES.neutral
  return (
    <span className="inline-flex items-center gap-2" title={`Attitude: ${a.label}`}>
      <span className="flex gap-[3px]" aria-hidden>
        {[1, 2, 3, 4, 5].map((n) => (
          <span
            key={n}
            className="w-[7px] h-[7px] rounded-full"
            style={{ background: n <= a.level ? a.tone : 'var(--line-strong)' }}
          />
        ))}
      </span>
      <span className="font-ui text-xs" style={{ color: a.tone }}>{a.label}</span>
    </span>
  )
}

function Person({ person }) {
  return (
    <li className="py-3.5 first:pt-0">
      <div className="flex items-baseline justify-between gap-3">
        <h4 className="font-display text-[1.15rem] leading-tight text-[var(--ink)]">{person.name}</h4>
        {person.in_party ? (
          <span className="caps-muted shrink-0">Companion</span>
        ) : person.status ? (
          <span className="caps-muted shrink-0" style={person.status === 'Captive' ? { color: 'var(--ember)' } : undefined}>
            {person.status}
          </span>
        ) : null}
      </div>
      <div className="mt-1">
        <AttitudeMeter attitude={person.attitude} />
      </div>
      {person.memories?.length > 0 && (
        <div className="mt-2.5">
          <p className="flex items-center gap-1.5 caps-muted mb-1.5" style={{ color: 'var(--memory)' }}>
            <MessageCircleHeart size={12} aria-hidden /> Remembers
          </p>
          <ul className="space-y-1.5">
            {person.memories.slice(-4).reverse().map((m, i) => (
              <li key={i} className="font-read text-[0.92rem] leading-snug text-[var(--ink-2)] pl-3 border-l border-[var(--line-strong)]">
                {m}
              </li>
            ))}
          </ul>
        </div>
      )}
    </li>
  )
}

function Objectives({ quests }) {
  const active = (quests || []).filter((q) => !['COMPLETE', 'completed', 'FAILED', 'failed'].includes(q.status))
  if (!active.length) return null
  return (
    <section>
      <h3 className="caps mb-3">Objectives</h3>
      <ul className="space-y-3">
        {active.map((q) => {
          const next = (q.objectives || []).filter((o) => !o.hidden && !o.completed)
          return (
            <li key={q.id}>
              <p className="font-display text-[1.05rem] leading-tight text-[var(--ink)]">{q.name}</p>
              <ul className="mt-1 space-y-0.5">
                {next.slice(0, 2).map((o, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-[var(--ink-2)] font-ui">
                    <Circle size={9} className="mt-[0.4rem] shrink-0 text-[var(--gold)]" aria-hidden />
                    {o.description}
                  </li>
                ))}
              </ul>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

/** Who's here, how they feel about you, what they remember, and what's next. */
export default function ScenePanel({ people = [], quests = [] }) {
  const here = people.filter((p) => p.here)
  const elsewhere = people.filter((p) => !p.here)

  return (
    <div className="space-y-8">
      <section>
        <h3 className="caps mb-3">Here</h3>
        {here.length ? (
          <ul className="divide-y divide-[var(--line)]">
            {here.map((p) => <Person key={p.id} person={p} />)}
          </ul>
        ) : (
          <p className="flex items-center gap-2 text-sm text-[var(--ink-3)] font-read italic">
            <Users size={14} aria-hidden /> No one else is here.
          </p>
        )}
      </section>

      <Objectives quests={quests} />

      {elsewhere.length > 0 && (
        <section>
          <h3 className="caps mb-3">People you know</h3>
          <ul className="divide-y divide-[var(--line)]">
            {elsewhere.map((p) => <Person key={p.id} person={p} />)}
          </ul>
        </section>
      )}
    </div>
  )
}
