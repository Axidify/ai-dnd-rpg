import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sword, Sparkles, Crosshair, Cross, Target, Axe, Shield, Flame, Music, Hand, Leaf, Star,
  Map, ChevronLeft, ChevronRight,
} from 'lucide-react'
import { useGameStore } from '../store/gameStore'

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

const races = ['Human', 'Elf', 'Dwarf', 'Halfling', 'Half-Orc', 'Tiefling', 'Dragonborn', 'Gnome', 'Half-Elf']
const STEPS = ['Name', 'Calling', 'Heritage', 'Beginning']

export default function CharacterCreation({ onBack }) {
  const [step, setStep] = useState(0)
  const [name, setName] = useState('')
  const [selectedClass, setSelectedClass] = useState(null)
  const [selectedRace, setSelectedRace] = useState('Human')
  const [selectedScenario, setSelectedScenario] = useState(null)

  const { createCharacter, fetchScenarios, scenarios, isLoading, error } = useGameStore()

  useEffect(() => {
    fetchScenarios()
  }, [fetchScenarios])

  const canNext = () => {
    if (step === 0) return name.trim().length >= 2
    if (step === 1) return !!selectedClass
    if (step === 2) return !!selectedRace
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
                  <p className="text-sm text-[var(--ink-3)] font-read italic mt-3">
                    This is how the Dungeon Master will know you.
                  </p>
                </div>
              )}

              {step === 1 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {classes.map((cls) => {
                    const Icon = cls.icon
                    const active = selectedClass?.name === cls.name
                    return (
                      <button
                        key={cls.name}
                        type="button"
                        onClick={() => setSelectedClass(cls)}
                        aria-pressed={active}
                        className={`focus-ring p-4 rounded-xl border text-left transition ${
                          active
                            ? 'border-[var(--gold)] bg-[var(--gold-soft)]'
                            : 'border-[var(--line)] hover:border-[var(--line-strong)] hover:bg-[var(--surface)]'
                        }`}
                      >
                        <Icon size={22} className={active ? 'text-[var(--gold)]' : 'text-[var(--ink-2)]'} aria-hidden />
                        <div className="font-ui font-medium text-sm mt-2 text-[var(--ink)]">{cls.name}</div>
                        <div className="text-[11px] text-[var(--ink-3)] font-read leading-snug mt-0.5">{cls.desc}</div>
                      </button>
                    )
                  })}
                </div>
              )}

              {step === 2 && (
                <div className="flex flex-wrap gap-2.5">
                  {races.map((race) => {
                    const active = selectedRace === race
                    return (
                      <button
                        key={race}
                        type="button"
                        onClick={() => setSelectedRace(race)}
                        aria-pressed={active}
                        className={`focus-ring px-4 py-3 rounded-xl border font-ui text-sm transition ${
                          active
                            ? 'border-[var(--gold)] text-[var(--gold)] bg-[var(--gold-soft)]'
                            : 'border-[var(--line)] text-[var(--ink-2)] hover:border-[var(--line-strong)] hover:text-[var(--ink)]'
                        }`}
                      >
                        {race}
                      </button>
                    )
                  })}
                </div>
              )}

              {step === 3 && (
                <div className="space-y-2.5">
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
                    <div className="text-sm text-[var(--ink-3)] font-read mt-0.5">Wander freely and forge your own path.</div>
                  </button>
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
                  Beginning…
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
