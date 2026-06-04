import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const diceTypes = [
  { sides: 4, color: '#C44B4B' },
  { sides: 6, color: '#9B7BB8' },
  { sides: 8, color: '#4A8FBD' },
  { sides: 10, color: '#5A9A6E' },
  { sides: 12, color: '#D4845A' },
  { sides: 20, color: '#C9A227' },
]

export default function DiceRoller() {
  const [selectedDice, setSelectedDice] = useState(diceTypes[5])
  const [rolling, setRolling] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const rollCount = useRef(0)

  const rollDice = () => {
    setRolling(true)
    setResult(null)
    rollCount.current += 1
    const currentRoll = rollCount.current

    const animationDuration = 1000
    const intervalTime = 50
    const iterations = animationDuration / intervalTime
    let i = 0

    const interval = setInterval(() => {
      setResult(Math.floor(Math.random() * selectedDice.sides) + 1)
      i += 1

      if (i >= iterations) {
        clearInterval(interval)
        const finalValue = Math.floor(Math.random() * selectedDice.sides) + 1
        setResult(finalValue)
        setRolling(false)
        setHistory((prev) => [
          { id: currentRoll, dice: `d${selectedDice.sides}`, value: finalValue },
          ...prev.slice(0, 9),
        ])
      }
    }, intervalTime)
  }

  return (
    <div className="py-2">
      <p className="text-center text-sm text-rpg-text-muted font-body mb-6">
        Choose a die, then roll. Results stay in this session only.
      </p>

      <div className="flex flex-wrap justify-center gap-2 mb-6">
        {diceTypes.map((dice) => (
          <button
            key={dice.sides}
            type="button"
            onClick={() => setSelectedDice(dice)}
            aria-pressed={selectedDice.sides === dice.sides}
            className={`rpg-focus min-w-[44px] min-h-[44px] px-2 rounded-md border font-body font-semibold text-sm transition ${
              selectedDice.sides === dice.sides
                ? 'border-rpg-gold bg-rpg-gold/10'
                : 'border-rpg-border hover:border-rpg-border-gold'
            }`}
            style={{
              color: selectedDice.sides === dice.sides ? dice.color : undefined,
            }}
          >
            d{dice.sides}
          </button>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
        <button
          type="button"
          onClick={rollDice}
          disabled={rolling}
          className="rpg-button min-h-[44px] px-8"
        >
          {rolling ? 'Rolling…' : `Roll d${selectedDice.sides}`}
        </button>

        <AnimatePresence mode="wait">
          {result !== null && (
            <motion.div
              key={`${selectedDice.sides}-${result}-${rolling}`}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="w-20 h-20 rounded-lg flex items-center justify-center text-3xl font-display border-2 border-rpg-gold bg-rpg-gold/10 text-rpg-gold shadow-glow"
              aria-live="polite"
              aria-label={`Roll result: ${result}`}
            >
              {result}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {history.length > 0 && (
        <div className="mt-8 pt-4 border-t border-rpg-border/50">
          <p className="text-xs text-rpg-text-muted uppercase tracking-wide text-center mb-3 font-body">
            Recent rolls
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {history.map((roll) => (
              <span
                key={roll.id}
                className="text-sm font-body text-rpg-text-secondary px-2 py-1 rounded-md bg-rpg-paper-inset border border-rpg-border/40"
              >
                {roll.dice}: <span className="text-rpg-gold tabular-nums">{roll.value}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
