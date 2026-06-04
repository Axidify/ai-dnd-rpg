import { Coins, ShoppingBag } from 'lucide-react'

export default function ShopPanel({ character, shopInventory, isLoading, onBuy, onSell }) {
  const gold = character?.gold ?? 0

  return (
    <div>
      <div className="flex items-center justify-center gap-2 mb-5 text-[var(--gold)]">
        <Coins size={16} aria-hidden />
        <span className="font-display text-xl">{gold}</span>
        <span className="caps-muted">gold</span>
      </div>

      {!shopInventory ? (
        <div className="text-center py-10 text-[var(--ink-3)]">
          <ShoppingBag size={36} className="mx-auto mb-3 opacity-50" aria-hidden />
          <p className="font-read italic">Browsing the wares…</p>
        </div>
      ) : (
        <div className="space-y-6">
          <section>
            <p className="caps mb-3">For sale</p>
            {shopInventory.shop_items?.length ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {shopInventory.shop_items.map((item, i) => {
                  const tooPoor = gold < item.price
                  return (
                    <div key={i} className="panel-inset rounded-lg p-3 flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-[var(--ink)] font-medium truncate">{item.name}</div>
                        <div className="text-xs text-[var(--ink-3)]">{item.type}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => onBuy?.(item.name)}
                        disabled={isLoading || tooPoor}
                        className="focus-ring shrink-0 text-xs px-3 py-1.5 rounded-md border border-[var(--sage)]/50 text-[var(--sage)] hover:bg-[var(--sage)]/10 transition disabled:opacity-40"
                      >
                        {item.price}g
                      </button>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-[var(--ink-3)] font-read italic">Nothing for sale here.</p>
            )}
          </section>

          <section>
            <p className="caps mb-3">Sell</p>
            {character?.inventory?.length ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {character.inventory.map((item, i) => {
                  const name = typeof item === 'string' ? item : item.name
                  return (
                    <div key={i} className="panel-inset rounded-lg p-3 flex items-center justify-between gap-3">
                      <span className="text-[var(--ink)] truncate">{name}</span>
                      <button
                        type="button"
                        onClick={() => onSell?.(name)}
                        disabled={isLoading}
                        className="focus-ring shrink-0 text-xs px-3 py-1.5 rounded-md border border-[var(--line-strong)] text-[var(--ink-2)] hover:text-[var(--gold)] hover:border-[var(--gold)] transition disabled:opacity-40"
                      >
                        Sell
                      </button>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-[var(--ink-3)] font-read italic">You have nothing to sell.</p>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
