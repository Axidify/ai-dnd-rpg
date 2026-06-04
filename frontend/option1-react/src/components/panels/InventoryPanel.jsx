import { Coins, Package, Sword, Shield, FlaskConical, Scroll, CheckCircle2 } from 'lucide-react'

const TYPE_ICONS = {
  weapon: Sword,
  armor: Shield,
  consumable: FlaskConical,
  quest: Scroll,
  misc: Package,
}

export default function InventoryPanel({ character, isLoading, onUse, onEquip }) {
  const items = character?.inventory || []
  const equippedNames = [character?.weapon, character?.equipped_armor]
    .filter(Boolean)
    .map((n) => n.toLowerCase())

  return (
    <div>
      <div className="flex items-center justify-center gap-2 mb-5 text-[var(--gold)]">
        <Coins size={16} aria-hidden />
        <span className="font-display text-xl">{character?.gold ?? 0}</span>
        <span className="caps-muted">gold</span>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-10 text-[var(--ink-3)]">
          <Package size={36} className="mx-auto mb-3 opacity-50" aria-hidden />
          <p className="font-read italic">Your pack is empty.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {items.map((item, i) => {
            const Icon = TYPE_ICONS[item.item_type] || Package
            const isEquipped = equippedNames.includes(item.name?.toLowerCase())
            const canUse = item.item_type === 'consumable' || item.heal_amount
            const canEquip =
              item.item_type === 'weapon' || item.item_type === 'armor' || item.damage_dice || item.ac_bonus
            return (
              <div
                key={i}
                className={`panel-inset rounded-lg p-3 ${isEquipped ? 'ring-1 ring-[var(--gold)]/40 border-[var(--gold)]/40' : ''}`}
              >
                <div className="flex items-start gap-3">
                  <span className="w-9 h-9 rounded-lg grid place-items-center bg-[var(--surface-2)] border border-[var(--line)] text-[var(--gold)] shrink-0">
                    <Icon size={16} aria-hidden />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[var(--ink)] font-medium truncate">{item.name}</span>
                      {item.quantity > 1 && (
                        <span className="text-[10px] text-[var(--ink-3)] tabular-nums">×{item.quantity}</span>
                      )}
                      {isEquipped && (
                        <span className="inline-flex items-center gap-0.5 text-[10px] text-[var(--gold)]">
                          <CheckCircle2 size={11} aria-hidden /> worn
                        </span>
                      )}
                    </div>
                    {item.description && (
                      <p className="text-xs text-[var(--ink-2)] mt-0.5 font-read leading-snug">{item.description}</p>
                    )}
                    <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[11px] text-[var(--ink-3)] font-ui">
                      {item.damage_dice && <span>{item.damage_dice} dmg</span>}
                      {item.ac_bonus && <span>+{item.ac_bonus} AC</span>}
                      {item.heal_amount && <span>{item.heal_amount} heal</span>}
                      {item.value > 0 && <span className="text-[var(--gold)]">{item.value}g</span>}
                    </div>
                    {(canUse || canEquip) && (
                      <div className="flex gap-2 mt-2">
                        {canUse && (
                          <button
                            type="button"
                            onClick={() => onUse?.(item.name)}
                            disabled={isLoading}
                            className="focus-ring text-xs px-2.5 py-1 rounded-md border border-[var(--sage)]/50 text-[var(--sage)] hover:bg-[var(--sage)]/10 transition disabled:opacity-50"
                          >
                            Use
                          </button>
                        )}
                        {canEquip && (
                          <button
                            type="button"
                            onClick={() => onEquip?.(item.name)}
                            disabled={isLoading}
                            className="focus-ring text-xs px-2.5 py-1 rounded-md border border-[var(--line-strong)] text-[var(--ink-2)] hover:text-[var(--gold)] hover:border-[var(--gold)] transition disabled:opacity-50"
                          >
                            Equip
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
