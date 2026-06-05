import { FolderOpen } from 'lucide-react'

export function SavePanel({ character, error, onSaveSlot }) {
  return (
    <div>
      {error && (
        <p role="alert" className="mb-3 text-sm font-ui" style={{ color: 'var(--ember)' }}>
          {error}
        </p>
      )}
      <div className="space-y-2.5">
        {[1, 2, 3].map((slot) => (
          <button
            key={slot}
            type="button"
            onClick={() => onSaveSlot?.(slot)}
            className="focus-ring w-full panel-inset rounded-lg p-4 text-left hover:border-[var(--gold)]/40 hover:bg-[var(--surface-2)] transition"
          >
            <div className="font-display text-lg text-[var(--ink)] leading-tight">Slot {slot}</div>
            <div className="text-sm text-[var(--ink-3)] font-ui">
              Inscribe {character?.name || 'your hero'}'s tale here
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export function LoadPanel({ saves = [], onLoad }) {
  if (!saves.length) {
    return (
      <div className="text-center py-10 text-[var(--ink-3)]">
        <FolderOpen size={36} className="mx-auto mb-3 opacity-50" aria-hidden />
        <p className="font-read italic">No journeys have been recorded.</p>
      </div>
    )
  }
  return (
    <div className="space-y-2.5">
      {saves.map((save, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onLoad?.(save.filepath || save.name)}
          className="focus-ring w-full panel-inset rounded-lg p-4 text-left hover:border-[var(--gold)]/40 hover:bg-[var(--surface-2)] transition"
        >
          <div className="font-display text-lg text-[var(--gold)] leading-tight">
            {save.character_name || 'Unknown hero'}
          </div>
          <div className="text-sm text-[var(--ink-2)] font-ui">
            Level {save.character_level || 1} · {save.character_class || 'Adventurer'}
          </div>
          {save.description && (
            <div className="text-xs text-[var(--ink-3)] mt-1 font-read italic truncate">{save.description}</div>
          )}
        </button>
      ))}
    </div>
  )
}
