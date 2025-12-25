import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Users, X, Star, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'

/**
 * ReputationPanel - Display NPC relationships and disposition levels
 * 
 * Disposition Tiers:
 * - 🔴 Hostile (<-50): Won't trade, may attack
 * - 🟠 Unfriendly (-50 to -10): Higher prices
 * - 🟡 Neutral (-10 to +10): Normal prices
 * - 🟢 Friendly (+10 to +50): Discounts available
 * - 💚 Trusted (>+50): Best prices, special options
 */

// Disposition tier colors and labels
const getDispositionStyle = (level) => {
  switch(level) {
    case 'hostile':
      return { color: 'text-red-500', bg: 'bg-red-900/20', border: 'border-red-500', emoji: '🔴' }
    case 'unfriendly':
      return { color: 'text-orange-500', bg: 'bg-orange-900/20', border: 'border-orange-500', emoji: '🟠' }
    case 'neutral':
      return { color: 'text-yellow-500', bg: 'bg-yellow-900/20', border: 'border-yellow-500', emoji: '🟡' }
    case 'friendly':
      return { color: 'text-green-500', bg: 'bg-green-900/20', border: 'border-green-500', emoji: '🟢' }
    case 'trusted':
      return { color: 'text-emerald-400', bg: 'bg-emerald-900/20', border: 'border-emerald-400', emoji: '💚' }
    default:
      return { color: 'text-gray-500', bg: 'bg-gray-900/20', border: 'border-gray-500', emoji: '⚪' }
  }
}

// Price modifier display
const getPriceModifier = (modifier) => {
  if (modifier > 1) return { text: `+${Math.round((modifier - 1) * 100)}%`, color: 'text-red-400' }
  if (modifier < 1) return { text: `-${Math.round((1 - modifier) * 100)}%`, color: 'text-green-400' }
  return { text: 'Normal', color: 'text-gray-400' }
}

export default function ReputationPanel({ show, onClose, sessionId, apiUrl = 'http://localhost:5000' }) {
  const [reputations, setReputations] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [expandedNpc, setExpandedNpc] = useState(null)
  const [npcDetails, setNpcDetails] = useState({})

  // Fetch reputation data when panel opens
  useEffect(() => {
    if (show && sessionId) {
      fetchReputations()
    }
  }, [show, sessionId])

  const fetchReputations = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${apiUrl}/api/reputation`, {
        headers: { 'X-Session-ID': sessionId }
      })
      if (!response.ok) throw new Error('Failed to fetch reputations')
      const data = await response.json()
      setReputations(data.npcs || [])
      setSummary(data.summary || null)
    } catch (err) {
      setError(err.message)
      setReputations([])
    } finally {
      setLoading(false)
    }
  }

  const fetchNpcDetails = async (npcId) => {
    if (npcDetails[npcId]) {
      setExpandedNpc(expandedNpc === npcId ? null : npcId)
      return
    }
    
    try {
      const response = await fetch(`${apiUrl}/api/reputation/${npcId}`, {
        headers: { 'X-Session-ID': sessionId }
      })
      if (response.ok) {
        const data = await response.json()
        setNpcDetails(prev => ({ ...prev, [npcId]: data }))
        setExpandedNpc(npcId)
      }
    } catch (err) {
      console.error('Failed to fetch NPC details:', err)
    }
  }

  if (!show) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="rpg-card max-w-2xl w-full max-h-[80vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700 sticky top-0 bg-rpg-card z-10">
            <h2 className="text-xl font-medieval text-rpg-gold flex items-center gap-2">
              <Star size={24} /> Reputation
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition"
            >
              <X size={24} />
            </button>
          </div>

          <div className="p-4 space-y-4">
            {/* Summary Stats */}
            {summary && (
              <div className="grid grid-cols-5 gap-2 p-3 bg-rpg-dark/50 rounded-lg border border-gray-700">
                <div className="text-center">
                  <div className="text-lg font-bold text-red-500">{summary.hostile || 0}</div>
                  <div className="text-xs text-rpg-text-secondary">Hostile</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-orange-500">{summary.unfriendly || 0}</div>
                  <div className="text-xs text-rpg-text-secondary">Unfriendly</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-yellow-500">{summary.neutral || 0}</div>
                  <div className="text-xs text-rpg-text-secondary">Neutral</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-500">{summary.friendly || 0}</div>
                  <div className="text-xs text-rpg-text-secondary">Friendly</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-emerald-400">{summary.trusted || 0}</div>
                  <div className="text-xs text-rpg-text-secondary">Trusted</div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="text-center py-8">
                <Users size={48} className="mx-auto mb-2 opacity-50 animate-pulse" />
                <p className="text-rpg-text-secondary">Loading reputation data...</p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-4 text-red-400">
                <AlertCircle size={32} className="mx-auto mb-2" />
                <p>{error}</p>
                <button
                  onClick={fetchReputations}
                  className="mt-2 px-4 py-1 bg-red-600/20 border border-red-500 rounded hover:bg-red-600/40 transition"
                >
                  Retry
                </button>
              </div>
            )}

            {/* NPC List */}
            {!loading && !error && reputations.length > 0 && (
              <div className="space-y-2">
                {reputations.map((npc) => {
                  const style = getDispositionStyle(npc.level)
                  const priceInfo = getPriceModifier(npc.price_modifier || 1)
                  const isExpanded = expandedNpc === npc.npc_id
                  const details = npcDetails[npc.npc_id]

                  return (
                    <div key={npc.npc_id} className={`rounded-lg border ${style.border} ${style.bg}`}>
                      <div
                        className="p-3 cursor-pointer flex items-center justify-between"
                        onClick={() => fetchNpcDetails(npc.npc_id)}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{style.emoji}</span>
                          <div>
                            <div className="font-semibold text-rpg-gold">{npc.name}</div>
                            <div className="text-sm text-rpg-text-secondary flex items-center gap-2">
                              <span className={style.color}>{npc.label}</span>
                              {npc.role && <span className="text-gray-500">• {npc.role}</span>}
                              {npc.location && <span className="text-gray-500">@ {npc.location}</span>}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {npc.can_trade !== undefined && !npc.can_trade && (
                            <span className="text-xs text-red-400 border border-red-500 px-2 py-1 rounded">
                              Won't Trade
                            </span>
                          )}
                          {npc.price_modifier && npc.price_modifier !== 1 && (
                            <span className={`text-xs ${priceInfo.color}`}>
                              Prices: {priceInfo.text}
                            </span>
                          )}
                          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </div>
                      </div>

                      {/* Expanded Details */}
                      <AnimatePresence>
                        {isExpanded && details && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-t border-gray-700"
                          >
                            <div className="p-3 space-y-2 text-sm">
                              {details.description && (
                                <p className="text-rpg-text-secondary">{details.description}</p>
                              )}
                              {details.disposition !== undefined && (
                                <div className="flex items-center gap-2">
                                  <span className="text-gray-400">Disposition:</span>
                                  <span className={style.color}>{details.disposition}</span>
                                </div>
                              )}
                              {details.available_skill_checks && details.available_skill_checks.length > 0 && (
                                <div>
                                  <span className="text-gray-400">Available actions:</span>
                                  <ul className="ml-4 mt-1 space-y-1">
                                    {details.available_skill_checks.map((check, idx) => (
                                      <li key={idx} className="text-rpg-primary">
                                        • {check.description} ({check.skill} DC {check.dc})
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && reputations.length === 0 && (
              <div className="text-center py-8 text-rpg-text-secondary">
                <Users size={48} className="mx-auto mb-2 opacity-50" />
                <p>No NPCs encountered yet</p>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
