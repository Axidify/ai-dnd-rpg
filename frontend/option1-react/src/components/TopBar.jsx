import { Backpack, Map, Scroll, Menu, Heart, MessageCircleHeart, Type } from 'lucide-react'
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
        <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 rounded-full bg-[var(--gold)] text-[var(--on-gold)] text-[10px] font-semibold leading-4 text-center">
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
  onOpenPeople,
  onOpenReading,
  peopleHere = 0,
  onOpenMenu,
}) {
  const ClassIcon = getClassIcon(character?.char_class || character?.class)
  const hp = getCharacterHp(character)
  const locationName =
    typeof currentLocation === 'object' ? currentLocation?.name : currentLocation

  return (
    <header className="relative z-20 shrink-0 h-14 px-2 sm:px-4 flex items-center justify-between gap-2 border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--bg)_80%,transparent)] backdrop-blur-md">
      {/* Hero */}
      <button
        type="button"
        onClick={onOpenHero}
        className="focus-ring flex items-center gap-2.5 pl-1 pr-2 py-1 rounded-xl hover:bg-[var(--gold-soft)] transition min-w-0 shrink-0"
        aria-label="Open character sheet"
      >
        <span className="relative w-9 h-9 rounded-full grid place-items-center bg-[var(--surface-2)] border border-[var(--line-strong)] text-[var(--gold)] shrink-0">
          <ClassIcon size={17} aria-hidden />
        </span>
        <span className="flex flex-col items-start min-w-0 leading-tight">
          {/* Name only where there's room; HP and level always show (HP 0 ends the run) */}
          <span className="hidden sm:block font-ui text-sm text-[var(--ink)] truncate max-w-[10rem]">
            {character?.name || 'Adventurer'}
          </span>
          <span
            className={`flex items-center gap-1 text-xs sm:text-[0.7rem] ${hp.pct <= 25 ? 'text-[var(--ember)]' : 'text-[var(--ink-2)] sm:text-[var(--ink-3)]'}`}
            aria-label={`${hp.current} of ${hp.max} hit points, level ${character?.level || 1}`}
          >
            <Heart size={11} className="text-[var(--ember)]" aria-hidden />
            <span className="tabular-nums font-ui">{hp.current}/{hp.max}</span>
            <span className="opacity-50">·</span>
            <span className="font-ui">Lv {character?.level || 1}</span>
          </span>
        </span>
      </button>

      {/* Location */}
      {/* Phones: fills the space between hero and menu; wider: centred on the bar */}
      <div className="flex-1 min-w-0 sm:flex-none sm:absolute sm:left-1/2 sm:-translate-x-1/2 px-2 sm:max-w-[40%] text-center pointer-events-none">
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
          {/* The scene rail shows people on wide screens */}
          <span className="xl:hidden">
            <IconButton label="People & objectives" onClick={onOpenPeople} badge={peopleHere}>
              <MessageCircleHeart size={18} aria-hidden />
            </IconButton>
          </span>
          <IconButton label="Quest journal" onClick={onOpenQuests} badge={questCount}>
            <Scroll size={18} aria-hidden />
          </IconButton>
          <IconButton label="World map" onClick={onOpenMap}>
            <Map size={18} aria-hidden />
          </IconButton>
          <IconButton label="Inventory" onClick={onOpenInventory}>
            <Backpack size={18} aria-hidden />
          </IconButton>
          <IconButton label="Reading settings" onClick={onOpenReading}>
            <Type size={18} aria-hidden />
          </IconButton>
        </div>
        <IconButton label="Menu" onClick={onOpenMenu}>
          <Menu size={18} aria-hidden />
        </IconButton>
      </div>
    </header>
  )
}
