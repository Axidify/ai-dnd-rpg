import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Sword, Sparkles, Crosshair, Cross, Target, Axe, Shield, Flame, Music, Hand, Leaf, Star, Map } from 'lucide-react'
import { useGameStore } from '../store/gameStore'

// All D&D 5e classes matching character.py
const classes = [
  { name: 'Fighter', icon: Sword, desc: 'Master of martial combat', color: '#DC143C' },
  { name: 'Wizard', icon: Sparkles, desc: 'Wielder of arcane magic', color: '#9932CC' },
  { name: 'Rogue', icon: Crosshair, desc: 'Stealthy and cunning', color: '#228B22' },
  { name: 'Cleric', icon: Cross, desc: 'Divine healer and warrior', color: '#D4AF37' },
  { name: 'Ranger', icon: Target, desc: 'Skilled hunter and tracker', color: '#1e88e5' },
  { name: 'Barbarian', icon: Axe, desc: 'Fierce primal warrior', color: '#8B4513' },
  { name: 'Paladin', icon: Shield, desc: 'Holy knight of justice', color: '#FFD700' },
  { name: 'Warlock', icon: Flame, desc: 'Pact-bound spellcaster', color: '#4B0082' },
  { name: 'Bard', icon: Music, desc: 'Magical musician', color: '#FF69B4' },
  { name: 'Monk', icon: Hand, desc: 'Master of martial arts', color: '#708090' },
  { name: 'Druid', icon: Leaf, desc: 'Nature\'s guardian', color: '#32CD32' },
  { name: 'Sorcerer', icon: Star, desc: 'Innate magic wielder', color: '#FF4500' },
]

// All D&D 5e races matching character.py
const races = ['Human', 'Elf', 'Dwarf', 'Halfling', 'Half-Orc', 'Tiefling', 'Dragonborn', 'Gnome', 'Half-Elf']

export default function CharacterCreation() {
  const [name, setName] = useState('')
  const [selectedClass, setSelectedClass] = useState(null)
  const [selectedRace, setSelectedRace] = useState('Human')
  const [selectedScenario, setSelectedScenario] = useState(null)
  
  const { createCharacter, fetchScenarios, scenarios, isLoading, error } = useGameStore()
  
  // Fetch scenarios on mount
  useEffect(() => {
    fetchScenarios()
  }, [fetchScenarios])
  
  const handleCreate = () => {
    if (name && selectedClass) {
      createCharacter(name, selectedClass.name, selectedRace, selectedScenario?.id || null)
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
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
                      ? 'border-rpg-primary bg-rpg-primary/20'
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
        
        {/* Scenario Selection */}
        <div className="rpg-card p-6 mb-6">
          <label className="block text-rpg-gold font-medieval text-lg mb-4">
            <Map size={20} className="inline mr-2" />
            Choose Your Adventure
          </label>
          <div className="space-y-3">
            {/* Free Play option */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSelectedScenario(null)}
              className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                !selectedScenario
                  ? 'border-rpg-primary bg-rpg-primary/20'
                  : 'border-gray-700 hover:border-gray-500'
              }`}
            >
              <div className="font-semibold text-rpg-gold">🌍 Free Adventure</div>
              <div className="text-sm text-rpg-text-secondary">Explore Willowbrook village freely</div>
            </motion.button>
            
            {/* Available scenarios */}
            {scenarios.map((scenario) => (
              <motion.button
                key={scenario.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedScenario(scenario)}
                className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                  selectedScenario?.id === scenario.id
                    ? 'border-rpg-primary bg-rpg-primary/20'
                    : 'border-gray-700 hover:border-gray-500'
                }`}
              >
                <div className="font-semibold text-rpg-gold">🏰 {scenario.name}</div>
                <div className="text-sm text-rpg-text-secondary">{scenario.description}</div>
                {scenario.duration && (
                  <div className="text-xs text-rpg-primary mt-1">⏱️ {scenario.duration}</div>
                )}
              </motion.button>
            ))}
          </div>
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
