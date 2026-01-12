/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark Fantasy theme (default from UI_DESIGN_SPEC.md)
        rpg: {
          dark: '#1A1A1A',        // Background - Near Black
          bg: '#1A1A1A',          // Background
          surface: '#2D2D2D',     // Surface - Dark Gray
          panel: '#2D2D2D',       // Panel surface
          primary: '#D4AF37',     // Gold primary
          accent: '#8B4513',      // Saddle Brown accent
          gold: '#D4AF37',        // Gold
          silver: '#c0c0c0',      // Silver
          health: '#DC143C',      // Crimson for health/errors
          mana: '#1e88e5',        // Blue for mana
          xp: '#9932CC',          // Purple for XP
          text: '#F5F5DC',        // Beige text primary
          'text-secondary': '#A0A0A0', // Gray text secondary
          'dm-bubble': '#2D2D2D', // DM message bubble
          'player-bubble': '#3D3D1A', // Player message bubble
        }
      },
      fontFamily: {
        medieval: ['Cinzel', 'serif'],
        body: ['Inter', 'sans-serif'],
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 3s ease-in-out infinite',
        'shake': 'shake 0.5s ease-in-out',
        'spin-slow': 'spin 8s linear infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #e94560, 0 0 10px #e94560' },
          '100%': { boxShadow: '0 0 20px #e94560, 0 0 30px #e94560' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-5px)' },
          '75%': { transform: 'translateX(5px)' },
        }
      }
    },
  },
  plugins: [],
}
