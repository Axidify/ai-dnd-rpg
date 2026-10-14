import { create } from 'zustand'
import axios from 'axios'
import { stripDmTags } from '../lib/stripDmTags'

function findLastDmIndex(messages) {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i]?.type === 'dm') return i
  }
  return messages.length - 1
}

/** Pull character + session fields from API responses (game_state is canonical). */
function syncFromGameState(gameState, prev = {}) {
  if (!gameState) return {}
  return {
    character: gameState.character ?? prev.character,
    currentLocation: gameState.current_location ?? prev.currentLocation,
    inCombat: gameState.in_combat ?? prev.inCombat,
    quests: gameState.quest_log ?? prev.quests,
    party: gameState.party ?? prev.party,
    gameOver: gameState.game_over ?? prev.gameOver,
    gameOverReason: gameState.game_over_reason ?? prev.gameOverReason,
    dmUnavailable: gameState.dm_unavailable ?? prev.dmUnavailable ?? false,
  }
}

function applyMutation(set, data, extra = {}) {
  set((state) => ({
    ...syncFromGameState(data?.game_state, state),
    ...extra,
    isLoading: false,
  }))
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
  party: [],
  gameOver: false,
  gameOverReason: null,
  dmUnavailable: false,  // last narration failed (LLM unreachable / stream error)
  lastAction: null,      // for "Try again"

  // Fetch available scenarios
  fetchScenarios: async () => {
    try {
      const response = await api.get('/scenarios')
      set({ scenarios: response.data.scenarios || [] })
    } catch (error) {
      console.error('Failed to fetch scenarios:', error)
    }
  },
  
  // Roll a character for review; /game/start reuses it via the token
  preview: null,         // { token, key, character }
  previewLoading: false,
  previewCharacter: async (name, charClass, race) => {
    const key = `${name}|${charClass}|${race}`
    if (get().preview?.key === key) return
    set({ previewLoading: true, error: null })
    try {
      const response = await api.post('/character/preview', {
        character: { name, class: charClass, race },
      })
      set({
        preview: { token: response.data.preview_token, key, character: response.data.character },
        previewLoading: false,
      })
    } catch (error) {
      set({
        preview: null,
        previewLoading: false,
        error: error.response?.data?.error || 'Could not roll your hero. Please try again.',
      })
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
      const preview = get().preview
      if (preview?.key === `${name}|${charClass}|${race}`) {
        payload.preview_token = preview.token
      }
      
      const response = await api.post('/game/start', payload)
      const { session_id, message, game_state } = response.data
      
      // Initialize messages with the DM welcome message
      const initialMessages = [{ type: 'dm', content: message }]
      
      set({
        sessionId: session_id,
        messages: initialMessages,
        ...syncFromGameState(game_state),
        isLoading: false,
        preview: null,  // the token is single-use
      })
    } catch (error) {
      const timedOut = error.code === 'ECONNABORTED'
      set({
        error: timedOut
          ? 'The Dungeon Master is taking too long to prepare your opening scene. Please try again.'
          : error.response?.data?.error || 'Failed to create character',
        isLoading: false,
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
    const { sessionId, inCombat, gameOver } = get()
    if (!sessionId) return
    if (gameOver) {
      set({ error: 'Game over — start a new adventure to continue.' })
      return
    }
    if (inCombat) {
      set({ error: 'Use Attack, Defend, or Flee during combat.' })
      return
    }

    set({
      messages: [
        ...get().messages,
        { type: 'player', content: action },
        { type: 'dm', content: '', isStreaming: true },
      ],
      isLoading: true,
      error: null,
      dmUnavailable: false,
      lastAction: action,
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
            fullContent += data.content
            patchDm({ content: stripDmTags(fullContent), rollResult })
          } else if (data.type === 'roll' && data.result) {
            rollResult = data.result
            patchDm({ rollResult })
          } else if (data.type === 'combat') {
            combatStarted = true
            set({ inCombat: true })
          } else if (data.type === 'gold' && data.total != null) {
            set((state) => ({
              character: state.character
                ? { ...state.character, gold: data.total }
                : state.character,
            }))
          } else if (data.type === 'xp' && data.amount) {
            set((state) => {
              if (!state.character) return {}
              const xp = (state.character.experience || 0) + data.amount
              return { character: { ...state.character, experience: xp } }
            })
          } else if (data.type === 'item' && data.item) {
            set((state) => {
              if (!state.character) return {}
              const inv = [...(state.character.inventory || [])]
              inv.push({ name: data.item })
              return { character: { ...state.character, inventory: inv } }
            })
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
          } else if (data.type === 'quest_accepted' && data.quest) {
            set((state) => ({
              quests: state.quests.some((q) => q.id === data.quest_id)
                ? state.quests.map((q) => (q.id === data.quest_id ? data.quest : q))
                : [...state.quests, data.quest],
            }))
          } else if (data.type === 'game_over') {
            set({ gameOver: true, gameOverReason: data.reason || null })
          } else if (data.type === 'done' || data.type === 'complete') {
            gotDone = true
            gameState = data.game_state
            if (data.game_over) {
              set({
                gameOver: true,
                gameOverReason: gameState?.game_over_reason || null,
              })
            }
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
          content: stripDmTags(fullContent, { trim: true }),
          rollResult,
          combatStarted,
          isStreaming: false,
        }
        return {
          messages: newMessages,
          ...syncFromGameState(gameState, {
            ...state,
            inCombat: gameState?.in_combat ?? combatStarted ?? state.inCombat,
          }),
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
        return { messages: newMessages, error: msg, isLoading: false, dmUnavailable: true }
      })
    } finally {
      clearTimeout(timeoutId)
      set({ isLoading: false })
    }
  },

  // Resend the last action after the DM couldn't be reached
  retryLastAction: () => {
    const { lastAction, isLoading } = get()
    if (lastAction && !isLoading) get().sendActionStreaming(lastAction)
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
        description,
      })
      set({ isLoading: false })
      return response.data
    } catch (error) {
      set({ isLoading: false })
      return { success: false, message: error.response?.data?.error || 'Save failed' }
    }
  },
  
  // Load game
  loadGame: async (saveName) => {
    set({ isLoading: true, error: null })
    try {
      // The server only accepts a bare save name, never a path
      const name = String(saveName ?? '').split(/[\\/]/).pop().replace(/\.json$/, '')
      const response = await api.post('/game/load', { name })
      const { session_id, game_state } = response.data
      
      set({
        sessionId: session_id,
        messages: game_state.messages || [],
        combatStatus: null,
        ...syncFromGameState(game_state),
        isLoading: false,
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
      set((state) => syncFromGameState(game_state, state))
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
        
        set((state) => {
          let updatedQuests = [...state.quests]
          for (const update of quest_updates) {
            updatedQuests = updatedQuests.map((q) =>
              q.id === update.quest_id ? update.quest : q
            )
            if (!updatedQuests.find((q) => q.id === update.quest_id)) {
              updatedQuests.push(update.quest)
            }
          }
          const synced = syncFromGameState(game_state, {
            ...state,
            quests: game_state?.quest_log || updatedQuests,
            inCombat: response.data.in_combat ?? response.data.combat_started ?? state.inCombat,
          })
          return {
            ...synced,
            currentLocation:
              typeof newLocation === 'object' ? newLocation.name : newLocation,
            messages: [
              ...state.messages,
              {
                type: 'dm',
                content: response.data.message,
                timestamp: new Date().toISOString(),
              },
            ],
            isLoading: false,
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
  
  endSession: async () => {
    const { sessionId } = get()
    if (sessionId) {
      try {
        await api.post('/game/end', { session_id: sessionId })
      } catch {
        /* best-effort cleanup */
      }
    }
    set({
      sessionId: null,
      character: null,
      messages: [],
      error: null,
      inCombat: false,
      currentLocation: null,
      quests: [],
      party: [],
      gameOver: false,
      gameOverReason: null,
      combatStatus: null,
      shopInventory: null,
    })
  },

  // ========== Combat Actions ==========
  combatStatus: null,
  
  getCombatStatus: async () => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    try {
      const response = await api.get('/combat/status', {
        params: { session_id: sessionId }
      })
      const inCombat = response.data.in_combat ?? response.data.active ?? false
      set({ combatStatus: response.data, inCombat })
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
        target: targetIndex,
      })
      const { message, combat_status } = response.data
      
      const died = response.data.player_died || response.data.game_over
      set((state) => ({
        messages: [...state.messages, { type: 'dm', content: message }],
        ...syncFromGameState(response.data.game_state, state),
        inCombat: response.data.game_state?.in_combat ?? state.inCombat,
        gameOver: died || response.data.game_state?.game_over || state.gameOver,
        gameOverReason:
          response.data.game_state?.game_over_reason || state.gameOverReason,
        combatStatus: combat_status || response.data.combat_status || null,
        isLoading: false,
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
      
      const died = response.data.player_died || response.data.game_over
      set((state) => ({
        messages: [...state.messages, { type: 'dm', content: message }],
        ...syncFromGameState(game_state, state),
        inCombat: game_state?.in_combat ?? state.inCombat,
        gameOver: died || game_state?.game_over || state.gameOver,
        gameOverReason: game_state?.game_over_reason || state.gameOverReason,
        combatStatus: response.data.combat_status || null,
        isLoading: false,
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
      
      const died = response.data.player_died || response.data.game_over
      set((state) => ({
        messages: [...state.messages, { type: 'dm', content: message }],
        ...syncFromGameState(game_state, state),
        inCombat: game_state?.in_combat ?? state.inCombat,
        gameOver: died || game_state?.game_over || state.gameOver,
        gameOverReason: game_state?.game_over_reason || state.gameOverReason,
        combatStatus: response.data.combat_status || null,
        isLoading: false,
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
      
      applyMutation(set, response.data, {
        messages: [...get().messages, { type: 'dm', content: response.data.message }],
      })
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
        type: restType,
      })
      
      applyMutation(set, response.data, {
        messages: [...get().messages, { type: 'dm', content: response.data.message }],
      })
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
      
      applyMutation(set, response.data, {
        messages: [...get().messages, { type: 'dm', content: response.data.message }],
      })
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
      
      applyMutation(set, response.data, {
        messages: [...get().messages, { type: 'dm', content: response.data.message }],
      })
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
  
  buyItem: async (itemIdOrName, quantity = 1) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/shop/buy', {
        session_id: sessionId,
        item_id: itemIdOrName,
        quantity,
      })
      
      applyMutation(set, response.data, {
        messages: [...get().messages, { type: 'dm', content: response.data.message }],
      })
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
      
      applyMutation(set, response.data, {
        messages: [...get().messages, { type: 'dm', content: response.data.message }],
      })
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
  availableRecruits: [],
  
  getParty: async () => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    try {
      const response = await api.get('/party/view', {
        params: { session_id: sessionId }
      })
      const members = response.data.party || response.data.members || []
      set({
        party: members,
        availableRecruits: response.data.available_recruits || [],
      })
      return response.data
    } catch (error) {
      console.error('Get party failed:', error)
      return null
    }
  },
  
  recruitMember: async (npcId) => {
    const { sessionId } = get()
    if (!sessionId) return null
    
    set({ isLoading: true })
    try {
      const response = await api.post('/party/recruit', {
        session_id: sessionId,
        npc_id: npcId,
      })
      
      applyMutation(set, response.data, {
        party: response.data.game_state?.party || get().party,
        messages: [...get().messages, { type: 'dm', content: response.data.message }],
      })
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
