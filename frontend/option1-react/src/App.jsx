import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import HomeScreen from './components/HomeScreen'
import CharacterCreation from './components/CharacterCreation'
import GameScreen from './components/GameScreen'
import { useGameStore } from './store/gameStore'

function App() {
  const [screen, setScreen] = useState('home')
  const character = useGameStore((s) => s.character)

  useEffect(() => {
    if (character) {
      setScreen('game')
    }
  }, [character])

  const handleLeaveGame = () => {
    useGameStore.getState().endSession()
    setScreen('home')
  }

  return (
    <div className="atmosphere min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      <AnimatePresence mode="wait">
        {screen === 'home' && (
          <motion.div
            key="home"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <HomeScreen
              onNewGame={() => setScreen('create')}
              onContinue={() => setScreen('game')}
            />
          </motion.div>
        )}
        {screen === 'create' && !character && (
          <motion.div
            key="create"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <CharacterCreation onBack={() => setScreen('home')} />
          </motion.div>
        )}
        {screen === 'game' && character && (
          <motion.div
            key="game"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="min-h-screen"
          >
            <GameScreen onLeaveGame={handleLeaveGame} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
