import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence, useMotionValue, useTransform } from 'framer-motion'
import { X, MapPin, Compass, Eye, EyeOff, ZoomIn, ZoomOut, Maximize2, Navigation, Footprints } from 'lucide-react'
import { useGameStore } from '../store/gameStore'

// Fantasy map region gradients with more visual depth
const REGION_COLORS = {
  default: 'from-amber-900/30 to-stone-900/30',
  forest: 'from-green-900/50 to-emerald-950/40',
  village: 'from-amber-700/40 to-yellow-900/30',
  dungeon: 'from-purple-950/50 to-gray-900/60',
  mountain: 'from-slate-600/50 to-gray-800/40',
  water: 'from-blue-800/40 to-cyan-950/50',
  cave: 'from-stone-900/60 to-gray-950/70',
}

// Enhanced location type icons with colors and glow effects
const LOCATION_STYLES = {
  '🏠': { color: 'text-amber-400', bg: 'bg-amber-900/60', glow: 'shadow-amber-500/30' },
  '🏰': { color: 'text-yellow-400', bg: 'bg-yellow-900/60', glow: 'shadow-yellow-500/30' },
  '🌲': { color: 'text-green-400', bg: 'bg-green-900/60', glow: 'shadow-green-500/30' },
  '🌳': { color: 'text-emerald-400', bg: 'bg-emerald-900/60', glow: 'shadow-emerald-500/30' },
  '⛏️': { color: 'text-slate-400', bg: 'bg-slate-700/60', glow: 'shadow-slate-500/30' },
  '🗡️': { color: 'text-red-400', bg: 'bg-red-900/60', glow: 'shadow-red-500/30' },
  '🏪': { color: 'text-orange-400', bg: 'bg-orange-900/60', glow: 'shadow-orange-500/30' },
  '⛪': { color: 'text-purple-400', bg: 'bg-purple-900/60', glow: 'shadow-purple-500/30' },
  '🍺': { color: 'text-amber-300', bg: 'bg-amber-800/60', glow: 'shadow-amber-400/30' },
  '🍻': { color: 'text-yellow-300', bg: 'bg-yellow-800/60', glow: 'shadow-yellow-400/30' },
  '🛠️': { color: 'text-orange-300', bg: 'bg-orange-800/60', glow: 'shadow-orange-400/30' },
  '🏛️': { color: 'text-stone-300', bg: 'bg-stone-700/60', glow: 'shadow-stone-400/30' },
  '⚠️': { color: 'text-yellow-500', bg: 'bg-yellow-900/60', glow: 'shadow-yellow-600/40' },
  '🕳️': { color: 'text-gray-400', bg: 'bg-gray-800/70', glow: 'shadow-gray-500/30' },
  '💀': { color: 'text-red-500', bg: 'bg-red-950/70', glow: 'shadow-red-600/40' },
  '🔮': { color: 'text-purple-300', bg: 'bg-purple-900/60', glow: 'shadow-purple-400/50' },
  '❓': { color: 'text-gray-500', bg: 'bg-gray-800/50', glow: 'shadow-gray-500/20' },
  '📍': { color: 'text-rpg-gold', bg: 'bg-rpg-primary/40', glow: 'shadow-rpg-gold/40' },
}

export default function WorldMap({ isOpen, onClose }) {
  const [locations, setLocations] = useState([])
  const [currentLocation, setCurrentLocation] = useState(null)
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [showFog, setShowFog] = useState(true)
  const [hoveredLocation, setHoveredLocation] = useState(null)
  
  // Pan and zoom state
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  
  const mapRef = useRef(null)
  const containerRef = useRef(null)
  
  const { getDestinations, travel, isLoading } = useGameStore()
  
  // Zoom limits
  const MIN_ZOOM = 0.5
  const MAX_ZOOM = 3
  const ZOOM_STEP = 0.25
  
  // Load map data when opened
  useEffect(() => {
    if (isOpen) {
      loadMapData()
      // Reset view when opening
      setScale(1)
      setPosition({ x: 0, y: 0 })
    }
  }, [isOpen])
  
  const loadMapData = async () => {
    const data = await getDestinations()
    setLocations(data.all_locations || [])
    setCurrentLocation(data.current_location)
    
    // Auto-center on current location
    if (data.current_location) {
      const { map_x, map_y } = data.current_location
      // Center the view on current location (offset from center)
      setPosition({
        x: (0.5 - map_x) * 100,
        y: (0.5 - map_y) * 100
      })
    }
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
  
  // Zoom handlers
  const handleZoomIn = () => {
    setScale(prev => Math.min(MAX_ZOOM, prev + ZOOM_STEP))
  }
  
  const handleZoomOut = () => {
    setScale(prev => Math.max(MIN_ZOOM, prev - ZOOM_STEP))
  }
  
  const handleResetView = () => {
    setScale(1)
    if (currentLocation) {
      setPosition({
        x: (0.5 - currentLocation.map_x) * 100,
        y: (0.5 - currentLocation.map_y) * 100
      })
    } else {
      setPosition({ x: 0, y: 0 })
    }
  }
  
  // Pan handlers
  const handleMouseDown = (e) => {
    if (e.button !== 0) return // Only left click
    setIsDragging(true)
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
  }
  
  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    })
  }, [isDragging, dragStart])
  
  const handleMouseUp = () => {
    setIsDragging(false)
  }
  
  // Mouse wheel zoom
  const handleWheel = (e) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
    setScale(prev => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, prev + delta)))
  }
  
  // Touch handlers for mobile
  const [touchStart, setTouchStart] = useState(null)
  const [touchScale, setTouchScale] = useState(null)
  
  const handleTouchStart = (e) => {
    if (e.touches.length === 1) {
      setTouchStart({ x: e.touches[0].clientX - position.x, y: e.touches[0].clientY - position.y })
    } else if (e.touches.length === 2) {
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      )
      setTouchScale({ dist, initialScale: scale })
    }
  }
  
  const handleTouchMove = (e) => {
    if (e.touches.length === 1 && touchStart) {
      setPosition({
        x: e.touches[0].clientX - touchStart.x,
        y: e.touches[0].clientY - touchStart.y
      })
    } else if (e.touches.length === 2 && touchScale) {
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      )
      const newScale = touchScale.initialScale * (dist / touchScale.dist)
      setScale(Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newScale)))
    }
  }
  
  const handleTouchEnd = () => {
    setTouchStart(null)
    setTouchScale(null)
  }
  
  // Calculate distance between two locations (for path animation)
  const getDistance = (loc1, loc2) => {
    return Math.sqrt(Math.pow(loc2.map_x - loc1.map_x, 2) + Math.pow(loc2.map_y - loc1.map_y, 2))
  }
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-2 md:p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="rpg-card w-full max-w-6xl h-[90vh] flex flex-col overflow-hidden border-2 border-rpg-gold/30"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-3 md:p-4 border-b border-gray-700 bg-gradient-to-r from-rpg-primary/20 to-transparent">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Compass className="text-rpg-gold animate-spin-slow" size={28} />
                  <div className="absolute inset-0 blur-sm bg-rpg-gold/30 rounded-full" />
                </div>
                <div>
                  <h2 className="text-xl md:text-2xl font-medieval text-rpg-gold">World Map</h2>
                  <p className="text-xs text-gray-400 hidden md:block">
                    {locations.filter(l => l.visited).length} of {locations.length} locations discovered
                  </p>
                </div>
              </div>
              
              {/* Toolbar */}
              <div className="flex items-center gap-2">
                {/* Zoom controls */}
                <div className="hidden md:flex items-center gap-1 mr-2 bg-gray-800/50 rounded-lg p-1">
                  <button
                    onClick={handleZoomOut}
                    className="p-1.5 hover:bg-gray-700 rounded transition text-gray-400 hover:text-white"
                    title="Zoom out"
                  >
                    <ZoomOut size={16} />
                  </button>
                  <span className="text-xs text-gray-400 w-12 text-center">{Math.round(scale * 100)}%</span>
                  <button
                    onClick={handleZoomIn}
                    className="p-1.5 hover:bg-gray-700 rounded transition text-gray-400 hover:text-white"
                    title="Zoom in"
                  >
                    <ZoomIn size={16} />
                  </button>
                  <button
                    onClick={handleResetView}
                    className="p-1.5 hover:bg-gray-700 rounded transition text-gray-400 hover:text-white ml-1 border-l border-gray-600 pl-2"
                    title="Reset view"
                  >
                    <Maximize2 size={16} />
                  </button>
                </div>
                
                {/* Fog toggle */}
                <button
                  onClick={() => setShowFog(!showFog)}
                  className={`
                    flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition
                    ${showFog ? 'bg-gray-800 border border-gray-600 hover:bg-gray-700' : 'bg-purple-900/50 border border-purple-500/50'}
                  `}
                >
                  {showFog ? <Eye size={16} /> : <EyeOff size={16} />}
                  <span className="hidden md:inline">{showFog ? 'Show All' : 'Hide Unknown'}</span>
                </button>
                
                {/* Close */}
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-700 rounded-lg transition ml-2"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            
            {/* Map Container */}
            <div className="flex-1 flex overflow-hidden">
              {/* Map Area */}
              <div 
                ref={containerRef}
                className="flex-1 relative overflow-hidden cursor-grab active:cursor-grabbing select-none"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={handleWheel}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
              >
                {/* Map parchment background */}
                <div 
                  ref={mapRef}
                  className="absolute transition-transform duration-75"
                  style={{
                    width: '200%',
                    height: '200%',
                    left: '-50%',
                    top: '-50%',
                    transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                    transformOrigin: 'center center',
                  }}
                >
                  {/* Parchment texture background */}
                  <div className="absolute inset-0 bg-gradient-to-br from-amber-950/90 via-stone-900 to-amber-950/80" />
                  
                  {/* Noise texture overlay */}
                  <div 
                    className="absolute inset-0 opacity-30"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
                    }}
                  />
                  
                  {/* Region color overlays */}
                  <div className="absolute inset-0">
                    {/* Forest region glow */}
                    <div 
                      className="absolute rounded-full blur-3xl opacity-40"
                      style={{
                        width: '40%',
                        height: '50%',
                        left: '20%',
                        top: '35%',
                        background: 'radial-gradient(circle, rgba(34, 197, 94, 0.3) 0%, transparent 70%)'
                      }}
                    />
                    {/* Village region glow */}
                    <div 
                      className="absolute rounded-full blur-3xl opacity-40"
                      style={{
                        width: '30%',
                        height: '25%',
                        left: '35%',
                        top: '20%',
                        background: 'radial-gradient(circle, rgba(251, 191, 36, 0.3) 0%, transparent 70%)'
                      }}
                    />
                    {/* Cave/dungeon region glow */}
                    <div 
                      className="absolute rounded-full blur-3xl opacity-40"
                      style={{
                        width: '35%',
                        height: '40%',
                        left: '50%',
                        top: '45%',
                        background: 'radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, transparent 70%)'
                      }}
                    />
                  </div>
                  
                  {/* Fantasy grid lines */}
                  <div 
                    className="absolute inset-0 opacity-5"
                    style={{
                      backgroundImage: `
                        linear-gradient(to right, rgba(212, 175, 55, 0.5) 1px, transparent 1px),
                        linear-gradient(to bottom, rgba(212, 175, 55, 0.5) 1px, transparent 1px)
                      `,
                      backgroundSize: '8% 8%'
                    }}
                  />
                  
                  {/* Decorative border */}
                  <div className="absolute inset-[15%] border-2 border-rpg-gold/10 rounded-lg" />
                  <div className="absolute inset-[16%] border border-rpg-gold/5 rounded-lg" />
                  
                  {/* Compass Rose */}
                  <div className="absolute top-[18%] right-[18%] opacity-20">
                    <div className="relative w-24 h-24">
                      <div className="absolute inset-0 flex items-center justify-center text-5xl">🧭</div>
                      <div className="absolute -top-4 left-1/2 -translate-x-1/2 text-xs text-rpg-gold font-medieval">N</div>
                      <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-xs text-rpg-gold font-medieval">S</div>
                      <div className="absolute top-1/2 -left-4 -translate-y-1/2 text-xs text-rpg-gold font-medieval">W</div>
                      <div className="absolute top-1/2 -right-4 -translate-y-1/2 text-xs text-rpg-gold font-medieval">E</div>
                    </div>
                  </div>
                  
                  {/* Connection lines between locations */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ left: '25%', top: '25%', width: '50%', height: '50%' }}>
                    <defs>
                      {/* Path gradient */}
                      <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="rgba(212, 175, 55, 0.6)" />
                        <stop offset="50%" stopColor="rgba(212, 175, 55, 0.3)" />
                        <stop offset="100%" stopColor="rgba(212, 175, 55, 0.6)" />
                      </linearGradient>
                      {/* Animated dash */}
                      <pattern id="pathPattern" patternUnits="userSpaceOnUse" width="20" height="1">
                        <rect width="10" height="1" fill="rgba(212, 175, 55, 0.5)">
                          <animate attributeName="x" from="0" to="20" dur="1s" repeatCount="indefinite" />
                        </rect>
                      </pattern>
                    </defs>
                    
                    {/* Draw paths from current location to reachable locations */}
                    {locations.map(loc => {
                      if (!loc.reachable || loc.id === currentLocation?.id) return null
                      const current = currentLocation
                      if (!current) return null
                      
                      const isSelected = selectedLocation?.id === loc.id
                      const isHovered = hoveredLocation?.id === loc.id
                      
                      return (
                        <g key={`path-${loc.id}`}>
                          {/* Glow effect for selected/hovered path */}
                          {(isSelected || isHovered) && (
                            <line
                              x1={`${current.map_x * 100}%`}
                              y1={`${current.map_y * 100}%`}
                              x2={`${loc.map_x * 100}%`}
                              y2={`${loc.map_y * 100}%`}
                              stroke="rgba(212, 175, 55, 0.3)"
                              strokeWidth="8"
                              className="blur-sm"
                            />
                          )}
                          {/* Main path */}
                          <line
                            x1={`${current.map_x * 100}%`}
                            y1={`${current.map_y * 100}%`}
                            x2={`${loc.map_x * 100}%`}
                            y2={`${loc.map_y * 100}%`}
                            stroke={isSelected || isHovered ? "rgba(212, 175, 55, 0.8)" : "rgba(212, 175, 55, 0.3)"}
                            strokeWidth={isSelected || isHovered ? "3" : "2"}
                            strokeDasharray={isSelected || isHovered ? "none" : "8,4"}
                            className="transition-all duration-300"
                          />
                          {/* Arrow indicator for selected */}
                          {isSelected && (
                            <circle
                              cx={`${(current.map_x + loc.map_x) / 2 * 100}%`}
                              cy={`${(current.map_y + loc.map_y) / 2 * 100}%`}
                              r="6"
                              fill="rgba(212, 175, 55, 0.8)"
                              className="animate-pulse"
                            />
                          )}
                        </g>
                      )
                    })}
                  </svg>
                  
                  {/* Location markers */}
                  <div className="absolute" style={{ left: '25%', top: '25%', width: '50%', height: '50%' }}>
                    {locations.map(loc => {
                      const style = getLocationStyle(loc.map_icon)
                      const isSelected = selectedLocation?.id === loc.id
                      const isHovered = hoveredLocation?.id === loc.id
                      const isCurrent = loc.is_current
                      const isHidden = loc.hidden && showFog
                      
                      if (isHidden && loc.map_x === 0 && loc.map_y === 0) return null
                      
                      return (
                        <motion.button
                          key={loc.id}
                          initial={{ scale: 0, opacity: 0 }}
                          animate={{ 
                            scale: isHovered ? 1.2 : 1, 
                            opacity: isHidden ? 0.3 : 1 
                          }}
                          whileHover={{ scale: 1.3 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleLocationClick(loc)}
                          onMouseEnter={() => setHoveredLocation(loc)}
                          onMouseLeave={() => setHoveredLocation(null)}
                          disabled={isHidden}
                          className={`
                            absolute transform -translate-x-1/2 -translate-y-1/2
                            flex flex-col items-center gap-1 group z-10
                            ${isHidden ? 'cursor-not-allowed' : 'cursor-pointer'}
                          `}
                          style={{
                            left: `${loc.map_x * 100}%`,
                            top: `${loc.map_y * 100}%`,
                          }}
                        >
                          {/* Marker glow effect */}
                          {(isCurrent || isSelected) && (
                            <div className={`
                              absolute w-20 h-20 -top-4 -left-4 rounded-full blur-xl
                              ${isCurrent ? 'bg-rpg-gold/40 animate-pulse' : 'bg-white/20'}
                            `} />
                          )}
                          
                          {/* Marker */}
                          <div className={`
                            relative w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center text-2xl md:text-3xl
                            border-2 transition-all duration-300 shadow-lg
                            ${isCurrent ? 'border-rpg-gold ring-4 ring-rpg-gold/50' : 'border-gray-600/80'}
                            ${isSelected ? 'ring-2 ring-white border-white' : ''}
                            ${loc.visited ? style.bg : 'bg-gray-800/70'}
                            ${loc.reachable && !isCurrent ? 'border-green-500/70 hover:border-green-400' : ''}
                            ${style.glow} shadow-xl
                          `}>
                            <span className={`
                              ${isCurrent ? 'animate-bounce' : ''} 
                              drop-shadow-lg
                              ${loc.visited ? '' : 'grayscale opacity-70'}
                            `}>
                              {loc.map_icon}
                            </span>
                            
                            {/* Visit indicator dot */}
                            {loc.visited && !isCurrent && (
                              <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-green-400 rounded-full" />
                            )}
                          </div>
                          
                          {/* Current location player marker */}
                          {isCurrent && (
                            <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-rpg-gold text-black text-xs px-2 py-0.5 rounded-full font-bold shadow-lg whitespace-nowrap">
                              👤 You
                            </div>
                          )}
                          
                          {/* Label - always visible for current/selected, hover for others */}
                          <motion.span 
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ 
                              opacity: isCurrent || isSelected || isHovered ? 1 : 0,
                              y: isCurrent || isSelected || isHovered ? 0 : -5
                            }}
                            className={`
                              text-xs md:text-sm font-medieval px-2 py-1 rounded bg-black/80 whitespace-nowrap
                              border border-gray-700/50 shadow-lg
                              ${isCurrent ? 'text-rpg-gold' : loc.visited ? 'text-white' : 'text-gray-400'}
                            `}
                          >
                            {loc.name}
                            {loc.reachable && !isCurrent && (
                              <span className="ml-1 text-green-400">→</span>
                            )}
                          </motion.span>
                        </motion.button>
                      )
                    })}
                  </div>
                </div>
                
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
                
                {/* Mini-map / Overview in corner */}
                <div className="absolute bottom-4 left-4 w-32 h-24 bg-black/60 border border-gray-700 rounded-lg overflow-hidden hidden md:block">
                  <div className="absolute inset-0 bg-gradient-to-br from-amber-950/50 to-stone-900/50">
                    {locations.map(loc => (
                      <div
                        key={`mini-${loc.id}`}
                        className={`
                          absolute w-2 h-2 rounded-full transform -translate-x-1/2 -translate-y-1/2
                          ${loc.is_current ? 'bg-rpg-gold animate-pulse w-3 h-3' : loc.visited ? 'bg-green-500/60' : 'bg-gray-600/40'}
                        `}
                        style={{
                          left: `${loc.map_x * 100}%`,
                          top: `${loc.map_y * 100}%`,
                        }}
                      />
                    ))}
                  </div>
                  <div className="absolute bottom-1 right-1 text-[10px] text-gray-500">Overview</div>
                </div>
                
                {/* Zoom controls for mobile */}
                <div className="absolute bottom-4 right-4 flex flex-col gap-2 md:hidden">
                  <button
                    onClick={handleZoomIn}
                    className="w-10 h-10 bg-black/70 border border-gray-600 rounded-lg flex items-center justify-center text-white"
                  >
                    <ZoomIn size={20} />
                  </button>
                  <button
                    onClick={handleZoomOut}
                    className="w-10 h-10 bg-black/70 border border-gray-600 rounded-lg flex items-center justify-center text-white"
                  >
                    <ZoomOut size={20} />
                  </button>
                  <button
                    onClick={handleResetView}
                    className="w-10 h-10 bg-black/70 border border-gray-600 rounded-lg flex items-center justify-center text-white"
                  >
                    <Navigation size={20} />
                  </button>
                </div>
              </div>
              
              {/* Sidebar - Location Details */}
              <div className="w-64 md:w-80 border-l border-gray-700 bg-gradient-to-b from-gray-900/95 to-black/95 flex flex-col">
                {/* Selected Location Details */}
                <div className="flex-1 p-4 overflow-y-auto">
                  {selectedLocation ? (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="space-y-4"
                    >
                      {/* Location header */}
                      <div className="text-center relative">
                        <div className="w-20 h-20 mx-auto mb-3 rounded-full bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-rpg-gold/30 flex items-center justify-center shadow-xl">
                          <span className="text-4xl drop-shadow-lg">{selectedLocation.map_icon}</span>
                        </div>
                        <h3 className="text-xl font-medieval text-rpg-gold">
                          {selectedLocation.name}
                        </h3>
                        <div className="flex items-center justify-center gap-3 mt-2">
                          {selectedLocation.visited && (
                            <span className="text-xs text-green-400 flex items-center gap-1 bg-green-900/30 px-2 py-1 rounded-full">
                              <Eye size={12} /> Visited
                            </span>
                          )}
                          {selectedLocation.is_current && (
                            <span className="text-xs text-rpg-gold flex items-center gap-1 bg-rpg-gold/20 px-2 py-1 rounded-full">
                              📍 You are here
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Distance indicator */}
                      {!selectedLocation.is_current && currentLocation && (
                        <div className="text-center text-gray-400 text-sm flex items-center justify-center gap-2">
                          <Footprints size={14} />
                          <span>
                            {Math.round(getDistance(currentLocation, selectedLocation) * 1000) / 10} leagues away
                          </span>
                        </div>
                      )}
                      
                      {/* Travel button */}
                      {selectedLocation.reachable && !selectedLocation.is_current && (
                        <button
                          onClick={handleTravel}
                          disabled={isLoading}
                          className="w-full rpg-button py-3 flex items-center justify-center gap-2 text-lg group"
                        >
                          <Navigation size={20} className="group-hover:translate-x-1 transition-transform" />
                          Travel Here
                        </button>
                      )}
                      
                      {/* Cannot reach message */}
                      {!selectedLocation.reachable && !selectedLocation.is_current && (
                        <div className="text-center text-gray-500 text-sm py-4 bg-gray-800/30 rounded-lg border border-gray-700/50">
                          <p className="text-yellow-500/80">🚫 Cannot reach from here</p>
                          <p className="mt-2 text-xs">Find a path to this location first</p>
                        </div>
                      )}
                    </motion.div>
                  ) : (
                    <div className="text-center text-gray-400 py-12">
                      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800/50 flex items-center justify-center">
                        <MapPin size={32} className="opacity-50" />
                      </div>
                      <p className="font-medieval text-lg">Select a Location</p>
                      <p className="text-sm mt-2 text-gray-500">Click on a marker to view details</p>
                      <p className="text-xs mt-4 text-gray-600">Tip: Use scroll to zoom, drag to pan</p>
                    </div>
                  )}
                </div>
                
                {/* Current Location Info */}
                {currentLocation && (
                  <div className="p-4 border-t border-gray-700 bg-black/30">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-2">
                      <span className="w-2 h-2 bg-rpg-gold rounded-full animate-pulse" />
                      Current Location
                    </p>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-rpg-gold/20 border border-rpg-gold/50 flex items-center justify-center">
                        <span className="text-xl">{currentLocation.map_icon || '📍'}</span>
                      </div>
                      <span className="font-medieval text-rpg-gold">{currentLocation.name}</span>
                    </div>
                  </div>
                )}
                
                {/* Legend */}
                <div className="p-4 border-t border-gray-700 bg-gradient-to-t from-black/50 to-transparent">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">Legend</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full border-2 border-rpg-gold bg-rpg-gold/20" />
                      <span className="text-gray-400">Current</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full border-2 border-green-500 bg-green-900/30" />
                      <span className="text-gray-400">Reachable</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full border-2 border-gray-500 bg-gray-800/50" />
                      <span className="text-gray-400">Visited</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full border-2 border-gray-700 bg-gray-900/50 opacity-50" />
                      <span className="text-gray-400">Unknown</span>
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
