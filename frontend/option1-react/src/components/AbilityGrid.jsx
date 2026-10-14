const ABILITIES = [
  ['strength', 'STR'],
  ['dexterity', 'DEX'],
  ['constitution', 'CON'],
  ['intelligence', 'INT'],
  ['wisdom', 'WIS'],
  ['charisma', 'CHA'],
]

export function formatModifier(mod) {
  if (mod === undefined || mod === null) return '—'
  return mod >= 0 ? `+${mod}` : `−${Math.abs(mod)}`
}

/** Six ability scores with their modifiers (modifier is the number that matters in play). */
export default function AbilityGrid({ character }) {
  if (!character) return null
  const mods = character.ability_modifiers || {}
  return (
    <dl className="grid grid-cols-3 gap-2">
      {ABILITIES.map(([key, short]) => {
        const score = character[key]
        const mod = mods[key] ?? (typeof score === 'number' ? Math.floor((score - 10) / 2) : undefined)
        return (
          <div key={key} className="panel-inset rounded-lg px-2 py-2 text-center">
            <dt className="caps-muted leading-none" title={key[0].toUpperCase() + key.slice(1)}>{short}</dt>
            <dd className="mt-1.5">
              <span className="block font-display text-xl leading-none text-[var(--ink)] tabular-nums">
                {formatModifier(mod)}
              </span>
              <span className="block text-[11px] text-[var(--ink-3)] tabular-nums mt-1">{score ?? '—'}</span>
            </dd>
          </div>
        )
      })}
    </dl>
  )
}
