import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronRight, Flame } from 'lucide-react'
import { useGameStore } from '../store/gameStore'
import { getClassIcon } from '../lib/classIcons'

export default function HomeScreen({ onNewGame, onContinue }) {
  const [saves, setSaves] = useState([])
  const [loadingSaves, setLoadingSaves] = useState(true)
  const { listSaves, loadGame, isLoading } = useGameStore()

  useEffect(() => {
    let active = true
    ;(async () => {
      const list = await listSaves()
      if (active) {
        setSaves(list)
        setLoadingSaves(false)
      }
    })()
    return () => {
      active = false
    }
  }, [listSaves])

  const handleLoad = async (filepath) => {
    const result = await loadGame(filepath)
    if (result.success) onContinue()
  }

  return (
    <div className="relative z-10 min-h-[100dvh] flex flex-col items-center justify-center px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-sm text-center"
      >
        {/* Emblem */}
        <div className="flex justify-center mb-7">
          <div className="relative w-16 h-16 rounded-full grid place-items-center border border-[var(--line-strong)] bg-[var(--surface)] shadow-paper">
            <Flame size={26} className="text-[var(--gold)]" aria-hidden />
            <span className="absolute -inset-px rounded-full" style={{ boxShadow: '0 0 40px rgba(194,168,104,0.25)' }} />
          </div>
        </div>

        <p className="caps-muted mb-3">An AI-guided adventure</p>
        <h1 className="display text-5xl sm:text-6xl mb-4 tracking-tight">By Lamplight</h1>
        <p className="font-read text-[var(--ink-2)] text-lg leading-relaxed mb-9 max-w-xs mx-auto">
          A Dungeon Master who remembers every choice. Speak your intent, and the story unfolds.
        </p>

        <button
          type="button"
          onClick={onNewGame}
          className="btn btn-primary focus-ring w-full py-3.5 text-base"
        >
          Begin a new tale
        </button>

        {!loadingSaves && saves.length > 0 && (
          <div className="mt-8 text-left">
            <p className="caps-muted mb-3 text-center">Continue a journey</p>
            <ul className="space-y-2">
              {saves.slice(0, 4).map((save, idx) => {
                const Icon = getClassIcon(save.character_class)
                const saveKey = save.filepath || save.name || idx
                return (
                  <li key={saveKey}>
                    <button
                      type="button"
                      onClick={() => handleLoad(save.filepath || save.name)}
                      disabled={isLoading}
                      className="focus-ring group w-full flex items-center gap-3 p-3 rounded-xl border border-[var(--line)] hover:border-[var(--line-strong)] hover:bg-[var(--surface)] transition disabled:opacity-50"
                    >
                      <span className="w-9 h-9 rounded-full grid place-items-center bg-[var(--surface-2)] border border-[var(--line)] text-[var(--gold)] shrink-0">
                        <Icon size={16} aria-hidden />
                      </span>
                      <span className="flex-1 min-w-0">
                        <span className="block font-ui text-[var(--ink)] truncate">
                          {save.character_name || 'Unknown hero'}
                        </span>
                        <span className="block text-xs text-[var(--ink-3)] font-ui">
                          Level {save.character_level || 1} · {save.character_class || 'Adventurer'}
                        </span>
                      </span>
                      <ChevronRight size={16} className="text-[var(--ink-3)] group-hover:text-[var(--gold)] shrink-0 transition" />
                    </button>
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </motion.div>
    </div>
  )
}
