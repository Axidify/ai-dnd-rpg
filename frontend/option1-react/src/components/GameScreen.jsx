import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Swords, Map, User, Backpack, LogOut, Skull, Heart, Shield, Zap } from 'lucide-react'
import { useGameStore } from '../store/gameStore'
import DiceRoller from './DiceRoller'

export default function GameScreen() {
  const [input, setInput] = useState('')
  const [showDice, setShowDice] = useState(false)
  const [activeTab, setActiveTab] = useState('chat')
  const messagesEndRef = useRef(null)
  
  const { 
    gameState, 
    messages, 
    sendAction, 
    isLoading, 
    sessionId,
    reset 
  } = useGameStore()
  
  const character = gameState?.character
  
  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      sendAction(input.trim())
      setInput('')
    }
  }
  
  const quickActions = [
    { label: 'Look around', action: 'look around' },
    { label: 'Check inventory', action: 'check inventory' },
    { label: 'Rest', action: 'rest' },
  ]
  
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Sidebar - Character Info */}
      <motion.aside
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-full md:w-64 bg-rpg-dark/80 border-b md:border-r md:border-b-0 border-gray-700 p-4"
      >
        {character && (
          <>
            {/* Character Portrait Placeholder */}
            <div className="rpg-card p-4 mb-4 text-center">
              <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-rpg-accent to-purple-800 flex items-center justify-center text-3xl mb-2">
                {character.class === 'Fighter' && '⚔️'}
                {character.class === 'Wizard' && '🧙'}
                {character.class === 'Rogue' && '🗡️'}
                {character.class === 'Cleric' && '✝️'}
                {character.class === 'Ranger' && '🏹'}
                {character.class === 'Barbarian' && '🪓'}
                {!['Fighter', 'Wizard', 'Rogue', 'Cleric', 'Ranger', 'Barbarian'].includes(character.class) && '👤'}
              </div>
              <h2 className="font-medieval text-xl text-rpg-gold">{character.name}</h2>
              <p className="text-sm text-gray-400">{character.race} {character.class}</p>
              <p className="text-sm text-rpg-accent">Level {character.level || 1}</p>
            </div>
            
            {/* Stats */}
            <div className="rpg-card p-4 mb-4 space-y-3">
              {/* HP Bar */}
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="flex items-center gap-1">
                    <Heart size={14} className="text-red-500" /> HP
                  </span>
                  <span>{character.hp || character.health || 20}/{character.max_hp || 20}</span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ 
                      width: `${((character.hp || character.health || 20) / (character.max_hp || 20)) * 100}%` 
                    }}
                    className="h-full bg-gradient-to-r from-red-600 to-red-400"
                  />
                </div>
              </div>
              
              {/* XP Bar */}
              {character.xp !== undefined && (
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="flex items-center gap-1">
                      <Zap size={14} className="text-yellow-500" /> XP
                    </span>
                    <span>{character.xp || 0}/{(character.level || 1) * 100}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ 
                        width: `${((character.xp || 0) / ((character.level || 1) * 100)) * 100}%` 
                      }}
                      className="h-full bg-gradient-to-r from-yellow-600 to-yellow-400"
                    />
                  </div>
                </div>
              )}
              
              {/* Other Stats */}
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex items-center gap-1">
                  <Shield size={14} className="text-blue-400" />
                  <span>AC: {character.armor_class || character.ac || 10}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Swords size={14} className="text-orange-400" />
                  <span>ATK: +{character.attack_bonus || 2}</span>
                </div>
              </div>
              
              {/* Gold */}
              <div className="text-rpg-gold text-center font-medieval">
                💰 {character.gold || 0} Gold
              </div>
            </div>
            
            {/* Dice Roller Toggle */}
            <button
              onClick={() => setShowDice(!showDice)}
              className="w-full rpg-button mb-4"
            >
              🎲 Dice Roller
            </button>
            
            <AnimatePresence>
              {showDice && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="rpg-card p-4 mb-4 overflow-hidden"
                >
                  <DiceRoller />
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Quit Button */}
            <button
              onClick={reset}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-red-500 text-red-400 rounded-lg hover:bg-red-500/20 transition"
            >
              <LogOut size={16} /> Leave Game
            </button>
          </>
        )}
      </motion.aside>
      
      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen md:h-auto">
        {/* Tab Bar (Mobile) */}
        <div className="md:hidden flex border-b border-gray-700">
          {[
            { id: 'chat', icon: Send, label: 'Chat' },
            { id: 'map', icon: Map, label: 'Map' },
            { id: 'inventory', icon: Backpack, label: 'Items' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 flex items-center justify-center gap-2 transition ${
                activeTab === tab.id 
                  ? 'text-rpg-gold border-b-2 border-rpg-gold' 
                  : 'text-gray-400'
              }`}
            >
              <tab.icon size={18} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
        
        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 rpg-scrollbar">
          <AnimatePresence initial={false}>
            {messages.map((msg, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-rpg-accent/30 border border-rpg-accent/50 rounded-br-none'
                      : 'bg-rpg-dark border border-gray-700 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {/* Loading indicator */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-rpg-dark border border-gray-700 rounded-lg rounded-bl-none p-4">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-rpg-gold rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-rpg-gold rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-rpg-gold rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* Quick Actions */}
        <div className="px-4 py-2 flex gap-2 overflow-x-auto">
          {quickActions.map((qa) => (
            <motion.button
              key={qa.label}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => sendAction(qa.action)}
              disabled={isLoading}
              className="px-4 py-2 bg-gray-800 border border-gray-600 rounded-full text-sm whitespace-nowrap hover:border-rpg-gold hover:text-rpg-gold transition disabled:opacity-50"
            >
              {qa.label}
            </motion.button>
          ))}
        </div>
        
        {/* Input Area */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="What do you do?"
              className="rpg-input flex-1"
              disabled={isLoading}
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={isLoading || !input.trim()}
              className="rpg-button px-6 disabled:opacity-50"
            >
              <Send size={20} />
            </motion.button>
          </div>
        </form>
      </main>
    </div>
  )
}
