import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'hey-green': '#00C389',
        'hey-green-dark': '#00A074',
        'hey-green-light': 'rgba(0,195,137,0.10)',
        'hey-purple': '#6B4EFF',
        'hey-purple-light': 'rgba(107,78,255,0.12)',
        'hey-orange': '#FF8C42',
        'hey-dark': '#0D1117',
        'hey-surface': '#161B22',
        'hey-card': '#1C2128',
        'hey-border': '#21262D',
        'hey-text': '#E2E8F0',
        'hey-muted': '#8B949E',
        'hey-faint': '#484F58',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
