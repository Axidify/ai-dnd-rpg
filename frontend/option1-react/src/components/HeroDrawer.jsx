import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X, Coins, Sword, Shield, Sparkles, Moon, ArrowUpCircle, Save, FolderOpen, LogOut, Award,
} from 'lucide-react'
import { getClassIcon } from '../lib/classIcons'
import { getCharacterHp, getXpProgress } from '../lib/gameConstants'
import AbilityGrid, { formatModifier } from './AbilityGrid'

const titleCase = (s) => String(s || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

function Meter({ value, max, color, label, valueText }) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="caps-muted">{label}</span>
        <span className="text-xs text-[var(--ink-2)] tabular-nums font-ui">{valueText}</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--line-strong)] overflow-hidden">
        <div className="h-full rounded-full transition-[width] duration-500" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="panel-inset rounded-lg px-3 py-2.5 flex items-center gap-2.5">
      <Icon size={16} className="text-[var(--gold)] shrink-0" aria-hidden />
      <div className="min-w-0">
        <div className="caps-muted leading-none mb-1">{label}</div>
        <div className="text-sm text-[var(--ink)] truncate">{value}</div>
      </div>
    </div>
  )
}

function Action({ icon: Icon, label, onClick, accent }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`focus-ring w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border transition text-left text-sm font-ui ${
        accent
          ? 'border-[var(--gold)] text-[var(--gold)] bg-[var(--gold-soft)] hover:brightness-110'
          : 'border-[var(--line)] text-[var(--ink-2)] hover:text-[var(--ink)] hover:border-[var(--line-strong)] hover:bg-[var(--surface-2)]'
      }`}
    >
      <Icon size={16} aria-hidden />
      {label}
    </button>
  )
}

export default function HeroDrawer({
  open, onClose, character, canLevelUp,
  onRest, onLevelUp, onSave, onLoad, onLeave,
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose?.()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  const ClassIcon = getClassIcon(character?.char_class || character?.class)
  const hp = getCharacterHp(character)
  const xp = getXpProgress(character)
  const ac = character?.armor_class ?? character?.ac ?? '—'
  const atk = character?.attack_bonus !== undefined
    ? `${formatModifier(character.attack_bonus)}${character.weapon_damage ? ` · ${character.weapon_damage}` : ''}`
    : '—'
  const nextXp = character?.next_level_xp ?? xp.nextThreshold
  const xpText = xp.level >= 5 ? `${xp.currentXP} xp · Max level` : `${xp.currentXP} / ${nextXp} xp`

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex justify-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
        >
          <div className="absolute inset-0 bg-black/70 backdrop-blur-[3px]" onClick={onClose} aria-hidden />
          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label="Character sheet"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="relative w-full max-w-[22rem] h-full bg-[var(--surface)] border-l border-[var(--line)] shadow-paper-lg flex flex-col"
          >
            <div className="shrink-0 px-5 pt-5 pb-4 border-b border-[var(--line)]">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="w-12 h-12 rounded-full grid place-items-center bg-[var(--surface-2)] border border-[var(--line-strong)] text-[var(--gold)] shrink-0">
                    <ClassIcon size={22} aria-hidden />
                  </span>
                  <div className="min-w-0">
                    <h2 className="display text-2xl truncate">{character?.name || 'Adventurer'}</h2>
                    <p className="text-xs text-[var(--ink-3)] font-ui">
                      Level {character?.level || 1} · {character?.race || ''} {character?.char_class || character?.class || ''}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  aria-label="Close"
                  className="focus-ring w-9 h-9 rounded-full grid place-items-center text-[var(--ink-3)] hover:text-[var(--gold)] hover:bg-[var(--gold-soft)] transition shrink-0"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
              <div className="space-y-3.5">
                <Meter label="Vitality" value={hp.current} max={hp.max} valueText={`${hp.current} / ${hp.max}`} color="var(--ember)" />
                <Meter label="Experience" value={xp.progress} max={100} valueText={xpText} color="var(--gold)" />
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <Stat icon={Shield} label="Armor" value={ac} />
                <Stat icon={Sword} label="Attack" value={atk} />
                <Stat icon={Award} label="Proficiency" value={formatModifier(character?.proficiency_bonus ?? 2)} />
                <Stat icon={Coins} label="Gold" value={character?.gold ?? 0} />
              </div>

              <div>
                <p className="caps-muted mb-2">Abilities</p>
                <AbilityGrid character={character} />
              </div>

              {(character?.weapon || character?.equipped_armor) && (
                <div>
                  <p className="caps-muted mb-2">Equipped</p>
                  <div className="space-y-2">
                    {character?.weapon && (
                      <div className="panel-inset rounded-lg px-3 py-2 flex items-center gap-2.5 text-sm">
                        <Sword size={15} className="text-[var(--gold)]" aria-hidden />
                        <span className="text-[var(--ink)]">{titleCase(character.weapon)}</span>
                      </div>
                    )}
                    {character?.equipped_armor && (
                      <div className="panel-inset rounded-lg px-3 py-2 flex items-center gap-2.5 text-sm">
                        <Shield size={15} className="text-[var(--gold)]" aria-hidden />
                        <span className="text-[var(--ink)]">{titleCase(character.equipped_armor)}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {Array.isArray(character?.abilities) && character.abilities.length > 0 && (
                <div>
                  <p className="caps-muted mb-2">Abilities</p>
                  <div className="flex flex-wrap gap-1.5">
                    {character.abilities.map((a, i) => (
                      <span key={i} className="inline-flex items-center gap-1 text-xs font-ui text-[var(--ink-2)] panel-inset rounded-full px-2.5 py-1">
                        <Sparkles size={11} className="text-[var(--gold)]" aria-hidden />
                        {typeof a === 'string' ? a : a.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="shrink-0 px-5 py-4 border-t border-[var(--line)] space-y-2">
              {canLevelUp && (
                <Action icon={ArrowUpCircle} label="Level up" onClick={onLevelUp} accent />
              )}
              <div className="grid grid-cols-2 gap-2">
                <Action icon={Moon} label="Rest" onClick={onRest} />
                <Action icon={Save} label="Save" onClick={onSave} />
                <Action icon={FolderOpen} label="Load" onClick={onLoad} />
                <Action icon={LogOut} label="Leave" onClick={onLeave} />
              </div>
            </div>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
