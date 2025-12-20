import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import CharacterCreation from './components/CharacterCreation'
import GameScreen from './components/GameScreen'
import { useGameStore } from './store/gameStore'

function App() {
  const { character } = useGameStore()

  return (
    <div className="min-h-screen bg-rpg-dark text-white">
      <AnimatePresence mode="wait">
        {!character ? (
          <motion.div
            key="creation"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <CharacterCreation />
          </motion.div>
        ) : (
          <motion.div
            key="game"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <GameScreen />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
