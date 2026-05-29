/** @type {import('tailwindcss').Config} */
export default {
  content: [
    'components/**/*.{vue,ts}',
    'layouts/**/*.vue',
    'pages/**/*.vue',
    'app.vue',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        'primary-light': 'var(--color-primary-light)',
        'primary-dark': 'var(--color-primary-dark)',
        surface: {
          DEFAULT: 'var(--color-surface)',
          elevated: 'var(--color-surface-elevated)',
        },
        foreground: 'var(--color-text)',
        secondary: 'var(--color-secondary)',
        border: {
          DEFAULT: 'var(--color-border)',
          light: 'var(--color-border-light)',
        },
        separator: 'var(--color-separator)',
        'input-bg': 'var(--color-input-bg)',
        'input-border': 'var(--color-input-border)',
        hover: 'var(--color-hover)',
        'btn-secondary': 'var(--color-btn-secondary)',
        'btn-secondary-hover': 'var(--color-btn-secondary-hover)',
        'muted-surface': 'var(--color-muted-surface)',
        danger: 'var(--color-danger)',
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        accent: 'var(--color-primary)',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        xl: '12px',
      },
    },
  },
  plugins: [],
}
