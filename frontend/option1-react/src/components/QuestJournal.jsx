import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Scroll, X, CheckCircle, Circle, Target, Trophy, Clock, MapPin, ChevronDown, ChevronUp } from 'lucide-react'

/**
 * QuestJournal - Display quests with objectives, progress, and rewards
 * 
 * Quest Types:
 * - MAIN: Primary story quests
 * - SIDE: Optional side quests
 * - MINOR: Small tasks and bounties
 */

// Quest type styling
const getQuestTypeStyle = (type) => {
  switch(type?.toLowerCase()) {
    case 'main':
      return { color: 'text-amber-400', bg: 'bg-amber-900/20', border: 'border-amber-500', icon: '⭐' }
    case 'side':
      return { color: 'text-blue-400', bg: 'bg-blue-900/20', border: 'border-blue-500', icon: '📋' }
    case 'minor':
      return { color: 'text-gray-400', bg: 'bg-gray-900/20', border: 'border-gray-500', icon: '📌' }
    default:
      return { color: 'text-gray-400', bg: 'bg-gray-900/20', border: 'border-gray-500', icon: '📜' }
  }
}

// Quest status styling
const getStatusStyle = (status) => {
  switch(status?.toLowerCase()) {
    case 'active':
      return { color: 'text-green-400', label: 'Active' }
    case 'complete':
    case 'completed':
      return { color: 'text-amber-400', label: 'Complete' }
    case 'failed':
      return { color: 'text-red-400', label: 'Failed' }
    default:
      return { color: 'text-gray-400', label: status || 'Unknown' }
  }
}

export default function QuestJournal({ show, onClose, sessionId, apiUrl = 'http://localhost:5000' }) {
  const [quests, setQuests] = useState({ active: [], completed: [], failed: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [expandedQuest, setExpandedQuest] = useState(null)
  const [activeTab, setActiveTab] = useState('active')

  // Fetch quests when panel opens
  useEffect(() => {
    if (show && sessionId) {
      fetchQuests()
    }
  }, [show, sessionId])

  const fetchQuests = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${apiUrl}/api/quests`, {
        headers: { 'X-Session-ID': sessionId }
      })
      if (!response.ok) throw new Error('Failed to fetch quests')
      const data = await response.json()
      
      // Organize quests by status
      const organized = {
        active: data.quests?.filter(q => q.status === 'ACTIVE' || q.status === 'active') || [],
        completed: data.quests?.filter(q => q.status === 'COMPLETE' || q.status === 'completed') || [],
        failed: data.quests?.filter(q => q.status === 'FAILED' || q.status === 'failed') || []
      }
      setQuests(organized)
    } catch (err) {
      setError(err.message)
      setQuests({ active: [], completed: [], failed: [] })
    } finally {
      setLoading(false)
    }
  }

  // Calculate objective completion
  const getProgress = (objectives) => {
    if (!objectives || objectives.length === 0) return { completed: 0, total: 0, percent: 0 }
    const completed = objectives.filter(o => o.completed).length
    const total = objectives.length
    return { completed, total, percent: Math.round((completed / total) * 100) }
  }

  if (!show) return null

  const currentQuests = quests[activeTab] || []
  const tabs = [
    { id: 'active', label: 'Active', count: quests.active.length, icon: <Target size={16} /> },
    { id: 'completed', label: 'Completed', count: quests.completed.length, icon: <Trophy size={16} /> },
    { id: 'failed', label: 'Failed', count: quests.failed.length, icon: <X size={16} /> }
  ]

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
          className="rpg-card max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <h2 className="text-xl font-medieval text-rpg-gold flex items-center gap-2">
              <Scroll size={24} /> Quest Journal
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition"
            >
              <X size={24} />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-700">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-4 py-3 flex items-center justify-center gap-2 transition
                  ${activeTab === tab.id
                    ? 'bg-rpg-primary/20 text-rpg-gold border-b-2 border-rpg-gold'
                    : 'text-rpg-text-secondary hover:bg-rpg-dark/50'
                  }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
                {tab.count > 0 && (
                  <span className={`text-xs px-2 py-0.5 rounded-full
                    ${activeTab === tab.id ? 'bg-rpg-gold/20' : 'bg-gray-700'}`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Loading State */}
            {loading && (
              <div className="text-center py-8">
                <Scroll size={48} className="mx-auto mb-2 opacity-50 animate-pulse" />
                <p className="text-rpg-text-secondary">Loading quests...</p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-4 text-red-400">
                <X size={32} className="mx-auto mb-2" />
                <p>{error}</p>
                <button
                  onClick={fetchQuests}
                  className="mt-2 px-4 py-1 bg-red-600/20 border border-red-500 rounded hover:bg-red-600/40 transition"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Quest List */}
            {!loading && !error && currentQuests.length > 0 && (
              <div className="space-y-3">
                {currentQuests.map((quest) => {
                  const typeStyle = getQuestTypeStyle(quest.quest_type || quest.type)
                  const statusStyle = getStatusStyle(quest.status)
                  const progress = getProgress(quest.objectives)
                  const isExpanded = expandedQuest === quest.id

                  return (
                    <div key={quest.id} className={`rounded-lg border ${typeStyle.border} ${typeStyle.bg}`}>
                      {/* Quest Header */}
                      <div
                        className="p-4 cursor-pointer"
                        onClick={() => setExpandedQuest(isExpanded ? null : quest.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <span className="text-2xl">{typeStyle.icon}</span>
                            <div>
                              <div className="font-semibold text-rpg-gold text-lg">{quest.name}</div>
                              <div className="flex items-center gap-2 mt-1">
                                <span className={`text-xs ${typeStyle.color}`}>
                                  {quest.quest_type || quest.type || 'Quest'}
                                </span>
                                <span className={`text-xs ${statusStyle.color}`}>
                                  • {statusStyle.label}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            {/* Progress Bar */}
                            {activeTab === 'active' && progress.total > 0 && (
                              <div className="text-right">
                                <div className="text-xs text-rpg-text-secondary">
                                  {progress.completed}/{progress.total}
                                </div>
                                <div className="w-20 h-2 bg-gray-700 rounded-full mt-1 overflow-hidden">
                                  <div
                                    className="h-full bg-rpg-gold transition-all"
                                    style={{ width: `${progress.percent}%` }}
                                  />
                                </div>
                              </div>
                            )}
                            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                          </div>
                        </div>
                      </div>

                      {/* Quest Details */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-t border-gray-700"
                          >
                            <div className="p-4 space-y-4">
                              {/* Description */}
                              {quest.description && (
                                <p className="text-rpg-text-secondary text-sm">
                                  {quest.description}
                                </p>
                              )}

                              {/* Objectives */}
                              {quest.objectives && quest.objectives.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-rpg-primary mb-2 flex items-center gap-1">
                                    <Target size={14} /> Objectives
                                  </h4>
                                  <ul className="space-y-2">
                                    {quest.objectives.map((obj, idx) => (
                                      <li key={obj.id || idx} className="flex items-start gap-2 text-sm">
                                        {obj.completed ? (
                                          <CheckCircle size={18} className="text-green-500 flex-shrink-0 mt-0.5" />
                                        ) : (
                                          <Circle size={18} className="text-gray-500 flex-shrink-0 mt-0.5" />
                                        )}
                                        <span className={obj.completed ? 'text-gray-500 line-through' : 'text-rpg-text'}>
                                          {obj.description}
                                          {obj.required_count > 1 && (
                                            <span className="text-rpg-text-secondary ml-1">
                                              ({obj.current_count || 0}/{obj.required_count})
                                            </span>
                                          )}
                                        </span>
                                        {obj.optional && (
                                          <span className="text-xs text-blue-400">(Optional)</span>
                                        )}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Rewards */}
                              {quest.rewards && Object.keys(quest.rewards).length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-rpg-primary mb-2 flex items-center gap-1">
                                    <Trophy size={14} /> Rewards
                                  </h4>
                                  <div className="flex flex-wrap gap-2">
                                    {quest.rewards.gold && (
                                      <span className="text-xs bg-yellow-900/30 border border-yellow-600 text-yellow-400 px-2 py-1 rounded">
                                        💰 {quest.rewards.gold} Gold
                                      </span>
                                    )}
                                    {quest.rewards.xp && (
                                      <span className="text-xs bg-purple-900/30 border border-purple-600 text-purple-400 px-2 py-1 rounded">
                                        ✨ {quest.rewards.xp} XP
                                      </span>
                                    )}
                                    {quest.rewards.items && quest.rewards.items.map((item, idx) => (
                                      <span key={idx} className="text-xs bg-blue-900/30 border border-blue-600 text-blue-400 px-2 py-1 rounded">
                                        📦 {item}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Quest Giver */}
                              {quest.giver_npc_id && (
                                <div className="text-xs text-rpg-text-secondary flex items-center gap-1">
                                  <MapPin size={12} />
                                  From: {quest.giver_name || quest.giver_npc_id}
                                </div>
                              )}

                              {/* Time Limit */}
                              {quest.time_limit && (
                                <div className="text-xs text-orange-400 flex items-center gap-1">
                                  <Clock size={12} />
                                  Time remaining: {quest.time_remaining || quest.time_limit} turns
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
            {!loading && !error && currentQuests.length === 0 && (
              <div className="text-center py-8 text-rpg-text-secondary">
                <Scroll size={48} className="mx-auto mb-2 opacity-50" />
                <p>No {activeTab} quests</p>
                {activeTab === 'active' && (
                  <p className="text-sm mt-2">Talk to NPCs to discover new quests</p>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
