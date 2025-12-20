import { create } from 'zustand'
import axios from 'axios'

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
  
  // Actions
  createCharacter: async (name, charClass, race) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/game/start', {
        character: { name, class: charClass, race }
      })
      const { session_id, game_state } = response.data
      set({
        sessionId: session_id,
        character: game_state.character,
        messages: game_state.messages || [],
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
      isLoading: true
    }))
    
    try {
      const response = await api.post('/game/action', {
        session_id: sessionId,
        action
      })
      
      set(state => ({
        messages: [...state.messages, { 
          type: 'dm', 
          content: response.data.message 
        }],
        character: response.data.game_state?.character || state.character,
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
  
  endSession: () => set({
    sessionId: null,
    character: null,
    messages: [],
    error: null
  })
}))
