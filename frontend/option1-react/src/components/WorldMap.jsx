import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, MapPin, Compass, Eye, EyeOff } from 'lucide-react'
import { useGameStore } from '../store/gameStore'

// Fantasy map background gradients
const REGION_COLORS = {
  default: 'from-amber-900/30 to-stone-900/30',
  forest: 'from-green-900/40 to-emerald-950/30',
  village: 'from-amber-800/30 to-yellow-900/20',
  dungeon: 'from-purple-950/40 to-gray-900/50',
  mountain: 'from-slate-700/40 to-gray-800/30',
  water: 'from-blue-900/30 to-cyan-950/40',
}

// Location type icons with colors
const LOCATION_STYLES = {
  '🏠': { color: 'text-amber-400', bg: 'bg-amber-900/50' },
  '🏰': { color: 'text-yellow-400', bg: 'bg-yellow-900/50' },
  '🌲': { color: 'text-green-400', bg: 'bg-green-900/50' },
  '⛏️': { color: 'text-slate-400', bg: 'bg-slate-700/50' },
  '🗡️': { color: 'text-red-400', bg: 'bg-red-900/50' },
  '🏪': { color: 'text-orange-400', bg: 'bg-orange-900/50' },
  '⛪': { color: 'text-purple-400', bg: 'bg-purple-900/50' },
  '🍺': { color: 'text-amber-300', bg: 'bg-amber-800/50' },
  '❓': { color: 'text-gray-500', bg: 'bg-gray-800/50' },
  '📍': { color: 'text-rpg-gold', bg: 'bg-rpg-primary/30' },
}

export default function WorldMap({ isOpen, onClose }) {
  const [locations, setLocations] = useState([])
  const [currentLocation, setCurrentLocation] = useState(null)
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [showFog, setShowFog] = useState(true)
  const mapRef = useRef(null)
  
  const { getDestinations, travel, isLoading } = useGameStore()
  
  // Load map data when opened
  useEffect(() => {
    if (isOpen) {
      loadMapData()
    }
  }, [isOpen])
  
  const loadMapData = async () => {
    const data = await getDestinations()
    setLocations(data.all_locations || [])
    setCurrentLocation(data.current_location)
  }
  
  const handleLocationClick = (location) => {
    if (location.hidden && showFog) return
    setSelectedLocation(location)
  }
  
  const handleTravel = async () => {
    if (!selectedLocation || !selectedLocation.reachable) return
    
    const result = await travel(selectedLocation.id)
    if (result.success) {
      await loadMapData()
      setSelectedLocation(null)
    }
  }
  
  const getLocationStyle = (icon) => {
    return LOCATION_STYLES[icon] || LOCATION_STYLES['📍']
  }
  
  return (
    <AnimatePresence>
      {isOpen && (
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
            className="rpg-card w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <Compass className="text-rpg-gold" size={24} />
                <h2 className="text-2xl font-medieval text-rpg-gold">World Map</h2>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowFog(!showFog)}
                  className="flex items-center gap-2 px-3 py-1 text-sm border border-gray-600 rounded hover:bg-gray-700 transition"
                >
                  {showFog ? <Eye size={16} /> : <EyeOff size={16} />}
                  {showFog ? 'Show Hidden' : 'Hide Unknown'}
                </button>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-700 rounded transition"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            
            {/* Map Container */}
            <div className="flex-1 flex">
              {/* Map Area */}
              <div 
                ref={mapRef}
                className="flex-1 relative bg-gradient-to-br from-stone-900 via-amber-950/20 to-stone-900 overflow-hidden"
                style={{
                  backgroundImage: `
                    radial-gradient(circle at 30% 40%, rgba(34, 197, 94, 0.1) 0%, transparent 40%),
                    radial-gradient(circle at 70% 60%, rgba(59, 130, 246, 0.1) 0%, transparent 30%),
                    radial-gradient(circle at 50% 80%, rgba(168, 85, 247, 0.1) 0%, transparent 35%)
                  `
                }}
              >
                {/* Grid lines for fantasy map feel */}
                <div className="absolute inset-0 opacity-10"
                  style={{
                    backgroundImage: `
                      linear-gradient(to right, rgba(212, 175, 55, 0.3) 1px, transparent 1px),
                      linear-gradient(to bottom, rgba(212, 175, 55, 0.3) 1px, transparent 1px)
                    `,
                    backgroundSize: '50px 50px'
                  }}
                />
                
                {/* Compass Rose */}
                <div className="absolute top-4 right-4 text-4xl opacity-30 select-none">
                  🧭
                </div>
                
                {/* Connection lines between locations */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  {locations.map(loc => {
                    if (!loc.reachable || loc.id === currentLocation?.id) return null
                    const current = currentLocation
                    if (!current) return null
                    
                    return (
                      <line
                        key={`line-${loc.id}`}
                        x1={`${current.map_x * 100}%`}
                        y1={`${current.map_y * 100}%`}
                        x2={`${loc.map_x * 100}%`}
                        y2={`${loc.map_y * 100}%`}
                        stroke="rgba(212, 175, 55, 0.3)"
                        strokeWidth="2"
                        strokeDasharray="5,5"
                      />
                    )
                  })}
                </svg>
                
                {/* Location markers */}
                {locations.map(loc => {
                  const style = getLocationStyle(loc.map_icon)
                  const isSelected = selectedLocation?.id === loc.id
                  const isCurrent = loc.is_current
                  const isHidden = loc.hidden && showFog
                  
                  if (isHidden && loc.map_x === 0 && loc.map_y === 0) return null
                  
                  return (
                    <motion.button
                      key={loc.id}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      whileHover={{ scale: 1.2 }}
                      onClick={() => handleLocationClick(loc)}
                      disabled={isHidden}
                      className={`
                        absolute transform -translate-x-1/2 -translate-y-1/2
                        flex flex-col items-center gap-1 group
                        ${isHidden ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}
                      `}
                      style={{
                        left: `${loc.map_x * 100}%`,
                        top: `${loc.map_y * 100}%`,
                      }}
                    >
                      {/* Marker */}
                      <div className={`
                        w-12 h-12 rounded-full flex items-center justify-center text-2xl
                        border-2 transition-all duration-200
                        ${isCurrent ? 'border-rpg-gold ring-4 ring-rpg-gold/50 animate-pulse' : 'border-gray-600'}
                        ${isSelected ? 'ring-2 ring-white' : ''}
                        ${loc.visited ? style.bg : 'bg-gray-800/50'}
                        ${loc.reachable && !isCurrent ? 'border-green-500/50' : ''}
                      `}>
                        <span className={isCurrent ? 'animate-bounce' : ''}>
                          {loc.map_icon}
                        </span>
                      </div>
                      
                      {/* Label */}
                      <span className={`
                        text-xs font-medieval px-2 py-0.5 rounded bg-black/70 whitespace-nowrap
                        ${isCurrent ? 'text-rpg-gold' : loc.visited ? 'text-white' : 'text-gray-400'}
                        opacity-0 group-hover:opacity-100 transition-opacity
                      `}>
                        {loc.name}
                      </span>
                      
                      {/* Current location indicator */}
                      {isCurrent && (
                        <div className="absolute -top-2 -right-2">
                          <span className="text-lg">👤</span>
                        </div>
                      )}
                    </motion.button>
                  )
                })}
                
                {/* Empty state */}
                {locations.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <MapPin size={48} className="mx-auto mb-4 opacity-50" />
                      <p>No map data available</p>
                      <p className="text-sm mt-2">Explore the world to discover locations!</p>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Sidebar - Location Details */}
              <div className="w-72 border-l border-gray-700 p-4 bg-black/30">
                {selectedLocation ? (
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-4"
                  >
                    <div className="text-center">
                      <span className="text-4xl">{selectedLocation.map_icon}</span>
                      <h3 className="text-xl font-medieval text-rpg-gold mt-2">
                        {selectedLocation.name}
                      </h3>
                      <div className="flex items-center justify-center gap-2 mt-1">
                        {selectedLocation.visited && (
                          <span className="text-xs text-green-400 flex items-center gap-1">
                            <Eye size={12} /> Visited
                          </span>
                        )}
                        {selectedLocation.is_current && (
                          <span className="text-xs text-rpg-gold flex items-center gap-1">
                            📍 You are here
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {selectedLocation.reachable && !selectedLocation.is_current && (
                      <button
                        onClick={handleTravel}
                        disabled={isLoading}
                        className="w-full rpg-button py-3 flex items-center justify-center gap-2"
                      >
                        <Compass size={18} />
                        Travel Here
                      </button>
                    )}
                    
                    {!selectedLocation.reachable && !selectedLocation.is_current && (
                      <div className="text-center text-gray-500 text-sm py-4">
                        <p>🚫 Cannot reach from here</p>
                        <p className="mt-1">Find a path to this location</p>
                      </div>
                    )}
                  </motion.div>
                ) : (
                  <div className="text-center text-gray-400 py-8">
                    <MapPin size={32} className="mx-auto mb-3 opacity-50" />
                    <p>Select a location</p>
                    <p className="text-sm mt-1">Click on a marker to view details</p>
                  </div>
                )}
                
                {/* Current Location Info */}
                {currentLocation && (
                  <div className="mt-6 pt-4 border-t border-gray-700">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Current Location</p>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{currentLocation.map_icon || '📍'}</span>
                      <span className="font-medieval text-rpg-gold">{currentLocation.name}</span>
                    </div>
                  </div>
                )}
                
                {/* Legend */}
                <div className="mt-6 pt-4 border-t border-gray-700">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Legend</p>
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full border-2 border-rpg-gold"></div>
                      <span>Current location</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full border-2 border-green-500"></div>
                      <span>Reachable</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full border-2 border-gray-600 opacity-50"></div>
                      <span>Undiscovered</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
