import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:           '#0A0F1E',
        surface:      '#111827',
        surface2:     '#1A2340',
        border:       '#2A3560',
        accent:       '#4F8EF7',
        'accent-dim': '#1E3A6E',
        text:         '#E8F0FF',
        muted:        '#64748B',
        dim:          '#94A3B8',
        success:      '#10B981',
        warning:      '#F59E0B',
        error:        '#EF4444',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
