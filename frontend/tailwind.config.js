/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#ecfdf5',
          100: '#d1fae5',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b'
        },
        ink: {
          500: '#64748b',
          700: '#334155',
          900: '#0f172a'
        },
        status: {
          success: '#047857',
          warning: '#b45309',
          error: '#be123c',
          info: '#2563eb',
          draft: '#7c3aed',
          published: '#047857',
          archived: '#64748b',
          completed: '#0f766e',
          pending: '#b45309',
          failed: '#be123c'
        }
      },
      borderRadius: {
        control: '0.375rem',
        panel: '0.5rem'
      },
      boxShadow: {
        panel: '0 1px 2px 0 rgb(15 23 42 / 0.06)',
        focus: '0 0 0 3px rgb(5 150 105 / 0.22)'
      },
      fontSize: {
        'page-title': ['1.875rem', { lineHeight: '2.25rem', fontWeight: '700' }],
        'section-title': ['1rem', { lineHeight: '1.5rem', fontWeight: '700' }]
      },
      screens: {
        xs: '420px'
      }
    }
  },
  plugins: []
};
