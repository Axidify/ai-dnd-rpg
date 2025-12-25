import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Scale, X, AlertTriangle, CheckCircle, XCircle, ChevronRight } from 'lucide-react'

/**
 * ChoicesPanel - Display moral choices available to the player
 * 
 * Choice Types:
 * - MORAL: Ethics-based decisions (spare/kill)
 * - NEGOTIATION: Dialogue options with NPCs
 * - STORY: Plot branching points
 */

// Choice type styling
const getChoiceTypeStyle = (type) => {
  switch(type?.toLowerCase()) {
    case 'moral':
      return { color: 'text-purple-400', bg: 'bg-purple-900/20', border: 'border-purple-500', icon: '⚖️' }
    case 'negotiation':
      return { color: 'text-blue-400', bg: 'bg-blue-900/20', border: 'border-blue-500', icon: '🗣️' }
    case 'story':
      return { color: 'text-amber-400', bg: 'bg-amber-900/20', border: 'border-amber-500', icon: '📜' }
    default:
      return { color: 'text-gray-400', bg: 'bg-gray-900/20', border: 'border-gray-500', icon: '❓' }
  }
}

// Consequence severity styling
const getConsequenceStyle = (severity) => {
  switch(severity?.toLowerCase()) {
    case 'major':
      return { color: 'text-red-400', icon: <AlertTriangle size={16} /> }
    case 'minor':
      return { color: 'text-yellow-400', icon: <AlertTriangle size={14} /> }
    case 'positive':
      return { color: 'text-green-400', icon: <CheckCircle size={16} /> }
    default:
      return { color: 'text-gray-400', icon: null }
  }
}

export default function ChoicesPanel({ show, onClose, sessionId, onMakeChoice, apiUrl = 'http://localhost:5000' }) {
  const [choices, setChoices] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedChoice, setSelectedChoice] = useState(null)
  const [making, setMaking] = useState(false)

  // Fetch available choices when panel opens
  useEffect(() => {
    if (show && sessionId) {
      fetchChoices()
    }
  }, [show, sessionId])

  const fetchChoices = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${apiUrl}/api/choices/available`, {
        headers: { 'X-Session-ID': sessionId }
      })
      if (!response.ok) throw new Error('Failed to fetch choices')
      const data = await response.json()
      setChoices(data.choices || [])
    } catch (err) {
      setError(err.message)
      setChoices([])
    } finally {
      setLoading(false)
    }
  }

  const handleMakeChoice = async (choiceId, optionId) => {
    setMaking(true)
    try {
      const response = await fetch(`${apiUrl}/api/choices/${choiceId}/select`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId
        },
        body: JSON.stringify({ option_id: optionId })
      })
      
      if (!response.ok) throw new Error('Failed to make choice')
      
      const data = await response.json()
      
      // Refresh choices and notify parent
      await fetchChoices()
      if (onMakeChoice) {
        onMakeChoice(data)
      }
      
      setSelectedChoice(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setMaking(false)
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
              <Scale size={24} /> Moral Choices
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition"
            >
              <X size={24} />
            </button>
          </div>

          <div className="p-4 space-y-4">
            {/* Loading State */}
            {loading && (
              <div className="text-center py-8">
                <Scale size={48} className="mx-auto mb-2 opacity-50 animate-pulse" />
                <p className="text-rpg-text-secondary">Loading choices...</p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-4 text-red-400">
                <XCircle size={32} className="mx-auto mb-2" />
                <p>{error}</p>
                <button
                  onClick={fetchChoices}
                  className="mt-2 px-4 py-1 bg-red-600/20 border border-red-500 rounded hover:bg-red-600/40 transition"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Choice List */}
            {!loading && !error && choices.length > 0 && (
              <div className="space-y-4">
                {choices.map((choice) => {
                  const style = getChoiceTypeStyle(choice.type)
                  const isSelected = selectedChoice?.id === choice.id

                  return (
                    <div key={choice.id} className={`rounded-lg border ${style.border} ${style.bg}`}>
                      {/* Choice Header */}
                      <div
                        className="p-4 cursor-pointer"
                        onClick={() => setSelectedChoice(isSelected ? null : choice)}
                      >
                        <div className="flex items-start gap-3">
                          <span className="text-2xl">{style.icon}</span>
                          <div className="flex-1">
                            <div className="font-semibold text-rpg-gold text-lg">{choice.prompt}</div>
                            {choice.context && (
                              <p className="text-sm text-rpg-text-secondary mt-1">{choice.context}</p>
                            )}
                            <div className="flex items-center gap-2 mt-2">
                              <span className={`text-xs ${style.color} border ${style.border} px-2 py-0.5 rounded`}>
                                {choice.type || 'Choice'}
                              </span>
                              {choice.time_sensitive && (
                                <span className="text-xs text-red-400 border border-red-500 px-2 py-0.5 rounded">
                                  Time Sensitive
                                </span>
                              )}
                            </div>
                          </div>
                          <ChevronRight
                            size={24}
                            className={`transition-transform ${isSelected ? 'rotate-90' : ''}`}
                          />
                        </div>
                      </div>

                      {/* Choice Options */}
                      <AnimatePresence>
                        {isSelected && choice.options && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-t border-gray-700"
                          >
                            <div className="p-4 space-y-3">
                              <p className="text-sm text-rpg-text-secondary mb-3">What will you do?</p>
                              {choice.options.map((option) => (
                                <button
                                  key={option.id}
                                  onClick={() => handleMakeChoice(choice.id, option.id)}
                                  disabled={making || (option.requirements && !option.requirements.met)}
                                  className={`w-full p-3 text-left rounded-lg border transition
                                    ${option.requirements && !option.requirements.met
                                      ? 'border-gray-600 bg-gray-800/50 opacity-50 cursor-not-allowed'
                                      : 'border-rpg-primary/50 bg-rpg-dark/50 hover:bg-rpg-primary/20 hover:border-rpg-primary'
                                    }`}
                                >
                                  <div className="font-medium text-rpg-gold">{option.text}</div>
                                  
                                  {/* Requirements */}
                                  {option.requirements && !option.requirements.met && (
                                    <div className="text-xs text-red-400 mt-1">
                                      Requires: {option.requirements.description}
                                    </div>
                                  )}
                                  
                                  {/* Consequence Preview */}
                                  {option.consequence_hint && (
                                    <div className="text-xs text-rpg-text-secondary mt-1 flex items-center gap-1">
                                      {getConsequenceStyle(option.consequence_severity).icon}
                                      <span>{option.consequence_hint}</span>
                                    </div>
                                  )}
                                </button>
                              ))}
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
            {!loading && !error && choices.length === 0 && (
              <div className="text-center py-8 text-rpg-text-secondary">
                <Scale size={48} className="mx-auto mb-2 opacity-50" />
                <p>No choices available right now</p>
                <p className="text-sm mt-2">Moral dilemmas will appear as you explore</p>
              </div>
            )}

            {/* Making Choice Overlay */}
            {making && (
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                <div className="text-center">
                  <Scale size={48} className="mx-auto mb-2 animate-pulse text-rpg-gold" />
                  <p className="text-rpg-gold">Making your choice...</p>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
