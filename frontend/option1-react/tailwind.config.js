/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        'bg-deep': 'var(--bg-deep)',
        surface: 'var(--surface)',
        'surface-2': 'var(--surface-2)',
        line: 'var(--line)',
        'line-strong': 'var(--line-strong)',
        gold: 'var(--gold)',
        'gold-bright': 'var(--gold-bright)',
        ember: 'var(--ember)',
        sage: 'var(--sage)',
        ink: 'var(--ink)',
        'ink-2': 'var(--ink-2)',
        'ink-3': 'var(--ink-3)',
        // Legacy aliases mapped to new palette so older components keep working
        rpg: {
          ink: 'var(--bg)',
          'ink-deep': 'var(--bg-deep)',
          paper: 'var(--surface)',
          'paper-raised': 'var(--surface-2)',
          'paper-inset': 'var(--bg-deep)',
          border: 'var(--line-strong)',
          'border-gold': 'var(--line-strong)',
          gold: 'var(--gold)',
          'gold-dim': 'var(--ink-3)',
          accent: 'var(--gold)',
          health: 'var(--ember)',
          mana: '#6f93b0',
          text: 'var(--ink)',
          'text-secondary': 'var(--ink-2)',
          'text-muted': 'var(--ink-3)',
          'dm-bubble': 'var(--surface)',
          'player-bubble': 'var(--surface-2)',
          dark: 'var(--bg)',
          bg: 'var(--bg)',
          surface: 'var(--surface-2)',
          panel: 'var(--surface)',
          primary: 'var(--gold)',
        },
      },
      fontFamily: {
        display: ['Cormorant Garamond', 'Georgia', 'serif'],
        read: ['Spectral', 'Georgia', 'serif'],
        ui: ['DM Sans', 'system-ui', 'sans-serif'],
        // legacy aliases
        story: ['Spectral', 'Georgia', 'serif'],
        medieval: ['Cormorant Garamond', 'serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        paper: '0 1px 0 rgba(194, 168, 104, 0.1), 0 8px 24px rgba(0, 0, 0, 0.45)',
        'paper-lg': '0 1px 0 rgba(194, 168, 104, 0.16), 0 22px 55px rgba(0, 0, 0, 0.6)',
        glow: '0 0 24px rgba(194, 168, 104, 0.14)',
      },
      animation: {
        'spin-slow': 'spin 12s linear infinite',
        'fade-up': 'fadeUp 0.5s ease both',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
