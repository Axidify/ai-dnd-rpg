import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const diceTypes = [
  { sides: 4, color: '#e53935' },
  { sides: 6, color: '#8e24aa' },
  { sides: 8, color: '#1e88e5' },
  { sides: 10, color: '#43a047' },
  { sides: 12, color: '#ff5722' },
  { sides: 20, color: '#ffd700' },
]

export default function DiceRoller() {
  const [selectedDice, setSelectedDice] = useState({ sides: 20, color: '#ffd700' })
  const [rolling, setRolling] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const rollCount = useRef(0)
  
  const rollDice = () => {
    setRolling(true)
    setResult(null)
    rollCount.current++
    const currentRoll = rollCount.current
    
    // Simulate rolling animation
    const animationDuration = 1000
    const intervalTime = 50
    const iterations = animationDuration / intervalTime
    let i = 0
    
    const interval = setInterval(() => {
      const randomValue = Math.floor(Math.random() * selectedDice.sides) + 1
      setResult(randomValue)
      i++
      
      if (i >= iterations) {
        clearInterval(interval)
        const finalValue = Math.floor(Math.random() * selectedDice.sides) + 1
        setResult(finalValue)
        setRolling(false)
        setHistory(prev => [
          { id: currentRoll, dice: `d${selectedDice.sides}`, value: finalValue },
          ...prev.slice(0, 9)
        ])
      }
    }, intervalTime)
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="mt-4"
    >
      {/* Dice Type Selection */}
      <div className="flex justify-center gap-2 mb-4">
        {diceTypes.map((dice) => (
          <motion.button
            key={dice.sides}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setSelectedDice(dice)}
            className={`w-10 h-10 rounded-lg border-2 font-bold text-sm transition-all ${
              selectedDice.sides === dice.sides
                ? 'border-rpg-gold'
                : 'border-gray-600 hover:border-gray-400'
            }`}
            style={{ 
              backgroundColor: selectedDice.sides === dice.sides ? `${dice.color}30` : 'transparent',
              color: dice.color
            }}
          >
            d{dice.sides}
          </motion.button>
        ))}
      </div>
      
      {/* Roll Button and Result */}
      <div className="flex items-center justify-center gap-6">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={rollDice}
          disabled={rolling}
          className="rpg-button px-6 py-2"
        >
          {rolling ? 'Rolling...' : `Roll d${selectedDice.sides}`}
        </motion.button>
        
        <AnimatePresence mode="wait">
          {result !== null && (
            <motion.div
              key={result}
              initial={{ scale: 0, rotate: -180 }}
              animate={{ 
                scale: 1, 
                rotate: 0,
                transition: { type: 'spring', bounce: 0.5 }
              }}
              exit={{ scale: 0, rotate: 180 }}
              className={`w-16 h-16 rounded-lg flex items-center justify-center text-2xl font-bold border-2 ${
                rolling ? 'animate-shake' : ''
              }`}
              style={{
                backgroundColor: `${selectedDice.color}30`,
                borderColor: selectedDice.color,
                color: selectedDice.color,
                boxShadow: rolling ? 'none' : `0 0 20px ${selectedDice.color}60`
              }}
            >
              {result}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {/* Roll History */}
      {history.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 flex flex-wrap justify-center gap-2"
        >
          {history.map((roll, index) => (
            <motion.span
              key={roll.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1 - index * 0.1, x: 0 }}
              className="text-sm text-gray-400"
            >
              {roll.dice}: {roll.value}
            </motion.span>
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}
