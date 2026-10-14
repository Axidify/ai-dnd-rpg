import { useState } from 'react'
import { Coins, ShoppingBag } from 'lucide-react'

const SELL_BLOCKED = {
  equipped: 'In use',
  quest: 'Quest item',
}

function Row({ title, detail, children }) {
  return (
    <div className="panel-inset rounded-lg p-3 flex items-center justify-between gap-3">
      <div className="min-w-0">
        <div className="text-[var(--ink)] font-medium truncate">{title}</div>
        {detail && <div className="text-xs text-[var(--ink-3)] font-read leading-snug mt-0.5">{detail}</div>}
      </div>
      {children}
    </div>
  )
}

export default function ShopPanel({ character, shopInventory, isLoading, onBuy, onSell }) {
  const gold = character?.gold ?? 0
  const [result, setResult] = useState(null)  // { success, message }

  const run = async (action) => {
    setResult(null)
    const res = await action()
    if (res?.message) setResult({ success: Boolean(res.success), message: res.message })
  }

  const items = shopInventory?.items || []
  const offers = shopInventory?.sell_offers || []

  return (
    <div>
      <div className="flex items-center justify-center gap-2 mb-2 text-[var(--gold)]">
        <Coins size={16} aria-hidden />
        <span className="font-display text-xl tabular-nums">{gold}</span>
        <span className="caps-muted">gold</span>
      </div>
      {shopInventory && !shopInventory.is_local && (
        <p className="text-center text-xs text-[var(--ink-3)] font-read italic mb-4">
          A pedlar's general wares. Look for local merchants on your travels.
        </p>
      )}

      {result && (
        <p
          role="status"
          className="mb-4 text-sm font-ui text-center"
          style={{ color: result.success ? 'var(--sage)' : 'var(--ember)' }}
        >
          {result.message}
        </p>
      )}

      {!shopInventory ? (
        <div className="text-center py-10 text-[var(--ink-3)]">
          <ShoppingBag size={36} className="mx-auto mb-3 opacity-50" aria-hidden />
          <p className="font-read italic">Browsing the wares…</p>
        </div>
      ) : (
        <div className="space-y-6">
          <section>
            <p className="caps mb-3">Buy</p>
            {items.length ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {items.map((item) => {
                  const tooPoor = gold < item.price
                  const limited = item.stock >= 0
                  return (
                    <Row
                      key={item.id}
                      title={item.name}
                      detail={[item.description, limited ? `${item.stock} left` : null].filter(Boolean).join(' · ')}
                    >
                      <button
                        type="button"
                        onClick={() => run(() => onBuy?.(item.id))}
                        disabled={isLoading || tooPoor}
                        aria-label={tooPoor ? `${item.name}: need ${item.price} gold` : `Buy ${item.name} for ${item.price} gold`}
                        className="focus-ring shrink-0 text-xs px-3 py-1.5 rounded-md border border-[color-mix(in_srgb,var(--gold)_55%,transparent)] text-[var(--gold)] hover:bg-[var(--gold-soft)] transition disabled:opacity-60 disabled:border-[var(--line)] disabled:text-[var(--ink-3)] disabled:hover:bg-transparent whitespace-nowrap tabular-nums"
                      >
                        {tooPoor ? `Need ${item.price}g` : `Buy · ${item.price}g`}
                      </button>
                    </Row>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-[var(--ink-3)] font-read italic">Nothing for sale here.</p>
            )}
          </section>

          <section>
            <p className="caps mb-3">Sell</p>
            {offers.length ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {offers.map((offer, i) => (
                  <Row key={`${offer.name}-${i}`} title={offer.quantity > 1 ? `${offer.name} ×${offer.quantity}` : offer.name}>
                    {offer.can_sell ? (
                      <button
                        type="button"
                        onClick={() => run(() => onSell?.(offer.name))}
                        disabled={isLoading}
                        aria-label={`Sell ${offer.name} for ${offer.price} gold`}
                        className="focus-ring shrink-0 text-xs px-3 py-1.5 rounded-md border border-[var(--line-strong)] text-[var(--ink-2)] hover:text-[var(--gold)] hover:border-[var(--gold)] transition disabled:opacity-50 whitespace-nowrap tabular-nums"
                      >
                        Sell · {offer.price}g
                      </button>
                    ) : (
                      <span className="shrink-0 text-xs text-[var(--ink-3)] font-ui" title={offer.reason === 'equipped' ? 'Equip something else first' : 'Needed for a quest'}>
                        {SELL_BLOCKED[offer.reason] || 'Not for sale'}
                      </span>
                    )}
                  </Row>
                ))}
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
