import { useEffect, useMemo, useState } from 'react'
import {
  Beer, Landmark, Hammer, Trees, AlertTriangle, Skull, Gem, Sword, Crown, Sparkles, Lock,
  Package, Sun, Eye, User, PartyPopper, Footprints, Flame, Archive, MapPin, Navigation,
} from 'lucide-react'
import Modal from './Modal'
import { useGameStore } from '../store/gameStore'

// Scenario data uses emoji for map icons; draw them as line icons in the house style
const ICONS = {
  '🍺': Beer, '🍻': Beer, '🏛️': Landmark, '🛠️': Hammer, '🌲': Trees, '🌳': Trees,
  '⚠️': AlertTriangle, '💀': Skull, '💎': Gem, '⚔️': Sword, '👑': Crown, '🔮': Sparkles,
  '🔒': Lock, '📦': Package, '☀️': Sun, '👁️': Eye, '👤': User, '🎉': PartyPopper,
  '🎊': PartyPopper, '🏃': Footprints, '🕯️': Flame, '⚰️': Archive,
}
const iconFor = (emoji) => ICONS[emoji] || MapPin

// Region bands behind the markers (alpha tints of the palette)
const REGION_TINT = {
  village: 'rgba(194, 168, 104, 0.07)',
  forest: 'rgba(147, 168, 119, 0.07)',
  cave: 'rgba(199, 107, 74, 0.06)',
}
const REGION_NAMES = { village: 'Village', forest: 'Forest', cave: 'Caves' }

// Several scenario locations share a spot (e.g. a "return" version of a place).
// Show one marker per spot, preferring the one that matters right now.
function onePerSpot(locations) {
  const rank = (l) => (l.is_current ? 4 : 0) + (l.reachable ? 2 : 0) + (l.visited ? 1 : 0) + (l.known ? 0.5 : 0)
  const bySpot = new Map()
  for (const loc of locations) {
    const spot = `${Math.round(loc.map_x * 50)},${Math.round(loc.map_y * 50)}`
    const prev = bySpot.get(spot)
    if (!prev || rank(loc) > rank(prev)) bySpot.set(spot, loc)
  }
  return [...bySpot.values()]
}

function regionBands(locations) {
  const bands = {}
  for (const loc of locations) {
    const r = loc.map_region
    if (!REGION_TINT[r]) continue
    const b = bands[r] || (bands[r] = { min: 1, max: 0 })
    b.min = Math.min(b.min, loc.map_y)
    b.max = Math.max(b.max, loc.map_y)
  }
  return Object.entries(bands).map(([region, { min, max }]) => ({
    region,
    top: Math.max(0, min - 0.05),
    bottom: Math.min(1, max + 0.05),
  }))
}

// Board coordinates: keep markers off the very edge
const pos = (v) => 6 + v * 88

function Marker({ loc, selected, otherSelected, onSelect }) {
  const Icon = iconFor(loc.map_icon)
  const size = loc.is_current ? 34 : loc.known ? 28 : 12
  const tone = loc.is_current
    ? 'border-[var(--gold-bright)] bg-[var(--surface-2)] text-[var(--gold-bright)]'
    : loc.reachable
      ? 'border-[var(--gold)] bg-[var(--surface)] text-[var(--gold)]'
      : loc.visited
        ? 'border-[var(--line-strong)] bg-[var(--surface)] text-[var(--ink-2)]'
        : loc.known
          ? 'border-[var(--line-strong)] bg-[var(--bg-deep)] text-[var(--ink-3)]'
          : 'border-[var(--line)] bg-[var(--line-strong)]'
  // Only label where you are and what you picked; nearby places would collide
  const showLabel = loc.known && (selected || (loc.is_current && !otherSelected))

  return (
    <button
      type="button"
      onClick={() => loc.known && onSelect(loc)}
      disabled={!loc.known}
      aria-label={loc.known ? `${loc.name}${loc.is_current ? ' (you are here)' : loc.reachable ? ' (reachable)' : ''}` : 'Undiscovered place'}
      aria-pressed={selected}
      className={`focus-ring absolute -translate-x-1/2 -translate-y-1/2 rounded-full grid place-items-center border transition
        ${tone} ${selected ? 'ring-2 ring-[var(--gold)] ring-offset-2 ring-offset-[var(--bg)]' : ''}
        ${loc.known ? 'hover:scale-110 cursor-pointer' : 'cursor-default'}`}
      style={{ left: `${pos(loc.map_x)}%`, top: `${pos(loc.map_y)}%`, width: size, height: size }}
    >
      {loc.known && <Icon size={loc.is_current ? 16 : 13} aria-hidden />}
      {showLabel && (
        <span
          className={`absolute top-full mt-1 whitespace-nowrap font-ui text-[11px] px-1.5 py-0.5 rounded
            ${loc.map_x < 0.3 ? 'left-0' : loc.map_x > 0.7 ? 'right-0' : 'left-1/2 -translate-x-1/2'}
            bg-[color-mix(in_srgb,var(--bg)_85%,transparent)] ${loc.is_current ? 'text-[var(--gold-bright)]' : 'text-[var(--ink-2)]'}`}
        >
          {loc.map_label || loc.name}
        </span>
      )}
    </button>
  )
}

export default function WorldMap({ isOpen, onClose }) {
  const { getDestinations, travel, isLoading } = useGameStore()
  const [data, setData] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [travelError, setTravelError] = useState(null)

  const load = async () => {
    const result = await getDestinations()
    setData(result)
  }

  useEffect(() => {
    if (!isOpen) return
    setSelectedId(null)
    setTravelError(null)
    load()
  }, [isOpen]) // eslint-disable-line react-hooks/exhaustive-deps

  const locations = useMemo(() => onePerSpot(data?.all_locations || []), [data])
  const bands = useMemo(() => regionBands(locations), [locations])
  const current = locations.find((l) => l.is_current)
  // Reachable places by name (from the full list: a shared map spot may hide one)
  const destinations = (data?.all_locations || []).filter((l) => l.reachable && !l.is_current && l.known)
  const selected = (data?.all_locations || []).find((l) => l.id === selectedId) || current
  const discovered = (data?.all_locations || []).filter((l) => l.visited).length
  const total = (data?.all_locations || []).length

  const handleTravel = async () => {
    if (!selected?.reachable) return
    setTravelError(null)
    const result = await travel(selected.id)
    if (result?.success) {
      onClose?.()  // show the arrival in the story
    } else {
      setTravelError(result?.message || 'You can’t go that way right now.')
      load()
    }
  }

  return (
    <Modal open={isOpen} onClose={onClose} eyebrow={`${discovered} of ${total} places visited`} title="Map" titleId="map-title" maxWidth="max-w-4xl">
      <div className="flex flex-col md:flex-row gap-5 md:gap-7">
        {/* Board */}
        <div className="flex justify-center md:flex-none">
          <div
            className="relative w-full max-w-[26rem] md:w-auto md:h-[min(62vh,40rem)] aspect-[3/4] rounded-xl border border-[var(--line)] bg-[var(--bg-deep)] overflow-hidden"
            role="group"
            aria-label="Map of the region"
          >
            {bands.map((b) => (
              <div
                key={b.region}
                className="absolute inset-x-0"
                style={{ top: `${pos(b.top)}%`, height: `${pos(b.bottom) - pos(b.top)}%`, background: REGION_TINT[b.region] }}
              >
                {/* Name only bands with room for it (a thin band is all markers) */}
                {pos(b.bottom) - pos(b.top) >= 14 && (
                  <span className="caps-muted absolute left-2.5 bottom-1.5 opacity-70">{REGION_NAMES[b.region]}</span>
                )}
              </div>
            ))}

            {/* Paths to reachable places */}
            {current && (
              <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
                {locations.filter((l) => l.reachable && !l.is_current).map((l) => (
                  <line
                    key={l.id}
                    x1={pos(current.map_x)} y1={pos(current.map_y)}
                    x2={pos(l.map_x)} y2={pos(l.map_y)}
                    stroke="var(--gold)"
                    strokeOpacity={l.id === selected?.id ? 0.9 : 0.4}
                    strokeWidth={l.id === selected?.id ? 2 : 1.2}
                    strokeDasharray={l.id === selected?.id ? undefined : '3 3'}
                    vectorEffect="non-scaling-stroke"
                  />
                ))}
              </svg>
            )}

            {locations.map((loc) => (
              <Marker
                key={loc.id}
                loc={loc}
                selected={loc.id === selected?.id && !loc.is_current}
                otherSelected={Boolean(selected && !selected.is_current)}
                onSelect={(l) => { setSelectedId(l.id); setTravelError(null) }}
              />
            ))}

            {!data && (
              <p className="absolute inset-0 grid place-items-center font-read italic text-[var(--ink-3)]">Unrolling the map…</p>
            )}
            {data && total === 0 && (
              <p className="absolute inset-0 grid place-items-center px-6 text-center font-read italic text-[var(--ink-3)]">
                This tale has no map. Wherever you wander, the Dungeon Master will describe it.
              </p>
            )}
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 min-w-0 flex flex-col gap-4">
          {selected ? (
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                {(() => {
                  const Icon = iconFor(selected.map_icon)
                  return (
                    <span className="w-11 h-11 rounded-full grid place-items-center border border-[var(--line-strong)] bg-[var(--surface-2)] text-[var(--gold)] shrink-0">
                      <Icon size={18} aria-hidden />
                    </span>
                  )
                })()}
                <div className="min-w-0">
                  <h3 className="display text-xl leading-tight">{selected.name}</h3>
                  <p className="caps-muted mt-1">
                    {selected.is_current ? 'You are here' : selected.reachable ? 'Reachable from here' : selected.visited ? 'Visited' : 'Not reachable from here'}
                  </p>
                </div>
              </div>
              {selected.description && (
                <p className="font-read text-[var(--ink-2)] leading-relaxed">{selected.description}</p>
              )}
              {selected.reachable && !selected.is_current && (
                <button
                  type="button"
                  onClick={handleTravel}
                  disabled={isLoading}
                  className="btn btn-primary focus-ring w-full py-3 flex items-center justify-center gap-2"
                >
                  <Navigation size={16} aria-hidden />
                  {isLoading ? 'Travelling…' : `Travel to ${selected.map_label || selected.name}`}
                </button>
              )}
              {travelError && (
                <p role="alert" className="text-sm font-ui" style={{ color: 'var(--ember)' }}>{travelError}</p>
              )}
              {!selected.is_current && current && (
                <button
                  type="button"
                  onClick={() => { setSelectedId(null); setTravelError(null) }}
                  className="focus-ring text-sm font-ui text-[var(--ink-3)] hover:text-[var(--gold)] transition"
                >
                  ← Back to {current.map_label || current.name}
                </button>
              )}
              {selected.is_current && data?.path_hint && (
                <p className="text-sm font-read italic text-[var(--ink-2)]">{data.path_hint.replace(/^🚪\s*/u, '')}</p>
              )}
              {selected.is_current && destinations.length > 0 && (
                <div className="pt-2">
                  <p className="caps-muted mb-2">Paths from here</p>
                  <ul className="space-y-1.5">
                    {destinations.map((d) => (
                      <li key={d.id}>
                        <button
                          type="button"
                          onClick={() => { setSelectedId(d.id); setTravelError(null) }}
                          className="focus-ring w-full flex items-center justify-between gap-3 px-3 py-2 rounded-lg border border-[var(--line)] hover:border-[var(--gold)] hover:bg-[var(--gold-soft)] transition text-left"
                        >
                          <span className="font-ui text-sm text-[var(--ink)] truncate">{d.map_label || d.name}</span>
                          <span className="caps-muted shrink-0">{d.visited ? 'Visited' : 'New'}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="font-read italic text-[var(--ink-3)]">Choose a place on the map.</p>
          )}

          {data && total > 0 && (
            <div className="mt-auto pt-4 border-t border-[var(--line)]">
              <p className="caps-muted mb-2.5">Key</p>
              <ul className="grid grid-cols-2 gap-2 text-xs font-ui text-[var(--ink-2)]">
                <li className="flex items-center gap-2"><span className="w-3.5 h-3.5 rounded-full border border-[var(--gold-bright)] bg-[var(--surface-2)]" />You are here</li>
                <li className="flex items-center gap-2"><span className="w-3.5 h-3.5 rounded-full border border-[var(--gold)]" />Reachable</li>
                <li className="flex items-center gap-2"><span className="w-3.5 h-3.5 rounded-full border border-[var(--line-strong)] bg-[var(--surface)]" />Known</li>
                <li className="flex items-center gap-2"><span className="w-2.5 h-2.5 mx-0.5 rounded-full bg-[var(--line-strong)]" />Undiscovered</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </Modal>
  )
}
