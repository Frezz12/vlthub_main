import { invoke } from '@tauri-apps/api/core'

export function useExternalLink() {
  const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI_INTERNALS__

  function openExternal(url: string) {
    if (isTauri) {
      invoke('open_in_browser', { url }).catch(() => {
        window.open(url, '_blank', 'noopener,noreferrer')
      })
    } else {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  return { openExternal, isTauri }
}
