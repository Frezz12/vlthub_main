import { listen } from '@tauri-apps/api/event'
import { formatError } from '~/utils/formatError'

export interface UploadEntry {
  id: string
  versionId: string
  projectId: string
  folderName: string
  progress: number
  phase: string
  status: 'archiving' | 'uploading' | 'complete' | 'error'
  errorMessage?: string
  onCancel?: () => void
}

const uploads = reactive<Record<string, UploadEntry>>({})
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

  listen<{ label: string; progress: number; phase: string; error?: string }>('upload-progress', (e) => {
    const { label, progress, phase, error } = e.payload
    const entry = uploads[label]
    if (!entry) return

    entry.progress = progress
    entry.phase = phase

    if (phase === 'complete') {
      entry.status = 'complete'
    } else if (phase === 'error') {
      entry.status = 'error'
      entry.errorMessage = formatError(error)
    } else if (phase === 'archive') {
      entry.status = 'archiving'
    } else if (phase === 'upload') {
      entry.status = 'uploading'
    }
  })

  listen<{ label: string; error: string }>('upload-error', (e) => {
    const entry = uploads[e.payload.label]
    if (!entry) return
    entry.status = 'error'
    entry.errorMessage = formatError(e.payload.error)
  })
}

export function useUploadProgress() {
  initGlobalListener()

  function registerUpload(versionId: string, projectId: string, folderName: string, onCancel?: () => void) {
    uploads[versionId] = {
      id: versionId,
      versionId,
      projectId,
      folderName,
      progress: 0,
      phase: 'archive',
      status: 'archiving',
      onCancel,
    }
  }

  function removeUpload(id: string) {
    delete uploads[id]
  }

  const allUploads = computed<UploadEntry[]>(() => Object.values(uploads))

  const hasActive = computed<boolean>(() =>
    Object.values(uploads).some((u) => u.status !== 'complete' && u.status !== 'error')
  )

  return {
    allUploads,
    hasActive,
    registerUpload,
    removeUpload,
  }
}
