import { useState, useRef, useEffect } from 'react'
import { useGameStore } from '../store/gameStore'
import { getXpProgress } from '../lib/gameConstants'

import TopBar from './TopBar'
import CommandBar from './CommandBar'
import StoryEntry from './StoryEntry'
import HeroDrawer from './HeroDrawer'
import Modal from './Modal'
import WorldMap from './WorldMap'
import InventoryPanel from './panels/InventoryPanel'
import QuestsPanel from './panels/QuestsPanel'
import ShopPanel from './panels/ShopPanel'
import PartyPanel from './panels/PartyPanel'
import RestPanel from './panels/RestPanel'
import MenuPanel from './panels/MenuPanel'
import { SavePanel, LoadPanel } from './panels/SaveLoadPanels'

export default function GameScreen({ onLeaveGame }) {
  const [input, setInput] = useState('')
  const [showHero, setShowHero] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [showInventory, setShowInventory] = useState(false)
  const [showQuests, setShowQuests] = useState(false)
  const [showShop, setShowShop] = useState(false)
  const [showParty, setShowParty] = useState(false)
  const [showRest, setShowRest] = useState(false)
  const [showSave, setShowSave] = useState(false)
  const [showLoad, setShowLoad] = useState(false)
  const [showMap, setShowMap] = useState(false)
  const [saves, setSaves] = useState([])
  const [saveError, setSaveError] = useState(null)

  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const {
    character, messages, sendActionStreaming, isLoading, currentLocation, inCombat, quests,
    gameOver, gameOverReason, dmUnavailable, lastAction, retryLastAction,
    saveGame, loadGame, listSaves,
    combatStatus, getCombatStatus, combatAttack, combatDefend, combatFlee,
    levelUp, rest, useItem, equipItem,
    shopInventory, browseShop, buyItem, sellItem,
    party, availableRecruits, getParty, recruitMember,
  } = useGameStore()

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    messagesEndRef.current?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!isLoading) inputRef.current?.focus()
  }, [isLoading])

  useEffect(() => {
    if (inCombat) getCombatStatus()
  }, [inCombat])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !isLoading && !gameOver) {
      sendActionStreaming(input.trim())
      setInput('')
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }

  const send = (action) => {
    if (!isLoading && !gameOver) sendActionStreaming(action)
  }

  const { canLevelUp } = getXpProgress(character)
  const activeQuestCount = (quests || []).filter(
    (q) => !['COMPLETE', 'completed', 'FAILED', 'failed'].includes(q.status)
  ).length

  const closeAll = () => {
    setShowMenu(false); setShowHero(false)
  }

  const openInventory = () => { closeAll(); setShowInventory(true) }
  const openQuests = () => { closeAll(); setShowQuests(true) }
  const openMap = () => { closeAll(); setShowMap(true) }
  const openRest = () => { closeAll(); setShowRest(true) }
  const openSave = () => { closeAll(); setSaveError(null); setShowSave(true) }
  const openShop = () => { closeAll(); useGameStore.setState({ shopInventory: null }); browseShop(); setShowShop(true) }
  const openParty = () => { closeAll(); getParty(); setShowParty(true) }
  const openLoad = async () => {
    closeAll()
    const list = await listSaves()
    setSaves(list)
    setShowLoad(true)
  }

  const handleLeave = () => {
    if (window.confirm('Leave this adventure? Unsaved progress may be lost.')) {
      onLeaveGame?.()
    }
  }

  const handleSaveSlot = async (slot) => {
    setSaveError(null)
    const result = await saveGame(slot, `Slot ${slot} — ${character?.name || 'Hero'}`)
    if (result?.success) setShowSave(false)
    else setSaveError(result?.message || 'Could not save.')
  }

  const handleLoadFile = async (filepath) => {
    const result = await loadGame(filepath)
    if (result?.success) setShowLoad(false)
  }

  const lastMsg = messages[messages.length - 1]
  const showThinking =
    isLoading &&
    messages.length > 0 &&
    !lastMsg?.isStreaming &&
    !(lastMsg?.type === 'dm' && lastMsg?.rollResult && !lastMsg?.content?.trim())

  return (
    <div className="h-[100dvh] flex flex-col bg-[var(--bg)] overflow-hidden">
      <TopBar
        character={character}
        currentLocation={currentLocation}
        inCombat={inCombat}
        questCount={activeQuestCount}
        onOpenHero={() => setShowHero(true)}
        onOpenInventory={openInventory}
        onOpenMap={openMap}
        onOpenQuests={openQuests}
        onOpenMenu={() => setShowMenu(true)}
      />

      {/* Story */}
      <div className="relative z-10 flex-1 overflow-y-auto">
        <div className="max-w-[42rem] mx-auto w-full px-5 sm:px-6 py-8 sm:py-12 min-h-full">
          {messages.length === 0 && !isLoading ? (
            <div className="h-full min-h-[50vh] flex flex-col items-center justify-center text-center gap-4">
              <span className="text-[var(--gold)] text-2xl" aria-hidden>✦</span>
              <p className="font-read italic text-[var(--ink-2)] text-lg max-w-sm">
                Your tale awaits. Describe what you do, and the world will answer.
              </p>
              <button
                type="button"
                onClick={() => send('I take in my surroundings.')}
                className="btn btn-ghost focus-ring px-4 py-2 text-sm"
              >
                Look around
              </button>
            </div>
          ) : (
            <div className="space-y-7">
              {messages.map((msg, i) => (
                <StoryEntry
                  key={i}
                  message={msg}
                  isOpening={i === 0 && msg.type === 'dm'}
                />
              ))}
              {showThinking && (
                <div className="flex items-center gap-1.5 py-1" aria-live="polite" aria-label="The world stirs">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--gold)] animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--gold)] animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--gold)] animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
              {dmUnavailable && !isLoading && !gameOver && (
                <div
                  className="panel-inset rounded-xl px-4 py-3 border border-[var(--line-strong)] flex items-center justify-between gap-4"
                  role="status"
                >
                  <p className="font-ui text-sm text-[var(--ink-2)]">
                    The Game Master can't be reached right now.
                    {lastAction ? ' Your action can be sent again.' : ' Your tale is ready when they are.'}
                  </p>
                  <button
                    type="button"
                    onClick={() => (lastAction ? retryLastAction() : send('I take in my surroundings.'))}
                    className="btn btn-ghost focus-ring px-3 py-1.5 text-sm shrink-0"
                  >
                    {lastAction ? 'Try again' : 'Begin'}
                  </button>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      <CommandBar
        ref={inputRef}
        input={input}
        setInput={setInput}
        onSubmit={handleSubmit}
        onSuggestion={send}
        isLoading={isLoading}
        inCombat={inCombat}
        gameOver={gameOver}
        combatStatus={combatStatus}
        onAttack={combatAttack}
        onDefend={combatDefend}
        onFlee={combatFlee}
      />

      {/* Hero drawer */}
      <HeroDrawer
        open={showHero}
        onClose={() => setShowHero(false)}
        character={character}
        canLevelUp={canLevelUp}
        onRest={openRest}
        onLevelUp={() => { levelUp(); setShowHero(false) }}
        onSave={openSave}
        onLoad={openLoad}
        onLeave={handleLeave}
      />

      {/* World map */}
      <WorldMap isOpen={showMap} onClose={() => setShowMap(false)} />

      {/* Menu */}
      <Modal open={showMenu} onClose={() => setShowMenu(false)} eyebrow="Adventure" title="Menu" titleId="menu-title" maxWidth="max-w-md">
        <MenuPanel
          questCount={activeQuestCount}
          canLevelUp={canLevelUp}
          onHero={() => { setShowMenu(false); setShowHero(true) }}
          onInventory={openInventory}
          onQuests={openQuests}
          onMap={openMap}
          onShop={openShop}
          onParty={openParty}
          onRest={openRest}
          onLevelUp={() => { setShowMenu(false); levelUp() }}
          onSave={openSave}
          onLoad={openLoad}
          onLeave={handleLeave}
        />
      </Modal>

      <Modal open={showInventory} onClose={() => setShowInventory(false)} eyebrow="Your pack" title="Inventory" titleId="inv-title">
        <InventoryPanel character={character} isLoading={isLoading} onUse={useItem} onEquip={equipItem} />
      </Modal>

      <Modal open={showQuests} onClose={() => setShowQuests(false)} eyebrow="The journal" title="Quests" titleId="quest-title">
        <QuestsPanel quests={quests} />
      </Modal>

      <Modal open={showShop} onClose={() => setShowShop(false)} eyebrow={shopInventory?.owner_name ? `Kept by ${shopInventory.owner_name}` : 'Wares & trade'} title={shopInventory?.shop_name || 'Shop'} titleId="shop-title" maxWidth="max-w-2xl">
        <ShopPanel character={character} shopInventory={shopInventory} isLoading={isLoading} onBuy={buyItem} onSell={sellItem} />
      </Modal>

      <Modal open={showParty} onClose={() => setShowParty(false)} eyebrow="Fellowship" title="Party" titleId="party-title">
        <PartyPanel party={party} availableRecruits={availableRecruits} isLoading={isLoading} onRecruit={recruitMember} />
      </Modal>

      <Modal open={showRest} onClose={() => setShowRest(false)} eyebrow="Recover" title="Rest" titleId="rest-title" maxWidth="max-w-md">
        <RestPanel
          isLoading={isLoading}
          onShortRest={async () => { await rest('short'); setShowRest(false) }}
          onLongRest={async () => { await rest('long'); setShowRest(false) }}
        />
      </Modal>

      <Modal open={showSave} onClose={() => { setShowSave(false); setSaveError(null) }} eyebrow="Remember this moment" title="Save" titleId="save-title" maxWidth="max-w-md">
        <SavePanel character={character} error={saveError} onSaveSlot={handleSaveSlot} />
      </Modal>

      <Modal open={showLoad} onClose={() => setShowLoad(false)} eyebrow="Return to a journey" title="Load" titleId="load-title" maxWidth="max-w-md">
        <LoadPanel saves={saves} onLoad={handleLoadFile} />
      </Modal>

      <Modal
        open={gameOver}
        onClose={() => {}}
        eyebrow="The tale ends"
        title="Game Over"
        titleId="gameover-title"
        maxWidth="max-w-md"
      >
        <div className="space-y-5 text-center">
          <p className="font-read text-[var(--ink-2)] leading-relaxed">
            {gameOverReason || 'Your adventure has come to an end.'}
          </p>
          <button
            type="button"
            onClick={handleLeave}
            className="btn btn-primary focus-ring w-full py-3"
          >
            Return to the hearth
          </button>
        </div>
      </Modal>
    </div>
  )
}
