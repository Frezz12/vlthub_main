import { listen } from '@tauri-apps/api/event'
import { formatError } from '~/utils/formatError'

export interface DownloadEntry {
  id: string
  fileName: string
  progress: number
  status: 'downloading' | 'complete' | 'error'
  errorMessage?: string
  onCancel?: () => void
}

const downloads = reactive<Record<string, DownloadEntry>>({})
let listenerInitialized = false

function isTauri(): boolean {
  return typeof window !== 'undefined' && (
    (window as any).__TAURI__ !== undefined ||
    (window as any).__TAURI_INTERNALS__ !== undefined
  )
}

function initGlobalListener() {
  if (listenerInitialized) return
  listenerInitialized = true
  if (!isTauri()) return

  listen<{ label: string; progress: number }>('download-progress', (e) => {
    const { label, progress } = e.payload
    const entry = downloads[label]
    if (!entry) return
    entry.progress = progress
    if (progress >= 100) {
      entry.status = 'complete'
    }
  })
}

export function useDownloadProgress() {
  initGlobalListener()

  function registerDownload(id: string, fileName: string, onCancel?: () => void) {
    downloads[id] = {
      id,
      fileName,
      progress: 0,
      status: 'downloading',
      onCancel,
    }
  }

  function markError(id: string, message: string) {
    const entry = downloads[id]
    if (!entry) return
    entry.status = 'error'
    entry.errorMessage = formatError(message)
  }

  function removeDownload(id: string) {
    delete downloads[id]
  }

  const allDownloads = computed<DownloadEntry[]>(() => Object.values(downloads))

  const hasActive = computed<boolean>(() =>
    Object.values(downloads).some((d) => d.status === 'downloading')
  )

  return {
    allDownloads,
    hasActive,
    registerDownload,
    markError,
    removeDownload,
  }
}
