import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sword, Sparkles, Crosshair, Cross, Target, Axe, Shield, Flame, Music, Hand, Leaf, Star,
  Map, ChevronLeft, ChevronRight, Heart, Coins, Check,
} from 'lucide-react'
import { useGameStore } from '../store/gameStore'
import AbilityGrid, { formatModifier } from './AbilityGrid'

const classes = [
  { name: 'Fighter', icon: Sword, desc: 'Master of martial combat' },
  { name: 'Wizard', icon: Sparkles, desc: 'Wielder of arcane secrets' },
  { name: 'Rogue', icon: Crosshair, desc: 'Stealthy and cunning' },
  { name: 'Cleric', icon: Cross, desc: 'Divine healer and warrior' },
  { name: 'Ranger', icon: Target, desc: 'Hunter and tracker' },
  { name: 'Barbarian', icon: Axe, desc: 'Fierce primal warrior' },
  { name: 'Paladin', icon: Shield, desc: 'Holy knight of justice' },
  { name: 'Warlock', icon: Flame, desc: 'Pact-bound spellcaster' },
  { name: 'Bard', icon: Music, desc: 'Magical wanderer' },
  { name: 'Monk', icon: Hand, desc: 'Master of body and mind' },
  { name: 'Druid', icon: Leaf, desc: "Nature's guardian" },
  { name: 'Sorcerer', icon: Star, desc: 'Innate magic in the blood' },
]

const races = [
  { name: 'Human', desc: 'Adaptable and ambitious; found in every corner of the realm' },
  { name: 'Elf', desc: 'Graceful and long-lived, with keen senses and old memories' },
  { name: 'Dwarf', desc: 'Stout and stubborn, at home in stone and forge-light' },
  { name: 'Halfling', desc: 'Small, quick and lucky; easily underestimated' },
  { name: 'Half-Orc', desc: 'Strong and enduring, often met with wary eyes' },
  { name: 'Tiefling', desc: 'Touched by infernal blood; striking, and rarely trusted' },
  { name: 'Dragonborn', desc: 'Proud, scaled kin of dragons, with a fierce sense of honour' },
  { name: 'Gnome', desc: 'Curious tinkerers and tricksters with boundless energy' },
  { name: 'Half-Elf', desc: 'At home in two worlds and wholly of neither' },
]
const STEPS = ['Name', 'Calling', 'Heritage', 'Your hero', 'Beginning']
const REVIEW_STEP = 3

const titleCase = (s) => String(s || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export default function CharacterCreation({ onBack }) {
  const [step, setStep] = useState(0)
  const [name, setName] = useState('')
  const [selectedClass, setSelectedClass] = useState(null)
  const [selectedRace, setSelectedRace] = useState('Human')
  // undefined = not chosen yet (defaults to the first adventure); null = open road
  const [chosenScenario, setSelectedScenario] = useState(undefined)

  const {
    createCharacter, fetchScenarios, scenarios, isLoading, error,
    preview, previewLoading, previewCharacter, classInfo, fetchClassInfo,
  } = useGameStore()
  const selectedScenario = chosenScenario === undefined ? scenarios[0] ?? null : chosenScenario

  useEffect(() => {
    fetchScenarios()
    fetchClassInfo()
  }, [fetchScenarios, fetchClassInfo])

  // Roll (or re-roll after edits) when the review step opens
  const heroKey = selectedClass ? `${name.trim()}|${selectedClass.name}|${selectedRace}` : null
  useEffect(() => {
    if (step === REVIEW_STEP && selectedClass) {
      previewCharacter(name.trim(), selectedClass.name, selectedRace)
    }
  }, [step, heroKey]) // eslint-disable-line react-hooks/exhaustive-deps
  const hero = preview?.key === heroKey ? preview.character : null

  const canNext = () => {
    if (step === 0) return name.trim().length >= 2
    if (step === 1) return !!selectedClass
    if (step === 2) return !!selectedRace
    if (step === REVIEW_STEP) return !!hero
    return true
  }

  const handleCreate = () => {
    if (name && selectedClass) {
      createCharacter(name.trim(), selectedClass.name, selectedRace, selectedScenario?.id || null)
    }
  }

  return (
    <div className="relative z-10 min-h-[100dvh] flex flex-col px-5 py-6 sm:py-10">
      <div className="w-full max-w-lg mx-auto flex-1 flex flex-col">
        <header className="mb-7">
          <button
            type="button"
            onClick={onBack}
            className="focus-ring inline-flex items-center gap-1 text-sm font-ui text-[var(--ink-3)] hover:text-[var(--gold)] mb-6 transition"
          >
            <ChevronLeft size={16} aria-hidden />
            Back
          </button>

          <div className="flex items-center gap-2 mb-4">
            {STEPS.map((label, i) => (
              <div key={label} className="flex-1">
                <div
                  className={`h-0.5 rounded-full transition-colors duration-300 ${
                    i <= step ? 'bg-[var(--gold)]' : 'bg-[var(--line-strong)]'
                  }`}
                />
              </div>
            ))}
          </div>
          <p className="caps-muted mb-1">Chapter {step + 1} of {STEPS.length}</p>
          <h1 className="display text-3xl sm:text-4xl">{STEPS[step]}</h1>
        </header>

        <div className="flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
            >
              {step === 0 && (
                <div>
                  <label htmlFor="hero-name" className="caps mb-3 block">
                    What are you called?
                  </label>
                  <input
                    id="hero-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && canNext() && setStep(1)}
                    placeholder="Elara Nightwood"
                    className="field-boxed focus-ring text-2xl font-display py-4"
                    autoFocus
                    autoComplete="off"
                  />
                  <p className="text-sm text-[var(--ink-3)] font-read italic mt-3" aria-live="polite">
                    {name.trim().length === 1
                      ? 'A little longer: at least 2 letters.'
                      : 'This is how the Dungeon Master will know you.'}
                  </p>
                </div>
              )}

              {step === 1 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {classes.map((cls) => {
                    const Icon = cls.icon
                    const active = selectedClass?.name === cls.name
                    const kit = classInfo[cls.name]
                    return (
                      <button
                        key={cls.name}
                        type="button"
                        onClick={() => setSelectedClass(cls)}
                        aria-pressed={active}
                        className={`focus-ring relative p-4 rounded-xl border text-left transition flex flex-col justify-start ${
                          active
                            ? 'border-[var(--gold)] bg-[var(--gold-soft)] ring-1 ring-[var(--gold)]'
                            : 'border-[var(--line)] hover:border-[var(--line-strong)] hover:bg-[var(--surface)]'
                        }`}
                      >
                        {active && (
                          <Check size={15} className="absolute top-3 right-3 text-[var(--gold)]" aria-hidden />
                        )}
                        <Icon size={22} className={active ? 'text-[var(--gold)]' : 'text-[var(--ink-2)]'} aria-hidden />
                        <div className={`font-ui font-medium text-sm mt-2 ${active ? 'text-[var(--gold-bright)]' : 'text-[var(--ink)]'}`}>{cls.name}</div>
                        <div className="text-[11px] text-[var(--ink-3)] font-read leading-snug mt-0.5">{cls.desc}</div>
                        {kit && (
                          <div className="text-[10.5px] text-[var(--ink-2)] font-ui mt-2 tabular-nums">
                            d{kit.hit_die} HP · {kit.weapon}
                          </div>
                        )}
                      </button>
                    )
                  })}
                </div>
              )}

              {step === 2 && (
                <div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    {races.map((race) => {
                      const active = selectedRace === race.name
                      return (
                        <button
                          key={race.name}
                          type="button"
                          onClick={() => setSelectedRace(race.name)}
                          aria-pressed={active}
                          className={`focus-ring relative px-4 py-3 rounded-xl border text-left transition flex flex-col justify-start ${
                            active
                              ? 'border-[var(--gold)] bg-[var(--gold-soft)] ring-1 ring-[var(--gold)]'
                              : 'border-[var(--line)] hover:border-[var(--line-strong)] hover:bg-[var(--surface)]'
                          }`}
                        >
                          {active && (
                            <Check size={14} className="absolute top-3 right-3 text-[var(--gold)]" aria-hidden />
                          )}
                          <div className={`font-ui font-medium text-sm ${active ? 'text-[var(--gold-bright)]' : 'text-[var(--ink)]'}`}>
                            {race.name}
                          </div>
                          <div className="text-[11px] text-[var(--ink-3)] font-read leading-snug mt-0.5 pr-4">{race.desc}</div>
                        </button>
                      )
                    })}
                  </div>
                  <p className="text-sm text-[var(--ink-3)] font-read italic mt-4">
                    Heritage shapes how the world sees you and how the Dungeon Master tells your story. It doesn't change your stats.
                  </p>
                </div>
              )}

              {step === REVIEW_STEP && (
                <div aria-live="polite">
                  {!hero ? (
                    <p className="font-read italic text-[var(--ink-2)]">
                      {previewLoading ? 'Rolling your fate…' : 'Your hero could not be rolled.'}
                    </p>
                  ) : (
                    <div className="space-y-5">
                      <div>
                        <p className="display text-2xl">{hero.name}</p>
                        <p className="text-sm text-[var(--ink-3)] font-ui">
                          Level 1 · {hero.race} {hero.char_class}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {[
                          [Heart, 'Hit points', hero.max_hp],
                          [Shield, 'Armor', hero.armor_class],
                          [Sword, 'Attack', `${formatModifier(hero.attack_bonus)}${hero.weapon_damage ? ` · ${hero.weapon_damage}` : ''}`],
                          [Coins, 'Gold', hero.gold],
                        ].map(([Icon, label, value]) => (
                          <div key={label} className="panel-inset rounded-lg px-3 py-2.5">
                            <div className="caps-muted leading-none mb-1.5 flex items-center gap-1.5">
                              <Icon size={12} className="text-[var(--gold)]" aria-hidden />
                              {label}
                            </div>
                            <div className="text-base text-[var(--ink)] tabular-nums font-ui">{value}</div>
                          </div>
                        ))}
                      </div>

                      <div>
                        <p className="caps-muted mb-2">Abilities <span className="normal-case tracking-normal">(4d6, drop lowest)</span></p>
                        <AbilityGrid character={hero} />
                      </div>

                      <div>
                        <p className="caps-muted mb-2">Starting gear</p>
                        <p className="text-sm text-[var(--ink-2)] font-read leading-relaxed">
                          {hero.inventory
                            .map((item) => (item.quantity > 1 ? `${item.name} ×${item.quantity}` : item.name))
                            .join(' · ')}
                        </p>
                        <p className="text-xs text-[var(--ink-3)] font-ui mt-1.5">
                          Wielding {titleCase(hero.weapon)}
                          {hero.equipped_armor ? `, wearing ${titleCase(hero.equipped_armor)}` : ''}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {step === 4 && (
                <div className="space-y-2.5">
                  {scenarios.map((scenario) => {
                    const active = selectedScenario?.id === scenario.id
                    return (
                      <button
                        key={scenario.id}
                        type="button"
                        onClick={() => setSelectedScenario(scenario)}
                        aria-pressed={active}
                        className={`focus-ring w-full p-4 rounded-xl border text-left transition ${
                          active
                            ? 'border-[var(--gold)] bg-[var(--gold-soft)]'
                            : 'border-[var(--line)] hover:border-[var(--line-strong)] hover:bg-[var(--surface)]'
                        }`}
                      >
                        <div className="flex items-start gap-2.5">
                          <Map size={17} className="text-[var(--gold)] shrink-0 mt-1" aria-hidden />
                          <div>
                            <div className="font-display text-lg text-[var(--ink)]">{scenario.name}</div>
                            <div className="text-sm text-[var(--ink-3)] font-read mt-0.5">{scenario.description}</div>
                          </div>
                        </div>
                      </button>
                    )
                  })}
                  <button
                    type="button"
                    onClick={() => setSelectedScenario(null)}
                    aria-pressed={!selectedScenario}
                    className={`focus-ring w-full p-4 rounded-xl border text-left transition ${
                      !selectedScenario
                        ? 'border-[var(--gold)] bg-[var(--gold-soft)]'
                        : 'border-[var(--line)] hover:border-[var(--line-strong)] hover:bg-[var(--surface)]'
                    }`}
                  >
                    <div className="font-display text-lg text-[var(--ink)]">An open road</div>
                    <div className="text-sm text-[var(--ink-3)] font-read mt-0.5">
                      Freeform: no map, quests or set story. The Dungeon Master improvises everything.
                    </div>
                  </button>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {error && (
          <p role="alert" className="mt-4 text-sm font-ui" style={{ color: 'var(--ember)' }}>
            {error}
          </p>
        )}

        <div className="flex gap-2.5 mt-6 pt-2">
          {step > 0 && (
            <button
              type="button"
              onClick={() => setStep((s) => s - 1)}
              disabled={isLoading}
              className="btn btn-ghost focus-ring px-5 py-3"
            >
              <ChevronLeft size={16} className="inline -ml-1 mr-1" aria-hidden />
              Back
            </button>
          )}
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              disabled={!canNext()}
              className="btn btn-primary focus-ring flex-1 py-3 flex items-center justify-center gap-1"
            >
              Continue
              <ChevronRight size={16} aria-hidden />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleCreate}
              disabled={!name || !selectedClass || isLoading}
              className="btn btn-primary focus-ring flex-1 py-3 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <span className="w-4 h-4 rounded-full border-2 border-[#1a1408]/40 border-t-[#1a1408] animate-spin" />
                  The DM is setting the scene…
                </>
              ) : (
                'Begin the tale'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
