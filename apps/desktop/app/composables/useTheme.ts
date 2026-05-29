export type ThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'theme'
let systemListenerAttached = false

function resolveIsDark(mode: ThemeMode): boolean {
  if (mode === 'dark') return true
  if (mode === 'light') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyTheme(mode: ThemeMode) {
  const dark = resolveIsDark(mode)
  document.documentElement.classList.toggle('dark', dark)
  document.documentElement.style.colorScheme = dark ? 'dark' : 'light'
  return dark
}

export function useTheme() {
  const mode = useState<ThemeMode>('themeMode', () => 'system')
  const isDark = useState('themeIsDark', () => false)

  function setMode(next: ThemeMode) {
    mode.value = next
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, next)
      isDark.value = applyTheme(next)
    }
  }

  function toggle() {
    setMode(isDark.value ? 'light' : 'dark')
  }

  function init() {
    if (!import.meta.client) return

    const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
    const initial: ThemeMode = stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system'
    mode.value = initial
    isDark.value = applyTheme(initial)

    if (!systemListenerAttached) {
      systemListenerAttached = true
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (mode.value === 'system') {
          isDark.value = applyTheme('system')
        }
      })
    }
  }

  return { mode, isDark, setMode, toggle, init }
}
