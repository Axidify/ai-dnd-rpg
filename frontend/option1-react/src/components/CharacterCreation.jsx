import { useState } from 'react'
import { motion } from 'framer-motion'
import { Sword, Wand2, Dagger, Cross, Bow, Axe } from 'lucide-react'
import { useGameStore } from '../store/gameStore'
import DiceRoller from './DiceRoller'

const classes = [
  { name: 'Fighter', icon: Sword, desc: 'Master of martial combat', color: '#e53935' },
  { name: 'Wizard', icon: Wand2, desc: 'Wielder of arcane magic', color: '#8e24aa' },
  { name: 'Rogue', icon: Dagger, desc: 'Stealthy and cunning', color: '#43a047' },
  { name: 'Cleric', icon: Cross, desc: 'Divine healer and warrior', color: '#ffd700' },
  { name: 'Ranger', icon: Bow, desc: 'Skilled hunter and tracker', color: '#1e88e5' },
  { name: 'Barbarian', icon: Axe, desc: 'Fierce primal warrior', color: '#ff5722' },
]

const races = ['Human', 'Elf', 'Dwarf', 'Halfling', 'Half-Orc', 'Tiefling']

export default function CharacterCreation() {
  const [name, setName] = useState('')
  const [selectedClass, setSelectedClass] = useState(null)
  const [selectedRace, setSelectedRace] = useState('Human')
  const [showDice, setShowDice] = useState(false)
  
  const { createCharacter, isLoading, error } = useGameStore()
  
  const handleCreate = () => {
    if (name && selectedClass) {
      createCharacter(name, selectedClass.name, selectedRace)
    }
  }
  
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="max-w-2xl w-full"
      >
        {/* Title */}
        <motion.h1 
          className="text-4xl md:text-5xl font-medieval text-center mb-8 text-rpg-gold"
          initial={{ y: -20 }}
          animate={{ y: 0 }}
        >
          ⚔️ Create Your Hero ⚔️
        </motion.h1>
        
        {/* Character Name */}
        <div className="rpg-card p-6 mb-6">
          <label className="block text-rpg-gold font-medieval text-lg mb-2">
            Hero Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your hero's name..."
            className="rpg-input w-full text-lg"
          />
        </div>
        
        {/* Class Selection */}
        <div className="rpg-card p-6 mb-6">
          <label className="block text-rpg-gold font-medieval text-lg mb-4">
            Choose Your Class
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {classes.map((cls) => {
              const Icon = cls.icon
              const isSelected = selectedClass?.name === cls.name
              
              return (
                <motion.button
                  key={cls.name}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setSelectedClass(cls)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    isSelected
                      ? 'border-rpg-accent bg-rpg-accent/20'
                      : 'border-gray-700 hover:border-gray-500'
                  }`}
                  style={isSelected ? { boxShadow: `0 0 20px ${cls.color}40` } : {}}
                >
                  <Icon 
                    size={32} 
                    className="mx-auto mb-2"
                    style={{ color: cls.color }}
                  />
                  <div className="font-semibold">{cls.name}</div>
                  <div className="text-xs text-gray-400">{cls.desc}</div>
                </motion.button>
              )
            })}
          </div>
        </div>
        
        {/* Race Selection */}
        <div className="rpg-card p-6 mb-6">
          <label className="block text-rpg-gold font-medieval text-lg mb-4">
            Choose Your Race
          </label>
          <div className="flex flex-wrap gap-2">
            {races.map((race) => (
              <motion.button
                key={race}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedRace(race)}
                className={`px-4 py-2 rounded-lg border transition-all ${
                  selectedRace === race
                    ? 'border-rpg-gold bg-rpg-gold/20 text-rpg-gold'
                    : 'border-gray-600 hover:border-gray-400'
                }`}
              >
                {race}
              </motion.button>
            ))}
          </div>
        </div>
        
        {/* Dice Roller Demo */}
        <div className="rpg-card p-6 mb-6">
          <button
            onClick={() => setShowDice(!showDice)}
            className="text-rpg-gold font-medieval hover:text-rpg-accent transition"
          >
            🎲 Try the Dice Roller
          </button>
          {showDice && <DiceRoller />}
        </div>
        
        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-6 text-red-400"
          >
            {error}
          </motion.div>
        )}
        
        {/* Create Button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleCreate}
          disabled={!name || !selectedClass || isLoading}
          className="w-full rpg-button text-xl py-4 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin h-6 w-6 mr-3" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Creating...
            </span>
          ) : (
            '🎲 Begin Your Adventure!'
          )}
        </motion.button>
      </motion.div>
    </div>
  )
}
