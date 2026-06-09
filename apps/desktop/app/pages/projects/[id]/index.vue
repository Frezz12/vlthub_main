<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
import { invoke } from '@tauri-apps/api/core'
import { formatError } from '~/utils/formatError'

const route = useRoute()
const auth = useAuthStore()
const projects = useProjectsStore()
const versions = useVersionsStore()
const { getDawName } = useDawIcon()
const toast = inject('toast') as {
  show: (
    msg: string,
    type?: 'success' | 'error' | 'info',
    duration?: number,
    action?: { label: string; onClick: () => void },
    position?: 'top' | 'bottom',
    download?: { title: string; fileLabel: string; path: string },
  ) => void
}

const showVersionModal = ref(false)
const showShareModal = ref(false)
const savingQuick = ref(false)
const quickAbort = ref<AbortController | null>(null)
const quickCancelled = ref(false)
const quickVersionId = ref<string | null>(null)
const quickPrevCurrentId = ref<string | null>(null)
const accessDenied = ref(false)
const accessRequestSent = ref(false)
const requestingAccess = ref(false)
const downloadingVer = ref<string | null>(null)
const downloadProgress = ref(0)
const statusOpen = ref(false)
const statusDropdownRef = ref<HTMLElement | null>(null)

const isDesktopApp = computed(() => !!(window as any).__TAURI_INTERNALS__)

const isOwner = computed(() => projects.currentProject?.owner_id === auth.user?.id)

const editVersionId = ref<string | null>(null)
const editTitle = ref('')
const editDesc = ref('')
const showDeleteConfirm = ref(false)
const showDeleteProjectConfirm = ref(false)
const deleteTarget = ref<{ id: string; title: string } | null>(null)

const showDownloadModal = ref(false)
const downloadVersionId = ref<string | null>(null)

const showDescModal = ref(false)
const editProjectDesc = ref('')
const savingDesc = ref(false)
const showFullDesc = ref(false)

function openDescModal() {
  editProjectDesc.value = projects.currentProject?.lyrics || ''
  showDescModal.value = true
}

async function saveProjectDesc() {
  if (!projects.currentProject) return
  savingDesc.value = true
  try {
    await projects.updateProject(projects.currentProject.id, { lyrics: editProjectDesc.value || null } as any)
    toast.show('Текст песни обновлён', 'success')
    showDescModal.value = false
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    savingDesc.value = false
  }
}

const archiver = useProjectArchiver()

function isTokenExpired(token: string | null): boolean {
  if (!token) return true
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

function startEdit(v: { id: string; title: string | null; description: string | null }) {
  editVersionId.value = v.id
  editTitle.value = v.title || ''
  editDesc.value = v.description || ''
}

function cancelEdit() {
  editVersionId.value = null
  editTitle.value = ''
  editDesc.value = ''
}

async function saveEdit() {
  if (!editVersionId.value || !projects.currentProject) return
  try {
    await versions.updateVersion(projects.currentProject.id, editVersionId.value, {
      title: editTitle.value || undefined,
      description: editDesc.value || null,
    })
    toast.show('Версия обновлена', 'success')
    cancelEdit()
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

function handleStatusClickOutside(e: MouseEvent) {
  if (statusDropdownRef.value && !statusDropdownRef.value.contains(e.target as Node)) {
    statusOpen.value = false
  }
}

onMounted(async () => {
  try {
    await projects.fetchProject(route.params.id as string)
    await versions.fetchVersions(route.params.id as string)
  } catch (e: any) {
    if (e?.response?.status === 403) {
      accessDenied.value = true
    } else {
      toast.show(formatError(e), 'error')
    }
  }
  document.addEventListener('click', handleStatusClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleStatusClickOutside)
})

async function handleDelete() {
  showDeleteProjectConfirm.value = true
}

async function confirmDeleteProject() {
  showDeleteProjectConfirm.value = false
  try {
    await projects.deleteProject(route.params.id as string)
    toast.show('Проект удалён', 'success')
    navigateTo('/')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

function refreshPage() {
  window.location.reload()
}

const statusOptions = [
  { value: 'in_progress', label: 'В работе', cls: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300', dotCls: 'bg-blue-500' },
  { value: 'completed', label: 'Завершён', cls: 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-300', dotCls: 'bg-green-500' },
  { value: 'on_hold', label: 'Отложен', cls: 'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-700 dark:text-yellow-300', dotCls: 'bg-yellow-500' },
  { value: 'dropped', label: 'Закрыт', cls: 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-300', dotCls: 'bg-red-500' },
]

async function handleStatusChange(status: string) {
  if (!projects.currentProject) return
  await projects.updateProject(route.params.id as string, { status } as any)
  toast.show('Статус обновлён', 'success')
  statusOpen.value = false
}

async function handleSetCurrent(verId: string) {
  await versions.setCurrentVersion(route.params.id as string, verId)
  toast.show('Версия отмечена как текущая', 'success')
}

async function handleRequestAccess() {
  requestingAccess.value = true
  try {
    await projects.requestAccess(route.params.id as string)
    accessRequestSent.value = true
    toast.show('Запрос отправлен автору проекта', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    requestingAccess.value = false
  }
}

async function handlePickFolder() {
  savingQuick.value = true
  try {
    const files = await archiver.pickFolder(true, route.params.id as string)
    if (!files.length) { savingQuick.value = false; return }
    const tauriPath = archiver.getCachedTauriPath()
    const pickedName = archiver.getPickedFolderName()
    const path = tauriPath || pickedName || null
    if (path) {
      await projects.updateMyPath(route.params.id as string, path)
    }
    toast.show('Папка проекта выбрана', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    savingQuick.value = false
  }
}

function cancelQuickSave() {
  quickCancelled.value = true
  quickAbort.value?.abort()
  savingQuick.value = false
  downloadProgress.value = 0
  const verId = quickVersionId.value
  if (verId) {
    versions.items = versions.items.filter((v: any) => v.id !== verId)
    versions.total--
    const prevId = quickPrevCurrentId.value
    if (prevId) {
      versions.items.forEach((v: any) => (v.is_current = false))
      const prev = versions.items.find((v: any) => v.id === prevId)
      if (prev) prev.is_current = true
    }
    versions.deleteVersion(route.params.id as string, verId).catch(() => {})
  }
  quickVersionId.value = null
  quickPrevCurrentId.value = null
  quickAbort.value = null
}

async function handleQuickSave() {
  savingQuick.value = true
  quickCancelled.value = false
  quickAbort.value = new AbortController()
  const signal = quickAbort.value.signal
  let version: any = null

  try {
    const savedPath = projects.currentProject?.my_project_path || projects.currentProject?.project_path

    // Desktop app with a saved path → skip picker, archive directly
    if (isDesktopApp.value && savedPath) {
      quickPrevCurrentId.value = versions.current?.id || null
      version = await versions.createVersion(route.params.id as string, {
        title: `Версия ${(versions.items.length || 0) + 1}`,
        description: null,
      })
      quickVersionId.value = version.id
      const folderName = savedPath.replace(/[/\\]$/, '').split(/[/\\]/).pop() || undefined
      const up = useUploadProgress()
      up.registerUpload(version.id, route.params.id as string, folderName || 'project', cancelQuickSave)
      await archiver.uploadTauriArchiveFromPath(savedPath, route.params.id as string, version.id, auth.accessToken!, folderName)
      if (quickCancelled.value) return
      await versions.fetchVersions(route.params.id as string)
      toast.show('Версия сохранена', 'success')
      return
    }

    // Fallback: open picker (browser or no saved path)
    const files = await archiver.pickFolder(false, route.params.id as string, savedPath || undefined)
    if (!files.length) { savingQuick.value = false; return }
    const tauriPath = archiver.getCachedTauriPath()
    const pickedName = archiver.getPickedFolderName()
    const newPath = tauriPath || pickedName || null
    if (newPath && newPath !== savedPath) {
      await projects.updateMyPath(route.params.id as string, newPath)
    }
    if (quickCancelled.value) return

    quickPrevCurrentId.value = versions.current?.id || null
    version = await versions.createVersion(route.params.id as string, {
      title: `Версия ${(versions.items.length || 0) + 1}`,
      description: null,
    })
    quickVersionId.value = version.id
    const folderName = pickedName || savedPath
      ?.replace(/[/\\]$/, '').split(/[/\\]/).pop() || undefined
    if (tauriPath) {
      const up = useUploadProgress()
      up.registerUpload(version.id, route.params.id as string, folderName || 'project', cancelQuickSave)
      await archiver.uploadTauriArchiveFromPath(tauriPath, route.params.id as string, version.id, auth.accessToken!, folderName)
    } else {
      const { blob } = await archiver.archiveProject(files, (pct) => {
        if (quickCancelled.value) return
        downloadProgress.value = pct
      }, signal)
      if (quickCancelled.value) return
      await archiver.uploadArchive(blob, route.params.id as string, version.id, auth.accessToken!, (pct) => {
        if (quickCancelled.value) return
        downloadProgress.value = pct
      }, folderName, signal)
    }
    if (quickCancelled.value) return
    await versions.fetchVersions(route.params.id as string)
    toast.show('Версия сохранена', 'success')
  } catch (e: any) {
    if (e.name === 'AbortError' || quickCancelled.value) return
    toast.show(formatError(e), 'error', 5000)
  } finally {
    savingQuick.value = false
    downloadProgress.value = 0
    quickAbort.value = null
    quickVersionId.value = null
  }
}

async function handleDeleteVersion(versionId: string, title: string | null) {
  deleteTarget.value = {
    id: versionId,
    title: title || `v${versions.items.find(v => v.id === versionId)?.version_number || ''}`,
  }
  showDeleteConfirm.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value || !projects.currentProject) return
  const { id } = deleteTarget.value
  showDeleteConfirm.value = false
  deleteTarget.value = null
  try {
    await versions.deleteVersion(projects.currentProject.id, id)
    toast.show('Версия удалена', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

async function handleDownloadZip(versionId: string, savePath: string | null = null) {
  downloadingVer.value = versionId
  downloadProgress.value = 0
  const dlStore = useDownloadProgress()
  try {
    if (isTokenExpired(auth.accessToken)) {
      const refreshed = await auth.refresh()
      if (!refreshed) {
        toast.show('Сессия истекла, войдите снова', 'error')
        return
      }
    }

    const res = await fetch(__API_BASE_URL__ + `/api/v1/projects/${route.params.id as string}/versions/${versionId}/download`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      method: 'POST',
    })
    if (!res.ok) throw new Error('Download failed')
    const { download_url, file_name: serverFileName } = await res.json() as {
      download_url: string
      file_name?: string
    }
    const defaultName = serverFileName || `version_${versionId}.zip`
    const fullPath = defaultName.replace(/^.*[/\\]/, '')

    const apiBaseUrl = (typeof __API_BASE_URL__ !== 'undefined' && __API_BASE_URL__) ? __API_BASE_URL__ : 'http://localhost:8000'
    const absoluteUrl = download_url.startsWith('/') ? `${apiBaseUrl}${download_url}` : download_url

    if ('__TAURI_INTERNALS__' in window) {
      const dest = savePath || await invoke<string | null>('save_file_dialog', { defaultName: fullPath })
      if (!dest) {
        toast.show('Скачивание отменено', 'info')
        return
      }

      dlStore.registerDownload(versionId, fullPath, () => {
        invoke('cancel_download', { label: versionId }).catch(() => {})
        dlStore.removeDownload(versionId)
      })

      const unlisten = await import('@tauri-apps/api/event').then(m =>
        m.listen<{ label: string; progress: number }>('download-progress', (e) => {
          if (e.payload.label === versionId) {
            downloadProgress.value = e.payload.progress
          }
        })
      )

      await invoke('download_file', {
        url: absoluteUrl,
        dest,
        label: versionId,
      })

      unlisten()

      if (!savePath) {
        toast.show('', 'success', 9000, {
          label: 'Папка',
          onClick: () => {
            invoke('open_in_file_manager', { path: dest }).catch(() => {
              toast.show('Не удалось открыть папку', 'error')
            })
          },
        }, 'bottom', {
          title: 'Файл сохранён',
          fileLabel: fullPath,
          path: dest,
        })
      }
    } else {
      const a = document.createElement('a')
      a.href = absoluteUrl
      a.download = fullPath
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      toast.show('Скачивание начато', 'success')
    }
  } catch (e: any) {
    if (e?.toString?.()?.includes?.('cancelled')) {
      dlStore.removeDownload(versionId)
      toast.show('Скачивание отменено', 'info')
    } else {
      console.error('download error', e)
      dlStore.markError(versionId, formatError(e))
      toast.show(formatError(e), 'error')
    }
  } finally {
    downloadingVer.value = null
    downloadProgress.value = 0
  }
}

async function handleUpdateProjectFiles() {
  const versionId = downloadVersionId.value
  if (!versionId) return
  const savedPath = projects.currentProject?.my_project_path || projects.currentProject?.project_path
  if (!savedPath) {
    toast.show('Не указан путь к проекту', 'error')
    return
  }

  downloadingVer.value = versionId
  downloadProgress.value = 0
  try {
    const tempDir = await invoke<string>('get_temp_dir')
    const zipName = `vlt_update_${versionId}.zip`
    const zipPath = `${tempDir}/${zipName}`

    await handleDownloadZip(versionId, zipPath)

    await invoke('extract_archive', { path: zipPath, dest: savedPath })
    await invoke('clean_temp_files', { paths: [zipPath] })

    showDownloadModal.value = false
    toast.show('Файлы проекта обновлены', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    downloadingVer.value = null
    downloadProgress.value = 0
    downloadVersionId.value = null
  }
}

async function handleDownloadVersion(versionId: string) {
  if ('__TAURI_INTERNALS__' in window) {
    downloadVersionId.value = versionId
    showDownloadModal.value = true
  } else {
    await handleDownloadZip(versionId)
  }
}

async function downloadCover() {
  if (!projects.currentProject?.cover_url) return
  const url = resolveApiUrl(projects.currentProject.cover_url)
  if (!url) return
  const defaultName = (projects.currentProject.title?.replace(/[/\\?%*:|"<>]/g, '_') || 'cover') + '.jpg'

  if ('__TAURI_INTERNALS__' in window) {
    const dest = await invoke<string | null>('save_file_dialog', { defaultName })
    if (!dest) return
    await invoke('download_file', {
      url,
      dest,
      label: 'cover-' + projects.currentProject.id,
    })
    toast.show('Обложка сохранена', 'success')
  } else {
    const a = document.createElement('a')
    a.href = url
    a.download = defaultName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 MB'
  const gb = bytes / 1_073_741_824
  if (gb >= 1) return gb.toFixed(2) + ' GB'
  const mb = bytes / 1_048_576
  return mb.toFixed(1) + ' MB'
}
</script>

<template>
  <div class="page-shell">
    <div v-if="projects.loading" class="animate-pulse space-y-4">
      <div class="h-8 bg-btn-secondary rounded w-1/3" />
      <div class="h-4 bg-btn-secondary rounded w-1/2" />
    </div>

    <!-- Access denied / Request access -->
    <div v-else-if="accessDenied" class="max-w-md mx-auto text-center py-16">
      <svg class="w-16 h-16 mx-auto text-secondary/40 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m0 0v2m0-2h2m-2 0H10m9.364-7.364A9 9 0 1112 3a9 9 0 017.364 4.636z" />
      </svg>
      <h2 class="text-xl font-semibold mb-2">Нет доступа к проекту</h2>
      <p class="text-sm text-secondary mb-6">Отправьте запрос автору, чтобы получить доступ</p>
      <UiButton
        v-if="!accessRequestSent"
        :loading="requestingAccess"
        @click="handleRequestAccess"
      >
        Запросить доступ
      </UiButton>
      <div v-else class="flex flex-col items-center gap-2">
        <span class="inline-flex items-center gap-1.5 text-sm text-success">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Запрос отправлен
        </span>
        <p class="text-xs text-secondary">Дождитесь ответа автора проекта</p>
      </div>
    </div>

    <template v-else-if="projects.currentProject">
      <!-- Header -->
      <div class="flex items-start justify-between mb-8">
        <div class="flex items-start gap-4">
          <div
            class="w-24 h-24 rounded-xl overflow-hidden shrink-0 bg-gradient-to-br from-[#F5F5F7] to-primary/10 group relative"
          >
            <img
              v-if="projects.currentProject.cover_url"
              :src="resolveApiUrl(projects.currentProject.cover_url)"
              :alt="projects.currentProject.title"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <svg class="w-8 h-8 text-primary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <button
              v-if="projects.currentProject.cover_url"
              class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Скачать обложку"
              @click="downloadCover"
            >
              <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </button>
          </div>
          <div>
            <div class="flex items-center gap-3 mb-2">
              <NuxtLink to="/" class="text-secondary hover:text-primary transition-colors">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </NuxtLink>
              <h1 class="page-title !text-2xl sm:!text-3xl">{{ projects.currentProject.title }}</h1>
            </div>

          <div class="flex flex-wrap items-center gap-3 text-sm">
            <span v-if="projects.currentProject.owner" class="flex items-center gap-1.5 text-secondary">
              <span class="w-5 h-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-medium">
                {{ projects.currentProject.owner.nickname?.[0]?.toUpperCase() || '?' }}
              </span>
              <span class="flex items-center gap-1">{{ projects.currentProject.owner.nickname }}<UserBadgeIcon :badge="(projects.currentProject.owner as any).active_badge" size="sm" /></span>
            </span>
            <span class="px-2 py-0.5 rounded bg-border/50 text-secondary">
              {{ getDawName(projects.currentProject.daw_type) }}
            </span>
            <span v-if="projects.currentProject.bpm" class="text-secondary">{{ projects.currentProject.bpm }} BPM</span>
            <span v-if="projects.currentProject.key" class="text-secondary">{{ projects.currentProject.key }}</span>
            <span v-if="projects.currentProject.artists" class="px-2 py-0.5 rounded bg-btn-secondary/60 text-secondary">
              feat. {{ projects.currentProject.artists }}
            </span>
            <span v-if="projects.currentProject.beatmaker" class="px-2 py-0.5 rounded bg-btn-secondary/60 text-secondary">
              {{ projects.currentProject.beatmaker }}
            </span>
            <span v-if="projects.currentProject.total_size" class="px-2 py-0.5 rounded bg-btn-secondary/60 text-secondary">
              {{ formatSize(projects.currentProject.total_size) }}
            </span>
            <span v-if="projects.currentProject.is_archived" class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs text-blue-400 bg-blue-500/10 shadow-[0_0_8px_rgba(59,130,246,0.3)]">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
              </svg>
              Архив
            </span>
            <span
              v-if="projects.currentProject.is_public"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs text-emerald-400 bg-emerald-500/10"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
              Публичный
            </span>
            <span v-else class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs text-zinc-400 bg-zinc-500/10">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
              Приватный
            </span>
            <div ref="statusDropdownRef" class="relative">
              <button
                type="button"
                class="flex items-center gap-1.5 px-2 py-0.5 rounded text-sm cursor-pointer border-none outline-none transition-colors"
                :class="statusOptions.find(s => s.value === projects.currentProject.status)?.cls || 'bg-btn-secondary/60'"
                @click="statusOpen = !statusOpen"
              >
                {{ statusOptions.find(s => s.value === projects.currentProject.status)?.label }}
                <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-180': statusOpen }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <Transition name="dropdown">
                <div
                  v-if="statusOpen"
                  class="absolute left-0 top-full mt-1 min-w-[140px] rounded-lg bg-surface-elevated border border-border shadow-lg z-20 overflow-hidden"
                >
                  <button
                    v-for="opt in statusOptions"
                    :key="opt.value"
                    type="button"
                    class="w-full flex items-center gap-2 px-3.5 py-2 text-sm text-left transition-colors whitespace-nowrap"
                    :class="projects.currentProject.status === opt.value ? 'bg-primary/5 text-primary font-medium' : 'text-foreground hover:bg-surface'"
                    @click="handleStatusChange(opt.value)"
                  >
                    <span class="w-2 h-2 rounded-full shrink-0" :class="opt.dotCls" />
                    {{ opt.label }}
                  </button>
                </div>
              </Transition>
            </div>
        </div>
      </div>
      </div>

        <div class="flex items-center gap-1.5">
          <UiButton variant="secondary" size="sm" class="!rounded-xl" @click="showShareModal = true">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            Поделиться
          </UiButton>
          <NuxtLink :to="`/projects/${projects.currentProject.id}/activity`">
            <UiButton variant="secondary" size="sm" class="!rounded-xl">Журнал</UiButton>
          </NuxtLink>
          <NuxtLink :to="`/projects/${projects.currentProject.id}/info`">
            <UiButton variant="secondary" size="sm" class="!rounded-xl">Настройки</UiButton>
          </NuxtLink>
          <div class="w-px h-5 bg-border/50 mx-0.5" />
          <UiButton v-if="isOwner" variant="danger" size="sm" class="!rounded-xl" @click="handleDelete">Удалить</UiButton>
        </div>
      </div>

      <!-- Текст песни -->
      <div class="mb-8 max-w-2xl">
        <div class="flex items-center gap-2 mb-2">
          <h3 class="text-sm font-medium text-foreground">Текст песни</h3>
          <button
            class="p-1 rounded-md text-secondary/50 hover:text-primary hover:bg-border/50 transition-colors shrink-0"
            title="Редактировать текст"
            @click="openDescModal"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>
        <template v-if="projects.currentProject.lyrics">
          <div
            class="text-sm text-secondary whitespace-pre-line"
            :class="!showFullDesc && 'line-clamp-4'"
            v-html="projects.currentProject.lyrics"
          />
          <button
            v-if="showFullDesc"
            class="text-xs text-primary hover:underline mt-1"
            @click="showFullDesc = false"
          >
            Скрыть
          </button>
          <button
            v-else
            class="text-xs text-primary hover:underline mt-1"
            @click="showFullDesc = true"
          >
            Показать всё
          </button>
        </template>
        <p v-else class="text-sm text-secondary/50 italic">Текст песни отсутствует</p>
      </div>

      <!-- Tags -->
      <div v-if="projects.currentProject.tags?.length" class="flex flex-wrap gap-1 mb-8">
        <UiBadge v-for="tag in projects.currentProject.tags" :key="tag">{{ tag }}</UiBadge>
      </div>

      <!-- Quick Save -->
      <div class="rounded-2xl bg-surface-elevated ring-1 ring-border/40 shadow-[0_1px_4px_rgba(0,0,0,0.06)] px-5 py-4 mb-8">
        <div class="flex items-center justify-between">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 mb-0.5">
              <svg class="w-4 h-4 text-secondary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <h3 class="text-[15px] font-medium text-foreground">Папка проекта</h3>
            </div>
            <p class="text-[13px] text-secondary/50 mt-1 truncate flex items-center gap-1.5">
              {{ projects.currentProject.my_project_path || projects.currentProject.project_path || 'Не указана' }}
              <span v-if="!isDesktopApp" class="text-[10px] px-1.5 py-0.5 rounded bg-btn-secondary/60 text-secondary/40">только в приложении</span>
            </p>
          </div>
            <div class="flex items-center gap-2 shrink-0 ml-4">
              <UiButton
                v-if="!projects.currentProject.my_project_path && !projects.currentProject.project_path"
                size="sm"
                @click="handlePickFolder"
                class="!rounded-xl"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                Выбрать папку
              </UiButton>
              <template v-else>
                <UiButton
                  size="sm"
                  variant="ghost"
                  @click="handlePickFolder"
                  class="!rounded-xl"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  Сменить
                </UiButton>
              </template>
            </div>
        </div>
        <div v-if="quickVersionId && savingQuick" class="mt-4">
          <div class="flex items-center justify-between text-[12px] text-secondary/50 mb-1.5">
            <span>Сохранение версии...</span>
            <span>{{ downloadProgress > 0 ? downloadProgress + '%' : '' }}</span>
          </div>
          <div class="h-1 rounded-full bg-btn-secondary overflow-hidden">
            <div class="h-full rounded-full bg-primary transition-all duration-300" :class="downloadProgress > 0 ? '' : 'animate-pulse'" :style="{ width: downloadProgress > 0 ? downloadProgress + '%' : '30%' }"></div>
          </div>
          <button
            type="button"
            class="mt-1 text-xs text-danger/70 hover:text-danger transition-colors"
            @click="cancelQuickSave"
          >
            Отмена
          </button>
        </div>
      </div>

<!-- Version Timeline -->
<div class="mb-10">
  <div class="flex items-center justify-between mb-7">
    <div class="flex items-baseline gap-3">
      <h2 class="text-[17px] font-semibold text-foreground tracking-tight">История версий</h2>
      <span class="text-[13px] text-secondary/40 font-medium tabular-nums">{{ versions.items.length }}</span>
    </div>
    <div class="flex items-center gap-2">
      <UiButton size="sm" variant="secondary" class="!rounded-xl" @click="showVersionModal = true">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        Новая версия
      </UiButton>
      <UiButton size="sm" class="!rounded-xl" @click="handleQuickSave">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
      </svg>
      Быстрое сохранение
    </UiButton>
  </div>
</div>

<!-- Timeline -->
  <div v-if="versions.items.length">
    <div class="timeline-container">
      <!-- Timeline Line -->
      <div class="timeline-line"></div>
      
      <TransitionGroup name="timeline" tag="div" class="relative space-y-3">
        <div
          v-for="(version, idx) in versions.sortedVersions"
          :key="version.id"
          class="relative"
          :style="{ opacity: version.is_current ? 1 : Math.max(0.45, 1 - (idx * 0.1)) }"
        >
          <!-- Timeline Dot -->
          <div class="timeline-dot" :class="{ 'is-current': version.is_current }">
            <div class="timeline-dot-inner"></div>
          </div>
          
          <!-- Card -->
          <div
            class="relative overflow-hidden transition-all duration-300 ease-out version-card-modern"
            :class="[
              version.is_current ? 'is-current' : '',
              !version.is_current && 'hover:shadow-lg hover:-translate-y-0.5'
            ]"
          >
          <div class="px-4 py-4">
            <div class="flex items-start justify-between gap-4">
              <div class="flex items-center gap-3 min-w-0 flex-1">
                <!-- Version badge -->
                <div class="version-badge">
                  {{ version.version_number }}
                </div>

                <div class="min-w-0 flex-1">
                  <!-- Edit mode -->
                  <template v-if="editVersionId === version.id">
                    <input
                      v-model="editTitle"
                      class="w-full rounded-lg border border-border bg-surface px-3 py-1.5 text-sm font-medium mb-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
                      placeholder="Название версии"
                    />
                    <textarea
                      v-model="editDesc"
                      class="w-full rounded-lg border border-border bg-surface px-3 py-1.5 text-xs resize-none focus:outline-none focus:ring-2 focus:ring-primary/30"
                      rows="2"
                      placeholder="Описание"
                    />
                    <div class="flex items-center gap-2 mt-2">
                      <UiButton size="xs" @click="saveEdit">Сохранить</UiButton>
                      <UiButton size="xs" variant="ghost" @click="cancelEdit">Отмена</UiButton>
                    </div>
                  </template>
                  <!-- View mode -->
                  <template v-else>
                    <div class="flex items-center gap-2 flex-wrap">
                      <NuxtLink
                        :to="`/projects/${projects.currentProject?.id}/versions/${version.id}`"
                        class="text-sm font-semibold text-foreground hover:text-primary transition-colors no-underline leading-tight"
                      >
                        {{ version.title || `Версия ${version.version_number}` }}
                      </NuxtLink>
                      <span
                        v-if="version.is_current && editVersionId !== version.id"
                        class="current-badge"
                      >Текущая</span>
                    </div>
                    <p v-if="version.description" class="text-sm text-secondary mt-1 leading-relaxed line-clamp-1">
                      {{ version.description }}
                    </p>
                  </template>
                </div>
              </div>

              <!-- Actions -->
              <div v-if="editVersionId !== version.id" class="flex items-center gap-1 shrink-0">
                <button
                  class="version-action-btn"
                  title="Редактировать"
                  @click="startEdit(version)"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  v-if="!version.is_current"
                  class="version-action-btn"
                  title="Сделать текущей"
                  @click="handleSetCurrent(version.id)"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
                <button
                  class="version-action-btn"
                  title="Скачать"
                  @click="handleDownloadVersion(version.id)"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </button>
                <button
                  class="version-action-btn danger"
                  title="Удалить"
                  @click="handleDeleteVersion(version.id, version.title)"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Meta row -->
            <div class="flex items-center gap-4 mt-3 pt-3 border-t border-border/30">
              <span class="flex items-center gap-1.5 text-xs text-secondary">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {{ new Date(version.created_at).toLocaleDateString() }}
              </span>
              <span v-if="version.file_size" class="flex items-center gap-1.5 text-xs text-secondary">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {{ (version.file_size / 1024 / 1024).toFixed(1) }} MB
              </span>
            </div>
          </div>
        </div>
      </div>
    </TransitionGroup>
    </div>
  </div>

  <div v-else class="py-16 text-center">
    <div class="w-14 h-14 mx-auto rounded-2xl bg-btn-secondary/50 flex items-center justify-center mb-4">
      <svg class="w-6 h-6 text-secondary/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
    <p class="text-[15px] font-medium text-secondary/60">Пока нет версий</p>
    <p class="text-[13px] text-secondary/40 mt-1">Сохраните первую версию проекта</p>
  </div>
</div>
    </template>

    <!-- Error fallback -->
    <div v-else class="text-center py-16">
      <svg class="w-16 h-16 mx-auto text-secondary/40 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
      <h2 class="text-xl font-semibold mb-2">Не удалось загрузить проект</h2>
      <p class="text-sm text-secondary mb-6">Попробуйте обновить страницу</p>
      <UiButton @click="refreshPage">Обновить</UiButton>
    </div>

    <!-- Modals -->
    <UiModal v-model="showVersionModal" title="Новая версия">
      <VersionCreateModal
        :project-id="route.params.id as string"
        @created="showVersionModal = false"
      />
    </UiModal>

    <UiModal v-model="showShareModal" title="Поделиться проектом">
      <ShareModal :project-id="route.params.id as string" />
    </UiModal>

    <!-- Delete Confirm Modal -->
    <UiModal v-model="showDeleteProjectConfirm" title="Удалить проект">
      <div class="flex flex-col gap-4">
        <p class="text-sm">Удалить проект «<strong>{{ projects.currentProject?.title }}</strong>»?</p>
        <p class="text-xs text-secondary">Все версии и файлы проекта будут удалены безвозвратно.</p>
        <div class="flex justify-end gap-2">
          <UiButton variant="secondary" @click="showDeleteProjectConfirm = false">Отмена</UiButton>
          <UiButton variant="danger" @click="confirmDeleteProject">Удалить</UiButton>
        </div>
      </div>
    </UiModal>

    <UiModal v-model="showDeleteConfirm" title="Удалить версию">
      <div class="flex flex-col gap-4">
        <p class="text-sm">Удалить версию «<strong>{{ deleteTarget?.title }}</strong>»?</p>
        <p class="text-xs text-secondary">Файлы версии будут удалены безвозвратно.</p>
        <div class="flex justify-end gap-2">
          <UiButton variant="secondary" @click="showDeleteConfirm = false; deleteTarget = null">Отмена</UiButton>
          <UiButton variant="danger" @click="confirmDelete">Удалить</UiButton>
        </div>
      </div>
    </UiModal>

    <UiModal v-model="showDownloadModal" title="Скачать версию" max-width="420px">
      <div class="flex flex-col gap-3">
        <button
          class="flex items-center gap-3 p-4 rounded-xl bg-surface-elevated border border-input-border hover:border-primary/40 hover:bg-hover transition-all text-left cursor-pointer"
          @click="showDownloadModal = false; handleDownloadZip(downloadVersionId!)"
        >
          <div class="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <p class="text-sm font-medium text-foreground">Скачать ZIP</p>
            <p class="text-xs text-secondary mt-0.5">Сохранить архив версии на компьютер</p>
          </div>
        </button>
        <button
          class="flex items-center gap-3 p-4 rounded-xl bg-surface-elevated border border-input-border hover:border-primary/40 hover:bg-hover transition-all text-left cursor-pointer"
          @click="handleUpdateProjectFiles"
        >
          <div class="w-10 h-10 rounded-lg bg-green-500/10 text-green-500 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
          <div>
            <p class="text-sm font-medium text-foreground">Обновить файлы проекта</p>
            <p class="text-xs text-secondary mt-0.5">Распаковать версию в папку проекта</p>
          </div>
        </button>
      </div>
    </UiModal>

    <UiModal v-model="showDescModal" title="Текст песни" max-width="580px">
      <div class="flex flex-col gap-4">
        <UiRichEditor v-model="editProjectDesc" placeholder="Текст песни..." :rows="12" />
        <div class="flex justify-end gap-2">
          <UiButton variant="secondary" @click="showDescModal = false">Отмена</UiButton>
          <UiButton :loading="savingDesc" @click="saveProjectDesc">Сохранить</UiButton>
        </div>
      </div>
    </UiModal>
  </div>
</template>

<style scoped>
.timeline-enter-active {
  transition: all 0.5s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.timeline-leave-active {
  transition: all 0.3s ease;
}

.timeline-enter-from {
  opacity: 0;
  transform: scale(0.96) translateY(16px);
}

.timeline-leave-to {
  opacity: 0;
  transform: scale(0.96) translateX(-20px);
}

.timeline-move {
  transition: transform 0.5s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.version-card-apple {
  transition: all 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.version-card-apple:hover {
  transform: translateY(-1px);
}
</style>
