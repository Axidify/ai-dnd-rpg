import { create } from 'zustand'
import axios from 'axios'
import { stripDmTags } from '../lib/stripDmTags'

function findLastDmIndex(messages) {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i]?.type === 'dm') return i
  }
  return messages.length - 1
}

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export const useGameStore = create((set, get) => ({
  // State
  sessionId: null,
  character: null,
  messages: [],
  isLoading: false,
  error: null,
  inCombat: false,
  currentLocation: null,
  scenarios: [],
  quests: [],  // Quest log
  
  // Fetch available scenarios
  fetchScenarios: async () => {
    try {
      const response = await api.get('/scenarios')
      set({ scenarios: response.data.scenarios || [] })
    } catch (error) {
      console.error('Failed to fetch scenarios:', error)
    }
  },
  
  // Actions
  createCharacter: async (name, charClass, race, scenarioId = null) => {
    set({ isLoading: true, error: null })
    try {
      const payload = {
        character: { name, class: charClass, race }
      }
      if (scenarioId) {
        payload.scenario_id = scenarioId
      }
      
      const response = await api.post('/game/start', payload)
      const { session_id, message, game_state } = response.data
      
      // Initialize messages with the DM welcome message
      const initialMessages = [{ type: 'dm', content: message }]
      
      set({
        sessionId: session_id,
        character: game_state.character,
        messages: initialMessages,
        currentLocation: game_state.current_location,
        quests: game_state.quest_log || [],
        isLoading: false
      })
    } catch (error) {
      set({ 
        error: error.response?.data?.error || 'Failed to create character',
        isLoading: false 
      })
    }
  },
  
  sendAction: async (action) => {
    const { sessionId } = get()
    if (!sessionId) return
    
    // Add player message immediately
    set(state => ({
      messages: [...state.messages, { type: 'player', content: action }],
      isLoading: true,
      error: null
    }))
    
    try {
      const response = await api.post('/game/action', {
        session_id: sessionId,
        action
      })
      
      const { message, roll_result, combat_started, game_state } = response.data
      
      set(state => ({
        messages: [...state.messages, { 
          type: 'dm', 
          content: message,
          rollResult: roll_result,
          combatStarted: combat_started
        }],
        character: game_state?.character || state.character,
        currentLocation: game_state?.current_location || state.currentLocation,
        inCombat: game_state?.in_combat || combat_started || false,
        quests: game_state?.quest_log || state.quests,
        isLoading: false
      }))
    } catch (error) {
      set({ 
        error: error.response?.data?.error || 'Action failed',
        isLoading: false 
      })
    }
  },
  
  clearError: () => set({ error: null }),
  
  // Send action with streaming response
  sendActionStreaming: async (action) => {
    const { sessionId } = get()
    if (!sessionId) return

    set({
      messages: [
        ...get().messages,
        { type: 'player', content: action },
        { type: 'dm', content: '', isStreaming: true },
      ],
      isLoading: true,
      error: null,
    })

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 120000)

    let fullContent = ''
    let rollResult = null
    let combatStarted = false
    let gameState = null
    let gotDone = false

    const patchDm = (patch) => {
      set((state) => {
        const newMessages = [...state.messages]
        const idx = findLastDmIndex(newMessages)
        newMessages[idx] = { ...newMessages[idx], ...patch }
        return { messages: newMessages }
      })
    }

    try {
      const response = await fetch('/api/game/action/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, action }),
        signal: controller.signal,
      })

      if (!response.ok) {
        const errText = await response.text().catch(() => '')
        throw new Error(errText || `Request failed (${response.status})`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = line.slice(6).trim()
          if (!payload) continue

          let data
          try {
            data = JSON.parse(payload)
          } catch (parseError) {
            console.warn('SSE JSON parse failed:', parseError, payload.slice(0, 120))
            continue
          }

          if (data.type === 'chunk' && data.content) {
            fullContent += stripDmTags(data.content)
            patchDm({ content: fullContent, rollResult })
          } else if (data.type === 'roll' && data.result) {
            rollResult = data.result
            patchDm({ rollResult })
          } else if (data.type === 'combat') {
            combatStarted = true
          } else if (data.type === 'quest_update' && data.quest) {
            set((state) => {
              const updated = state.quests.map((q) =>
                q.id === data.quest_id ? data.quest : q
              )
              if (!updated.find((q) => q.id === data.quest_id)) {
                updated.push(data.quest)
              }
              return { quests: updated }
            })
          } else if (data.type === 'done' || data.type === 'complete') {
            gotDone = true
            gameState = data.game_state
          } else if (data.type === 'error') {
            throw new Error(data.message || 'Stream error')
          }
        }
      }

      if (!gotDone) {
        console.warn('Stream ended without done event')
      }

      if (!fullContent.trim() && rollResult) {
        const outcome = rollResult.success ? 'succeeds' : 'fails'
        fullContent = `The ${rollResult.skill || 'check'} ${outcome}. *What do you do next?*`
      }

      set((state) => {
        const newMessages = [...state.messages]
        const idx = findLastDmIndex(newMessages)
        newMessages[idx] = {
          type: 'dm',
          content: fullContent.trim(),
          rollResult,
          combatStarted,
          isStreaming: false,
        }
        return {
          messages: newMessages,
          character: gameState?.character || state.character,
          currentLocation: gameState?.current_location || state.currentLocation,
          inCombat: gameState?.in_combat ?? combatStarted ?? state.inCombat,
          quests: gameState?.quest_log || state.quests,
          isLoading: false,
        }
      })
    } catch (error) {
      const msg =
        error.name === 'AbortError'
          ? 'The Dungeon Master took too long to respond. Please try again.'
          : error.message || 'Streaming failed'

      set((state) => {
        const newMessages = [...state.messages]
        const idx = findLastDmIndex(newMessages)
        if (idx >= 0 && newMessages[idx]?.type === 'dm') {
          newMessages[idx] = {
            type: 'dm',
            content: fullContent.trim() || `*${msg}*`,
            rollResult,
            isStreaming: false,
          }
        }
        return { messages: newMessages, error: msg, isLoading: false }
      })
    } finally {
      clearTimeout(timeoutId)
      set({ isLoading: false })
    }
  },
  
  // Roll dice
  rollDice: async (diceType = 'd20', modifier = 0) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    try {
      const response = await api.post('/game/roll', {
        session_id: sessionId,
        dice: diceType,
        modifier
      })
      return response.data
    } catch (error) {
      console.error('Roll failed:', error)
      return null
    }
  },
  
  // Save game
  saveGame: async (slot = 1, description = '') => {
    const { sessionId } = get()
    if (!sessionId) return { success: false, message: 'No active session' }
    
    set({ isLoading: true })
    try {
      const response = await api.post('/game/save', {
        session_id: sessionId,
        slot,
        description
      })
      set({ isLoading: false })
      return response.data
    } catch (error) {
      set({ isLoading: false })
      return { success: false, message: error.response?.data?.error || 'Save failed' }
    }
  },
  
  // Load game
  loadGame: async (filepath) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/game/load', { filepath })
      const { session_id, game_state } = response.data
      
      set({
        sessionId: session_id,
        character: game_state.character,
        messages: game_state.messages || [],
        currentLocation: game_state.current_location,
        quests: game_state.quest_log || [],
        isLoading: false
      })
      return { success: true }
    } catch (error) {
      set({ 
        error: error.response?.data?.error || 'Load failed',
        isLoading: false 
      })
      return { success: false }
    }
  },
  
  // List saved games
  listSaves: async () => {
    try {
      const response = await api.get('/game/saves')
      return response.data.saves || []
    } catch (error) {
      console.error('Failed to list saves:', error)
      return []
    }
  },
  
  // Refresh game state
  refreshState: async () => {
    const { sessionId } = get()
    if (!sessionId) return
    
    try {
      const response = await api.get('/game/state', {
        params: { session_id: sessionId }
      })
      const { game_state } = response.data
      set({
        character: game_state.character,
        currentLocation: game_state.current_location,
        inCombat: game_state.in_combat,
        quests: game_state.quest_log || []
      })
    } catch (error) {
      console.error('Failed to refresh state:', error)
    }
  },
  
  // Get available travel destinations
  getDestinations: async () => {
    const { sessionId } = get()
    if (!sessionId) return { destinations: [] }
    
    try {
      const response = await api.get('/locations', {
        params: { session_id: sessionId }
      })
      return response.data
    } catch (error) {
      console.error('Failed to get destinations:', error)
      return { destinations: [] }
    }
  },
  
  // Travel to a destination
  travel: async (destination) => {
    const { sessionId } = get()
    if (!sessionId) return { success: false, message: 'No active session' }
    
    set({ isLoading: true })
    
    try {
      const response = await api.post('/travel', {
        session_id: sessionId,
        destination
      })
      
      if (response.data.success) {
        const newLocation = response.data.new_location
        const game_state = response.data.game_state
        const quest_updates = response.data.quest_updates || []
        
        set(state => {
          // Update quests from quest_updates
          let updatedQuests = [...state.quests]
          for (const update of quest_updates) {
            updatedQuests = updatedQuests.map(q => 
              q.id === update.quest_id ? update.quest : q
            )
            // If quest wasn't in the list, add it
            if (!updatedQuests.find(q => q.id === update.quest_id)) {
              updatedQuests.push(update.quest)
            }
          }
          
          return {
            currentLocation: typeof newLocation === 'object' ? newLocation.name : newLocation,
            messages: [...state.messages, {
              type: 'dm',
              content: response.data.message,
              timestamp: new Date().toISOString()
            }],
            quests: game_state?.quest_log || updatedQuests,
            character: game_state?.character || state.character,
            isLoading: false
          }
        })
      } else {
        set({ isLoading: false })
      }
      
      return response.data
    } catch (error) {
      console.error('Failed to travel:', error)
      set({ isLoading: false })
      return { success: false, message: error.message }
    }
  },
  
  endSession: () => set({
    sessionId: null,
    character: null,
    messages: [],
    error: null,
    inCombat: false,
    currentLocation: null
  }),

  // ========== Combat Actions ==========
  combatStatus: null,
  
  getCombatStatus: async () => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    try {
      const response = await api.get('/combat/status', {
        params: { session_id: sessionId }
      })
      set({ combatStatus: response.data, inCombat: response.data.active })
      return response.data
    } catch (error) {
      console.error('Failed to get combat status:', error)
      return null
    }
  },
  
  combatAttack: async (targetIndex = 0) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/combat/attack', {
        session_id: sessionId,
        target_index: targetIndex
      })
      const { message, game_state, combat_log } = response.data
      
      // Add combat log to messages
      set(state => ({
        messages: [...state.messages, { type: 'dm', content: message }],
        character: game_state?.character || state.character,
        inCombat: game_state?.in_combat ?? state.inCombat,
        combatStatus: response.data.combat_status || null,
        isLoading: false
      }))
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Attack failed:', error)
      return null
    }
  },
  
  combatDefend: async () => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/combat/defend', {
        session_id: sessionId
      })
      const { message, game_state } = response.data
      
      set(state => ({
        messages: [...state.messages, { type: 'dm', content: message }],
        character: game_state?.character || state.character,
        inCombat: game_state?.in_combat ?? state.inCombat,
        combatStatus: response.data.combat_status || null,
        isLoading: false
      }))
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Defend failed:', error)
      return null
    }
  },
  
  combatFlee: async () => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/combat/flee', {
        session_id: sessionId
      })
      const { message, game_state } = response.data
      
      set(state => ({
        messages: [...state.messages, { type: 'dm', content: message }],
        character: game_state?.character || state.character,
        inCombat: game_state?.in_combat ?? state.inCombat,
        combatStatus: response.data.combat_status || null,
        isLoading: false
      }))
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Flee failed:', error)
      return null
    }
  },

  // ========== Character Actions ==========
  levelUp: async (choice = null) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/character/levelup', {
        session_id: sessionId,
        choice
      })
      
      set(state => ({
        character: response.data.character || state.character,
        messages: [...state.messages, { type: 'dm', content: response.data.message }],
        isLoading: false
      }))
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Level up failed:', error)
      return { success: false, message: error.response?.data?.error || 'Level up failed' }
    }
  },
  
  rest: async (restType = 'short') => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/character/rest', {
        session_id: sessionId,
        rest_type: restType
      })
      
      set(state => ({
        character: response.data.character || state.character,
        messages: [...state.messages, { type: 'dm', content: response.data.message }],
        isLoading: false
      }))
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Rest failed:', error)
      return { success: false, message: error.response?.data?.error || 'Rest failed' }
    }
  },

  // ========== Inventory Actions ==========
  useItem: async (itemName, target = null) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/inventory/use', {
        session_id: sessionId,
        item_name: itemName,
        target
      })
      
      set(state => ({
        character: response.data.character || state.character,
        messages: [...state.messages, { type: 'dm', content: response.data.message }],
        isLoading: false
      }))
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Use item failed:', error)
      return { success: false, message: error.response?.data?.error || 'Use item failed' }
    }
  },
  
  equipItem: async (itemName) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/inventory/equip', {
        session_id: sessionId,
        item_name: itemName
      })
      
      set(state => ({
        character: response.data.character || state.character,
        messages: [...state.messages, { type: 'dm', content: response.data.message }],
        isLoading: false
      }))
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Equip failed:', error)
      return { success: false, message: error.response?.data?.error || 'Equip failed' }
    }
  },

  // ========== Shop Actions ==========
  shopInventory: null,
  
  browseShop: async () => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    try {
      const response = await api.get('/shop/browse', {
        params: { session_id: sessionId }
      })
      set({ shopInventory: response.data })
      return response.data
    } catch (error) {
      console.error('Browse shop failed:', error)
      return null
    }
  },
  
  buyItem: async (itemName, quantity = 1) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/shop/buy', {
        session_id: sessionId,
        item_name: itemName,
        quantity
      })
      
      set(state => ({
        character: response.data.character || state.character,
        messages: [...state.messages, { type: 'dm', content: response.data.message }],
        isLoading: false
      }))
      // Refresh shop inventory after purchase
      get().browseShop()
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Buy failed:', error)
      return { success: false, message: error.response?.data?.error || 'Purchase failed' }
    }
  },
  
  sellItem: async (itemName, quantity = 1) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/shop/sell', {
        session_id: sessionId,
        item_name: itemName,
        quantity
      })
      
      set(state => ({
        character: response.data.character || state.character,
        messages: [...state.messages, { type: 'dm', content: response.data.message }],
        isLoading: false
      }))
      // Refresh shop inventory after sale
      get().browseShop()
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Sell failed:', error)
      return { success: false, message: error.response?.data?.error || 'Sale failed' }
    }
  },

  // ========== Party Actions ==========
  party: [],
  availableRecruits: [],
  
  getParty: async () => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    try {
      const response = await api.get('/party/view', {
        params: { session_id: sessionId }
      })
      set({ 
        party: response.data.party || [],
        availableRecruits: response.data.available_recruits || []
      })
      return response.data
    } catch (error) {
      console.error('Get party failed:', error)
      return null
    }
  },
  
  recruitMember: async (npcName) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/party/recruit', {
        session_id: sessionId,
        npc_name: npcName
      })
      
      set(state => ({
        party: response.data.party || state.party,
        messages: [...state.messages, { type: 'dm', content: response.data.message }],
        isLoading: false
      }))
      // Refresh party data
      get().getParty()
      return response.data
    } catch (error) {
      set({ isLoading: false })
      console.error('Recruit failed:', error)
      return { success: false, message: error.response?.data?.error || 'Recruit failed' }
    }
  },

  // ========== Location Actions ==========
  locationDetails: null,
  
  scanLocation: async () => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    try {
      const response = await api.get('/location/scan', {
        params: { session_id: sessionId }
      })
      set({ locationDetails: response.data })
      return response.data
    } catch (error) {
      console.error('Scan location failed:', error)
      return null
    }
  }
}))
