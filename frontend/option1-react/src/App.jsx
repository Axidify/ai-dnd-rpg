import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import HomeScreen from './components/HomeScreen'
import CharacterCreation from './components/CharacterCreation'
import GameScreen from './components/GameScreen'
import { useGameStore } from './store/gameStore'

// Quick cross-fade between screens (matches modal timing)
const SCREEN_FADE = { duration: 0.18 }

function App() {
  const [screen, setScreen] = useState('home')
  const character = useGameStore((s) => s.character)

  useEffect(() => {
    if (character) {
      setScreen('game')
    } else if (screen === 'game') {
      // No character (session ended or state reset): never leave a blank screen
      setScreen('home')
    }
  }, [character, screen])

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
            transition={SCREEN_FADE}
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
            transition={SCREEN_FADE}
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
            transition={SCREEN_FADE}
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
