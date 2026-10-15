import { THEMES, TEXT_SIZES, useReadingPrefs } from '../../lib/readingPrefs'

function Choice({ selected, onClick, children, className = '' }) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={`focus-ring rounded-xl border transition font-ui ${
        selected
          ? 'border-[var(--gold)] bg-[var(--gold-soft)] text-[var(--ink)]'
          : 'border-[var(--line)] text-[var(--ink-2)] hover:border-[var(--line-strong)] hover:bg-[var(--surface-2)]'
      } ${className}`}
    >
      {children}
    </button>
  )
}

export default function ReadingPanel() {
  const [prefs, update] = useReadingPrefs()

  return (
    <div className="space-y-6">
      <section>
        <h3 className="caps-muted mb-2.5">Theme</h3>
        <div className="grid grid-cols-2 gap-2.5">
          {THEMES.map((t) => (
            <Choice
              key={t.id}
              selected={prefs.theme === t.id}
              onClick={() => update({ theme: t.id })}
              className="px-3 py-3 text-left"
            >
              <span className="block text-sm">{t.label}</span>
              <span className="block text-xs text-[var(--ink-3)] mt-0.5">{t.hint}</span>
            </Choice>
          ))}
        </div>
      </section>

      <section>
        <h3 className="caps-muted mb-2.5">Text size</h3>
        <div className="grid grid-cols-4 gap-2">
          {TEXT_SIZES.map((s, i) => (
            <Choice
              key={s.id}
              selected={prefs.textSize === s.id}
              onClick={() => update({ textSize: s.id })}
              className="py-2.5"
            >
              <span className="font-read" style={{ fontSize: `${0.85 + i * 0.15}rem` }} aria-label={`Text size ${s.label}`}>
                Aa
              </span>
            </Choice>
          ))}
        </div>
      </section>

      <p className="story-prose text-[var(--ink-2)] border-l-2 border-[var(--line-strong)] pl-4">
        The lamplight gutters as Bram leans closer. &ldquo;You came back,&rdquo; he says.
      </p>
    </div>
  )
}
