import {
  Backpack, Scroll, Map, ShoppingBag, Users, Moon, ArrowUpCircle, Save, FolderOpen, User, LogOut,
} from 'lucide-react'

function Item({ icon: Icon, label, onClick, badge, accent, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`focus-ring relative flex flex-col items-center justify-center gap-2 py-4 rounded-xl border transition disabled:opacity-40 ${
        accent
          ? 'border-[var(--gold)] text-[var(--gold)] bg-[var(--gold-soft)]'
          : 'border-[var(--line)] text-[var(--ink-2)] hover:text-[var(--gold)] hover:border-[var(--line-strong)] hover:bg-[var(--surface-2)]'
      }`}
    >
      <Icon size={20} aria-hidden />
      <span className="text-xs font-ui">{label}</span>
      {badge > 0 && (
        <span className="absolute top-2 right-2 min-w-[16px] h-4 px-1 rounded-full bg-[var(--gold)] text-[#1a1408] text-[10px] font-semibold leading-4 text-center">
          {badge}
        </span>
      )}
    </button>
  )
}

export default function MenuPanel({
  questCount, canLevelUp,
  onHero, onInventory, onQuests, onMap, onShop, onParty, onRest, onLevelUp, onSave, onLoad, onLeave,
}) {
  return (
    <div>
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2.5">
        <Item icon={User} label="Hero" onClick={onHero} />
        <Item icon={Backpack} label="Inventory" onClick={onInventory} />
        <Item icon={Scroll} label="Quests" onClick={onQuests} badge={questCount} />
        <Item icon={Map} label="Map" onClick={onMap} />
        <Item icon={ShoppingBag} label="Shop" onClick={onShop} />
        <Item icon={Users} label="Party" onClick={onParty} />
        <Item icon={Moon} label="Rest" onClick={onRest} />
        {canLevelUp && <Item icon={ArrowUpCircle} label="Level up" onClick={onLevelUp} accent />}
        <Item icon={Save} label="Save" onClick={onSave} />
        <Item icon={FolderOpen} label="Load" onClick={onLoad} />
      </div>
      <button
        type="button"
        onClick={onLeave}
        className="focus-ring mt-5 w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-[var(--line)] text-[var(--ink-3)] hover:text-[var(--ember)] hover:border-[color-mix(in_srgb,var(--ember)_40%,transparent)] transition text-sm font-ui"
      >
        <LogOut size={16} aria-hidden /> Leave the adventure
      </button>
    </div>
  )
}
