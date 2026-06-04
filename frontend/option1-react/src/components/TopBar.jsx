import { Backpack, Map, Scroll, Menu, Heart } from 'lucide-react'
import { getClassIcon } from '../lib/classIcons'
import { getCharacterHp } from '../lib/gameConstants'

function IconButton({ label, onClick, badge, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="focus-ring relative w-10 h-10 grid place-items-center rounded-lg text-[var(--ink-2)] hover:text-[var(--gold)] hover:bg-[var(--gold-soft)] transition"
    >
      {children}
      {badge > 0 && (
        <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 rounded-full bg-[var(--gold)] text-[#1a1408] text-[10px] font-semibold leading-4 text-center">
          {badge}
        </span>
      )}
    </button>
  )
}

export default function TopBar({
  character,
  currentLocation,
  inCombat,
  questCount = 0,
  onOpenHero,
  onOpenInventory,
  onOpenMap,
  onOpenQuests,
  onOpenMenu,
}) {
  const ClassIcon = getClassIcon(character?.class)
  const hp = getCharacterHp(character)
  const locationName =
    typeof currentLocation === 'object' ? currentLocation?.name : currentLocation

  return (
    <header className="relative z-20 shrink-0 h-14 px-2 sm:px-4 flex items-center justify-between gap-2 border-b border-[var(--line)] bg-[var(--bg)]/80 backdrop-blur-md">
      {/* Hero */}
      <button
        type="button"
        onClick={onOpenHero}
        className="focus-ring flex items-center gap-2.5 pl-1 pr-2 py-1 rounded-xl hover:bg-[var(--gold-soft)] transition min-w-0"
        aria-label="Open character sheet"
      >
        <span className="relative w-9 h-9 rounded-full grid place-items-center bg-[var(--surface-2)] border border-[var(--line-strong)] text-[var(--gold)] shrink-0">
          <ClassIcon size={17} aria-hidden />
        </span>
        <span className="hidden sm:flex flex-col items-start min-w-0 leading-tight">
          <span className="font-ui text-sm text-[var(--ink)] truncate max-w-[10rem]">
            {character?.name || 'Adventurer'}
          </span>
          <span className="flex items-center gap-1 text-[var(--ink-3)] text-[0.7rem]">
            <Heart size={10} className="text-[var(--ember)]" aria-hidden />
            <span className="tabular-nums">{hp.current}/{hp.max}</span>
            <span className="opacity-50">·</span>
            <span>Lv {character?.level || 1}</span>
          </span>
        </span>
      </button>

      {/* Location */}
      <div className="absolute left-1/2 -translate-x-1/2 px-2 max-w-[40%] text-center pointer-events-none">
        {inCombat ? (
          <span className="caps" style={{ color: 'var(--ember)' }}>
            In battle
          </span>
        ) : (
          <span className="font-display text-base sm:text-lg tracking-[0.04em] text-[var(--ink-2)] truncate block">
            {locationName || 'The Unknown'}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-0.5">
        <div className="hidden sm:flex items-center gap-0.5">
          <IconButton label="Quest journal" onClick={onOpenQuests} badge={questCount}>
            <Scroll size={18} aria-hidden />
          </IconButton>
          <IconButton label="World map" onClick={onOpenMap}>
            <Map size={18} aria-hidden />
          </IconButton>
          <IconButton label="Inventory" onClick={onOpenInventory}>
            <Backpack size={18} aria-hidden />
          </IconButton>
        </div>
        <IconButton label="Menu" onClick={onOpenMenu}>
          <Menu size={18} aria-hidden />
        </IconButton>
      </div>
    </header>
  )
}
