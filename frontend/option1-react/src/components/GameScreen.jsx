import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Swords, Map, User, Backpack, LogOut, Skull, Heart, Shield, Zap, Save, FolderOpen, Compass, X, Package, Scroll, CheckCircle, Circle, Moon, Sun, Star, ShoppingBag, Users, Target, Sparkles, Scale } from 'lucide-react'
import { useGameStore } from '../store/gameStore'
import WorldMap from './WorldMap'
import ReputationPanel from './ReputationPanel'
import ChoicesPanel from './ChoicesPanel'
import QuestJournal from './QuestJournal'

export default function GameScreen() {
  const [input, setInput] = useState('')
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [showLoadModal, setShowLoadModal] = useState(false)
  const [showWorldMap, setShowWorldMap] = useState(false)
  const [showInventory, setShowInventory] = useState(false)
  const [showQuests, setShowQuests] = useState(false)
  const [showShop, setShowShop] = useState(false)
  const [showParty, setShowParty] = useState(false)
  const [showRest, setShowRest] = useState(false)
  const [showReputation, setShowReputation] = useState(false)
  const [showChoices, setShowChoices] = useState(false)
  const [saves, setSaves] = useState([])
  const [activeTab, setActiveTab] = useState('chat')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  
  const { 
    character, 
    messages, 
    sendActionStreaming, 
    isLoading, 
    sessionId,
    currentLocation,
    inCombat,
    quests,
    saveGame,
    loadGame,
    listSaves,
    endSession,
    // New combat functions
    combatStatus,
    getCombatStatus,
    combatAttack,
    combatDefend,
    combatFlee,
    // Character functions
    levelUp,
    rest,
    // Inventory functions
    useItem,
    equipItem,
    // Shop functions
    shopInventory,
    browseShop,
    buyItem,
    sellItem,
    // Party functions
    party,
    availableRecruits,
    getParty,
    recruitMember,
    // Location functions
    scanLocation,
    locationDetails
  } = useGameStore()
  
  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Refocus input when loading completes
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus()
    }
  }, [isLoading])

  // Fetch combat status when entering combat
  useEffect(() => {
    if (inCombat) {
      getCombatStatus()
    }
  }, [inCombat])
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      sendActionStreaming(input.trim())
      setInput('')
      // Maintain focus on input after submission
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }
  
    // Check if can level up
  const XP_THRESHOLDS = { 1: 0, 2: 100, 3: 300, 4: 600, 5: 1000 }
  const currentXP = character?.experience ?? character?.xp ?? 0
  const lvl = character?.level || 1
  const nextThreshold = XP_THRESHOLDS[lvl + 1] || XP_THRESHOLDS[5]
  const canLevelUp = lvl < 5 && currentXP >= nextThreshold
  
  const quickActions = inCombat ? [
    { label: '⚔️ Attack', action: 'attack', handler: () => combatAttack() },
    { label: '🛡️ Defend', action: 'defend', handler: () => combatDefend() },
    { label: '🏃 Flee', action: 'flee', handler: () => combatFlee() },
  ] : [
    { label: '👀 Look around', action: 'look around' },
    { label: '🗺️ World Map', action: 'travel', special: 'map' },
    { label: '🎒 Inventory', action: 'inventory', special: 'inventory' },
    { label: '📜 Quests', action: 'quests', special: 'quests' },
    { label: '🛒 Shop', action: 'shop', special: 'shop' },
    { label: '👥 Party', action: 'party', special: 'party' },
    { label: '⭐ Reputation', action: 'reputation', special: 'reputation' },
    { label: '⚖️ Choices', action: 'choices', special: 'choices' },
  ]
  
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* World Map Modal */}
      <WorldMap isOpen={showWorldMap} onClose={() => setShowWorldMap(false)} />
      
      {/* Inventory Modal */}
      <AnimatePresence>
        {showInventory && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setShowInventory(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="rpg-card max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <h2 className="text-xl font-medieval text-rpg-gold flex items-center gap-2">
                  <Backpack size={24} /> Inventory
                </h2>
                <button
                  onClick={() => setShowInventory(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <X size={24} />
                </button>
              </div>
              
              <div className="p-4">
                {/* Gold Display */}
                <div className="text-center mb-4 p-3 bg-rpg-dark/50 rounded-lg border border-rpg-gold/30">
                  <span className="text-rpg-gold font-medieval text-lg">💰 {character?.gold || 0} Gold</span>
                </div>
                
                {/* Items Grid */}
                {character?.inventory && character.inventory.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {character.inventory.map((item, index) => (
                      <div
                        key={index}
                        className={`p-3 bg-rpg-dark/50 rounded-lg border transition ${
                          (item.name.toLowerCase() === character.weapon?.toLowerCase() || 
                           item.name.toLowerCase() === character.equipped_armor?.toLowerCase())
                            ? 'border-rpg-gold/70 ring-1 ring-rpg-gold/30' 
                            : 'border-gray-700 hover:border-rpg-primary/50'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded bg-rpg-surface flex items-center justify-center text-xl shrink-0">
                            {item.item_type === 'weapon' && '⚔️'}
                            {item.item_type === 'armor' && '🛡️'}
                            {item.item_type === 'consumable' && '🧪'}
                            {item.item_type === 'quest' && '📜'}
                            {item.item_type === 'misc' && '📦'}
                            {!item.item_type && '📦'}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-rpg-gold truncate">{item.name}</span>
                              {item.quantity > 1 && (
                                <span className="text-xs bg-rpg-primary/30 px-1.5 py-0.5 rounded">x{item.quantity}</span>
                              )}
                              {(item.name.toLowerCase() === character.weapon?.toLowerCase() || 
                                item.name.toLowerCase() === character.equipped_armor?.toLowerCase()) && (
                                <span className="text-xs bg-green-600/40 text-green-300 px-1.5 py-0.5 rounded border border-green-500/50">✓ Equipped</span>
                              )}
                            </div>
                            <p className="text-xs text-rpg-text-secondary mt-1">{item.description}</p>
                            <div className="flex gap-2 mt-2 text-xs">
                              {item.damage_dice && (
                                <span className="text-red-400">⚔️ {item.damage_dice}</span>
                              )}
                              {item.ac_bonus && (
                                <span className="text-blue-400">🛡️ +{item.ac_bonus} AC</span>
                              )}
                              {item.heal_amount && (
                                <span className="text-green-400">💚 {item.heal_amount}</span>
                              )}
                              {item.value > 0 && (
                                <span className="text-rpg-gold">💰 {item.value}g</span>
                              )}
                            </div>
                            {/* Use/Equip buttons */}
                            <div className="flex gap-2 mt-2">
                              {(item.item_type === 'consumable' || item.heal_amount) && (
                                <button
                                  onClick={() => useItem(item.name)}
                                  disabled={isLoading}
                                  className="px-2 py-1 text-xs bg-green-600/20 border border-green-500 text-green-400 rounded hover:bg-green-600/40 transition disabled:opacity-50"
                                >
                                  Use
                                </button>
                              )}
                              {(item.item_type === 'weapon' || item.item_type === 'armor' || item.damage_dice || item.ac_bonus) && (
                                <button
                                  onClick={() => equipItem(item.name)}
                                  disabled={isLoading}
                                  className="px-2 py-1 text-xs bg-blue-600/20 border border-blue-500 text-blue-400 rounded hover:bg-blue-600/40 transition disabled:opacity-50"
                                >
                                  Equip
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-rpg-text-secondary">
                    <Package size={48} className="mx-auto mb-2 opacity-50" />
                    <p>Your inventory is empty</p>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Shop Modal */}
      <AnimatePresence>
        {showShop && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setShowShop(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="rpg-card max-w-3xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <h2 className="text-xl font-medieval text-rpg-gold flex items-center gap-2">
                  <ShoppingBag size={24} /> Shop
                </h2>
                <div className="flex items-center gap-4">
                  <span className="text-rpg-gold">💰 {character?.gold || 0} Gold</span>
                  <button
                    onClick={() => setShowShop(false)}
                    className="text-gray-400 hover:text-white transition"
                  >
                    <X size={24} />
                  </button>
                </div>
              </div>
              
              <div className="p-4">
                {shopInventory ? (
                  <div className="space-y-6">
                    {/* Items For Sale */}
                    <div>
                      <h3 className="text-lg font-semibold text-rpg-primary mb-3">🛒 For Sale</h3>
                      {shopInventory.shop_items && shopInventory.shop_items.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {shopInventory.shop_items.map((item, idx) => (
                            <div key={idx} className="p-3 bg-rpg-dark/50 rounded-lg border border-gray-700 flex items-center justify-between">
                              <div>
                                <span className="text-rpg-gold font-semibold">{item.name}</span>
                                <p className="text-sm text-rpg-text-secondary">{item.type}</p>
                              </div>
                              <button
                                onClick={() => buyItem(item.name)}
                                disabled={isLoading || (character?.gold || 0) < item.price}
                                className="px-3 py-1 bg-green-600/20 border border-green-500 text-green-400 rounded hover:bg-green-600/40 transition disabled:opacity-50 text-sm"
                              >
                                Buy ({item.price}g)
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-rpg-text-secondary">No items for sale</p>
                      )}
                    </div>
                    
                    {/* Your Items to Sell */}
                    <div>
                      <h3 className="text-lg font-semibold text-rpg-primary mb-3">💰 Sell Your Items</h3>
                      {character?.inventory && character.inventory.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {character.inventory.map((item, idx) => (
                            <div key={idx} className="p-3 bg-rpg-dark/50 rounded-lg border border-gray-700 flex items-center justify-between">
                              <span className="text-rpg-gold">{typeof item === 'string' ? item : item.name}</span>
                              <button
                                onClick={() => sellItem(typeof item === 'string' ? item : item.name)}
                                disabled={isLoading}
                                className="px-3 py-1 bg-yellow-600/20 border border-yellow-500 text-yellow-400 rounded hover:bg-yellow-600/40 transition disabled:opacity-50 text-sm"
                              >
                                Sell
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-rpg-text-secondary">No items to sell</p>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-rpg-text-secondary">
                    <ShoppingBag size={48} className="mx-auto mb-2 opacity-50" />
                    <p>Loading shop...</p>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Party Modal */}
      <AnimatePresence>
        {showParty && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setShowParty(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="rpg-card max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <h2 className="text-xl font-medieval text-rpg-gold flex items-center gap-2">
                  <Users size={24} /> Party
                </h2>
                <button
                  onClick={() => setShowParty(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <X size={24} />
                </button>
              </div>
              
              <div className="p-4 space-y-6">
                {/* Current Party */}
                <div>
                  <h3 className="text-lg font-semibold text-rpg-primary mb-3">👥 Party Members</h3>
                  {party && party.length > 0 ? (
                    <div className="space-y-3">
                      {party.map((member, idx) => (
                        <div key={idx} className="p-3 bg-rpg-dark/50 rounded-lg border border-gray-700">
                          <div className="flex items-center justify-between">
                            <span className="text-rpg-gold font-semibold">{member.name}</span>
                            <span className="text-sm text-rpg-text-secondary">{member.class || member.role}</span>
                          </div>
                          {member.hp && (
                            <div className="mt-2 text-sm">
                              <span className="text-red-400">❤️ {member.hp}/{member.max_hp || member.hp}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-rpg-text-secondary">You're adventuring alone</p>
                  )}
                </div>
                
                {/* Available Recruits */}
                <div>
                  <h3 className="text-lg font-semibold text-rpg-primary mb-3">🆕 Available Recruits</h3>
                  {availableRecruits && availableRecruits.length > 0 ? (
                    <div className="space-y-3">
                      {availableRecruits.map((npc, idx) => (
                        <div key={idx} className="p-3 bg-rpg-dark/50 rounded-lg border border-gray-700 flex items-center justify-between">
                          <div>
                            <span className="text-rpg-gold font-semibold">{npc.name}</span>
                            <p className="text-sm text-rpg-text-secondary">{npc.description || npc.class}</p>
                            {npc.requirement && (
                              <p className="text-xs text-yellow-400 mt-1">Requires: {npc.requirement}</p>
                            )}
                          </div>
                          <button
                            onClick={() => recruitMember(npc.name)}
                            disabled={isLoading || !npc.can_recruit}
                            className="px-3 py-1 bg-blue-600/20 border border-blue-500 text-blue-400 rounded hover:bg-blue-600/40 transition disabled:opacity-50 text-sm"
                          >
                            Recruit
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-rpg-text-secondary">No one available to recruit here</p>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Rest Modal */}
      <AnimatePresence>
        {showRest && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setShowRest(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="rpg-card max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <h2 className="text-xl font-medieval text-rpg-gold flex items-center gap-2">
                  <Moon size={24} /> Rest
                </h2>
                <button
                  onClick={() => setShowRest(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <X size={24} />
                </button>
              </div>
              
              <div className="p-4 space-y-4">
                <button
                  onClick={async () => { await rest('short'); setShowRest(false) }}
                  disabled={isLoading}
                  className="w-full p-4 bg-blue-600/20 border border-blue-500 rounded-lg hover:bg-blue-600/40 transition disabled:opacity-50"
                >
                  <div className="flex items-center gap-3">
                    <Sun size={24} className="text-blue-400" />
                    <div className="text-left">
                      <div className="font-semibold text-blue-300">Short Rest</div>
                      <div className="text-sm text-rpg-text-secondary">Recover some HP (1 hour)</div>
                    </div>
                  </div>
                </button>
                
                <button
                  onClick={async () => { await rest('long'); setShowRest(false) }}
                  disabled={isLoading}
                  className="w-full p-4 bg-purple-600/20 border border-purple-500 rounded-lg hover:bg-purple-600/40 transition disabled:opacity-50"
                >
                  <div className="flex items-center gap-3">
                    <Moon size={24} className="text-purple-400" />
                    <div className="text-left">
                      <div className="font-semibold text-purple-300">Long Rest</div>
                      <div className="text-sm text-rpg-text-secondary">Fully restore HP (8 hours)</div>
                    </div>
                  </div>
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Sidebar - Character Info */}
      <motion.aside
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-full md:w-64 md:h-screen md:sticky md:top-0 bg-rpg-dark/80 border-b md:border-r md:border-b-0 border-gray-700 p-4 overflow-y-auto"
      >
        {character && (
          <>
            {/* Character Portrait Placeholder */}
            <div className="rpg-card p-4 mb-4 text-center">
              <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-rpg-primary to-rpg-accent flex items-center justify-center text-3xl mb-2">
                {(character.char_class || character.class) === 'Fighter' && '⚔️'}
                {(character.char_class || character.class) === 'Wizard' && '🧙'}
                {(character.char_class || character.class) === 'Rogue' && '🗡️'}
                {(character.char_class || character.class) === 'Cleric' && '✝️'}
                {(character.char_class || character.class) === 'Ranger' && '🏹'}
                {(character.char_class || character.class) === 'Barbarian' && '🪓'}
                {!['Fighter', 'Wizard', 'Rogue', 'Cleric', 'Ranger', 'Barbarian'].includes(character.char_class || character.class) && '👤'}
              </div>
              <h2 className="font-medieval text-xl text-rpg-gold">{character.name}</h2>
              <p className="text-sm text-rpg-text-secondary">{character.race} {character.char_class || character.class}</p>
              <p className="text-sm text-rpg-primary">Level {character.level || 1}</p>
            </div>
            
            {/* Current Location */}
            {currentLocation && (
              <div className="text-center mb-4 p-2 bg-rpg-dark/50 rounded-lg border border-rpg-primary/20">
                <span className="text-rpg-text-secondary text-sm">📍 Location:</span>
                <p className="text-rpg-gold font-medieval">{currentLocation}</p>
              </div>
            )}
            
            {/* Combat Indicator */}
            {inCombat && (
              <div className="mb-4 p-3 bg-rpg-health/20 rounded-lg border border-rpg-health">
                <div className="text-center mb-2">
                  <span className="text-rpg-health font-bold animate-pulse">⚔️ IN COMBAT!</span>
                </div>
                {combatStatus?.enemies && combatStatus.enemies.length > 0 && (
                  <div className="space-y-2">
                    {combatStatus.enemies.map((enemy, idx) => (
                      <div key={idx} className="flex items-center justify-between text-sm">
                        <span className="text-red-300">{enemy.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-red-500"
                              style={{ width: `${(enemy.current_hp / enemy.max_hp) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400">{enemy.current_hp}/{enemy.max_hp}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Stats */}
            <div className="rpg-card p-4 mb-4 space-y-3">
              {/* HP Bar */}
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="flex items-center gap-1">
                    <Heart size={14} className="text-red-500" /> HP
                  </span>
                  <span>{character.current_hp ?? character.hp ?? character.health ?? 20}/{character.max_hp || 20}</span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ 
                      width: `${((character.current_hp ?? character.hp ?? character.health ?? 20) / (character.max_hp || 20)) * 100}%` 
                    }}
                    className="h-full bg-gradient-to-r from-red-600 to-red-400"
                  />
                </div>
              </div>
              
              {/* XP Bar - thresholds match backend: 100/300/600/1000 */}
              {(() => {
                const XP_THRESHOLDS = { 1: 0, 2: 100, 3: 300, 4: 600, 5: 1000 }
                const currentXP = character.experience ?? character.xp ?? 0
                const level = character.level || 1
                const currentThreshold = XP_THRESHOLDS[level] || 0
                const nextThreshold = XP_THRESHOLDS[level + 1] || XP_THRESHOLDS[5]
                const xpInLevel = currentXP - currentThreshold
                const xpNeeded = nextThreshold - currentThreshold
                const progress = level >= 5 ? 100 : (xpInLevel / xpNeeded) * 100
                return (
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <Zap size={14} className="text-yellow-500" /> XP
                      </span>
                      <span>{currentXP}{level < 5 ? `/${nextThreshold}` : ' (MAX)'}</span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(progress, 100)}%` }}
                        className="h-full bg-gradient-to-r from-yellow-600 to-yellow-400"
                      />
                    </div>
                  </div>
                )
              })()}
              
              {/* Combat Stats */}
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
              
              {/* Equipped Gear */}
              <div className="text-xs text-rpg-text-secondary space-y-1">
                <div className="flex items-center gap-1">
                  <span className="text-red-400">⚔️</span>
                  <span>{character.weapon || 'Unarmed'}</span>
                </div>
                {character.equipped_armor && (
                  <div className="flex items-center gap-1">
                    <span className="text-blue-400">🛡️</span>
                    <span>{character.equipped_armor}</span>
                  </div>
                )}
              </div>
              
              {/* Ability Scores */}
              <div className="border-t border-gray-600 pt-2 mt-2">
                <div className="text-xs text-rpg-text-secondary mb-2 text-center">Ability Scores</div>
                <div className="grid grid-cols-3 gap-1 text-xs">
                  <div className="text-center p-1 bg-rpg-dark/50 rounded">
                    <div className="text-red-400 font-bold">STR</div>
                    <div>{character.strength || 10}</div>
                  </div>
                  <div className="text-center p-1 bg-rpg-dark/50 rounded">
                    <div className="text-green-400 font-bold">DEX</div>
                    <div>{character.dexterity || 10}</div>
                  </div>
                  <div className="text-center p-1 bg-rpg-dark/50 rounded">
                    <div className="text-orange-400 font-bold">CON</div>
                    <div>{character.constitution || 10}</div>
                  </div>
                  <div className="text-center p-1 bg-rpg-dark/50 rounded">
                    <div className="text-blue-400 font-bold">INT</div>
                    <div>{character.intelligence || 10}</div>
                  </div>
                  <div className="text-center p-1 bg-rpg-dark/50 rounded">
                    <div className="text-purple-400 font-bold">WIS</div>
                    <div>{character.wisdom || 10}</div>
                  </div>
                  <div className="text-center p-1 bg-rpg-dark/50 rounded">
                    <div className="text-pink-400 font-bold">CHA</div>
                    <div>{character.charisma || 10}</div>
                  </div>
                </div>
              </div>
              
              {/* Gold */}
              <div className="text-rpg-gold text-center font-medieval">
                💰 {character.gold || 0} Gold
              </div>
            </div>

            {/* Rest & Level Up Buttons */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setShowRest(true)}
                disabled={inCombat}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-purple-500 text-purple-400 rounded-lg hover:bg-purple-500/20 transition text-sm disabled:opacity-50"
              >
                <Moon size={16} /> Rest
              </button>
              {canLevelUp && (
                <button
                  onClick={levelUp}
                  className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-yellow-500 text-yellow-400 rounded-lg hover:bg-yellow-500/20 transition text-sm animate-pulse"
                >
                  <Sparkles size={16} /> Level Up!
                </button>
              )}
            </div>
            
            {/* Save/Load Buttons */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setShowSaveModal(true)}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-rpg-primary text-rpg-primary rounded-lg hover:bg-rpg-primary/20 transition text-sm"
              >
                <Save size={16} /> Save
              </button>
              <button
                onClick={async () => {
                  const savedGames = await listSaves()
                  setSaves(savedGames)
                  setShowLoadModal(true)
                }}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-rpg-gold text-rpg-gold rounded-lg hover:bg-rpg-gold/20 transition text-sm"
              >
                <FolderOpen size={16} /> Load
              </button>
            </div>
            
            {/* Quit Button */}
            <button
              onClick={endSession}
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
            { id: 'map', icon: Map, label: 'Map', action: () => setShowWorldMap(true) },
            { id: 'inventory', icon: Backpack, label: 'Items', action: () => setShowInventory(true) },
            { id: 'quests', icon: Scroll, label: 'Quests', action: () => setShowQuests(true) },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => tab.action ? tab.action() : setActiveTab(tab.id)}
              className={`flex-1 py-3 flex items-center justify-center gap-2 transition ${
                activeTab === tab.id 
                  ? 'text-rpg-gold border-b-2 border-rpg-gold' 
                  : 'text-gray-400'
              }`}
            >
              <tab.icon size={18} />
              <span className="text-xs">{tab.label}</span>
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
                className={`flex ${msg.type === 'player' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-lg ${
                    msg.type === 'player'
                      ? 'bg-rpg-player-bubble border border-rpg-primary/30 rounded-br-none'
                      : 'bg-rpg-dm-bubble border border-rpg-surface rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {/* Streaming indicator */}
                  {msg.isStreaming && (
                    <span className="inline-flex gap-1 ml-2 align-middle">
                      <span className="w-1.5 h-1.5 bg-rpg-gold rounded-full animate-pulse" />
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {/* Loading indicator - only show when waiting for first chunk */}
          {isLoading && messages.length > 0 && !messages[messages.length - 1]?.isStreaming && (
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
              onClick={() => {
                if (qa.handler) qa.handler()
                else if (qa.special === 'map') setShowWorldMap(true)
                else if (qa.special === 'inventory') setShowInventory(true)
                else if (qa.special === 'quests') setShowQuests(true)
                else if (qa.special === 'shop') { browseShop(); setShowShop(true) }
                else if (qa.special === 'party') { getParty(); setShowParty(true) }
                else if (qa.special === 'reputation') setShowReputation(true)
                else if (qa.special === 'choices') setShowChoices(true)
                else sendActionStreaming(qa.action)
              }}
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
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="What do you do?"
              className="rpg-input flex-1"
              disabled={isLoading}
              autoFocus
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
      
      {/* Save Modal */}
      <AnimatePresence>
        {showSaveModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
            onClick={() => setShowSaveModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="rpg-card p-6 max-w-md w-full"
              onClick={e => e.stopPropagation()}
            >
              <h2 className="text-2xl font-medieval text-rpg-gold mb-4">💾 Save Game</h2>
              <div className="space-y-3">
                {[1, 2, 3].map(slot => (
                  <button
                    key={slot}
                    onClick={async () => {
                      const result = await saveGame(slot, `Slot ${slot} - ${character?.name || 'Hero'}`)
                      if (result.success) {
                        setShowSaveModal(false)
                      } else {
                        alert(result.message)
                      }
                    }}
                    className="w-full p-4 text-left border border-rpg-primary/30 rounded-lg hover:bg-rpg-primary/20 transition"
                  >
                    <div className="font-semibold">Slot {slot}</div>
                    <div className="text-sm text-rpg-text-secondary">Quick save to slot {slot}</div>
                  </button>
                ))}
              </div>
              <button
                onClick={() => setShowSaveModal(false)}
                className="w-full mt-4 p-2 border border-gray-600 rounded-lg hover:bg-gray-700 transition"
              >
                Cancel
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Load Modal */}
      <AnimatePresence>
        {showLoadModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
            onClick={() => setShowLoadModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="rpg-card p-6 max-w-md w-full max-h-[80vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <h2 className="text-2xl font-medieval text-rpg-gold mb-4">📂 Load Game</h2>
              {saves.length === 0 ? (
                <p className="text-rpg-text-secondary text-center py-8">No saved games found</p>
              ) : (
                <div className="space-y-3">
                  {saves.map((save, idx) => (
                    <button
                      key={idx}
                      onClick={async () => {
                        const result = await loadGame(save.filepath)
                        if (result.success) {
                          setShowLoadModal(false)
                        }
                      }}
                      className="w-full p-4 text-left border border-rpg-gold/30 rounded-lg hover:bg-rpg-gold/20 transition"
                    >
                      <div className="font-semibold text-rpg-gold">{save.character_name || 'Unknown Hero'}</div>
                      <div className="text-sm">Level {save.character_level || 1} {save.character_class || 'Adventurer'}</div>
                      <div className="text-xs text-rpg-text-secondary mt-1">{save.description || 'No description'}</div>
                    </button>
                  ))}
                </div>
              )}
              <button
                onClick={() => setShowLoadModal(false)}
                className="w-full mt-4 p-2 border border-gray-600 rounded-lg hover:bg-gray-700 transition"
              >
                Cancel
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reputation Panel */}
      <ReputationPanel
        show={showReputation}
        onClose={() => setShowReputation(false)}
        sessionId={sessionId}
      />

      {/* Choices Panel */}
      <ChoicesPanel
        show={showChoices}
        onClose={() => setShowChoices(false)}
        sessionId={sessionId}
        onMakeChoice={(result) => {
          // Optionally refresh game state after choice
          console.log('Choice made:', result)
        }}
      />

      {/* Quest Journal */}
      <QuestJournal
        show={showQuests}
        onClose={() => setShowQuests(false)}
        sessionId={sessionId}
      />
    </div>
  )
}
