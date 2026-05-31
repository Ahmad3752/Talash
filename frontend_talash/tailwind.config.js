/** @type {import('tailwindcss').Config} */
export default {
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#0a0f1e',
          teal: '#00ffcc',
          green: '#10b981',
          amber: '#f59e0b',
          orange: '#f97316',
          rose: '#f43f5e',
        },
      },
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
        inter: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [
    function ({ addComponents }) {
      addComponents({
        '.glass-card': {
          '@apply': 'bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden',
        },
        '.glass-card-hover': {
          '@apply': 'transition-all duration-300 hover:bg-white/10 hover:border-white/20',
        },
        '.stat-chip': {
          '@apply': 'flex flex-col p-4 glass-card',
        },
        '.stat-label': {
          '@apply': 'text-xs uppercase tracking-wider text-slate-400 font-mono mb-1',
        },
        '.stat-value': {
          '@apply': 'text-2xl font-bold font-mono text-brand-teal',
        },
      });
    },
  ],
};

