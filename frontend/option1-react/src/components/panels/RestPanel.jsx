import { Sun, Moon } from 'lucide-react'

function RestOption({ icon: Icon, title, desc, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="focus-ring w-full panel-inset rounded-xl p-4 flex items-center gap-4 text-left hover:border-[color-mix(in_srgb,var(--gold)_40%,transparent)] hover:bg-[var(--surface-2)] transition disabled:opacity-50"
    >
      <span className="w-11 h-11 rounded-full grid place-items-center bg-[var(--surface-2)] border border-[var(--line-strong)] text-[var(--gold)] shrink-0">
        <Icon size={20} aria-hidden />
      </span>
      <div>
        <div className="font-display text-lg text-[var(--ink)] leading-tight">{title}</div>
        <div className="text-sm text-[var(--ink-2)] font-read">{desc}</div>
      </div>
    </button>
  )
}

export default function RestPanel({ isLoading, onShortRest, onLongRest }) {
  return (
    <div className="space-y-3">
      <RestOption icon={Sun} title="Short rest" desc="Catch your breath and recover some vitality." onClick={onShortRest} disabled={isLoading} />
      <RestOption icon={Moon} title="Long rest" desc="Make camp until dawn and fully restore." onClick={onLongRest} disabled={isLoading} />
    </div>
  )
}
