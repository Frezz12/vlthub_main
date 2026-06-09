<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
import { invoke } from '@tauri-apps/api/core'
import { formatError } from '~/utils/formatError'

const route = useRoute()
const versions = useVersionsStore()
const auth = useAuthStore()
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

const commentText = ref('')
const loadingComment = ref(false)
const previewFile = ref<File | null>(null)
const uploadingPreview = ref(false)
const deletingPreviewId = ref<string | null>(null)

const projectId = computed(() => route.params.id as string)
const verId = computed(() => route.params.verId as string)

const downloadingFileId = ref<string | null>(null)
const fileDownloadProgress = ref(0)

const showDownloadModal = ref(false)
const downloadVersionId = ref<string | null>(null)

const isDesktopApp = computed(() => !!(window as any).__TAURI_INTERNALS__)
const apiBase = typeof __API_BASE_URL__ !== 'undefined' && __API_BASE_URL__ ? __API_BASE_URL__ : 'http://localhost:8000'

const projects = useProjectsStore()

function onPreviewFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    previewFile.value = input.files[0]
  }
}

async function handlePreviewUpload() {
  if (!previewFile.value) return
  uploadingPreview.value = true
  try {
    const formData = new FormData()
    formData.append('file', previewFile.value)
    formData.append('title', previewFile.value.name.replace(/\.[^/.]+$/, ''))
    const res = await fetch(
      `${apiBase}/api/v1/projects/${projectId.value}/versions/${verId.value}/previews`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: formData,
      },
    )
    if (!res.ok) throw new Error('Preview upload failed')
    toast.show('Превью загружено', 'success')
    previewFile.value = null
    await versions.fetchVersion(projectId.value, verId.value)
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    uploadingPreview.value = false
  }
}

async function handleDeletePreview(previewId: string) {
  deletingPreviewId.value = previewId
  try {
    await useApiFetch(
      `/api/v1/projects/${projectId.value}/versions/${verId.value}/previews/${previewId}`,
      { method: 'DELETE', headers: { Authorization: `Bearer ${auth.accessToken}` } },
    )
    await versions.fetchVersion(projectId.value, verId.value)
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    deletingPreviewId.value = null
  }
}

async function handleDownloadZip(savePath: string | null = null) {
  downloadingFileId.value = verId.value
  fileDownloadProgress.value = 0
  const dlStore = useDownloadProgress()

  try {
    const dlRes = await useApiFetch<{ download_url: string; file_name: string }>(
      `/api/v1/projects/${projectId.value}/versions/${verId.value}/download`,
      { method: 'POST', headers: { Authorization: `Bearer ${auth.accessToken}` } },
    )
    const dlUrl = resolveApiUrl(dlRes.download_url)
    const fullPath = dlRes.file_name.replace(/^.*[/\\]/, '')

    if ('__TAURI_INTERNALS__' in window) {
      const dest = savePath || await invoke<string | null>('save_file_dialog', { defaultName: fullPath })
      if (!dest) {
        toast.show('Скачивание отменено', 'info')
        return
      }

      dlStore.registerDownload(verId.value, fullPath, () => {
        invoke('cancel_download', { label: verId.value }).catch(() => {})
        dlStore.removeDownload(verId.value)
      })

      const unlisten = await import('@tauri-apps/api/event').then(m =>
        m.listen<{ label: string; progress: number }>('download-progress', (e) => {
          if (e.payload.label === verId.value) {
            fileDownloadProgress.value = e.payload.progress
          }
        })
      )

      await invoke('download_file', { url: dlUrl, dest, label: verId.value })

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
      const res = await fetch(dlUrl, {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fullPath
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.show('Скачивание начато', 'success')
    }
  } catch (e: any) {
    if (e?.toString?.()?.includes?.('cancelled')) {
      dlStore.removeDownload(verId.value)
      toast.show('Скачивание отменено', 'info')
    } else {
      console.error('download error', e)
      dlStore.markError(verId.value, formatError(e))
      toast.show(formatError(e), 'error')
    }
  } finally {
    downloadingFileId.value = null
    fileDownloadProgress.value = 0
  }
}

async function handleUpdateProjectFiles() {
  const savedPath = projects.currentProject?.my_project_path || projects.currentProject?.project_path
  if (!savedPath) {
    toast.show('Не указан путь к проекту', 'error')
    return
  }

  downloadingFileId.value = verId.value
  fileDownloadProgress.value = 0
  try {
    const tempDir = await invoke<string>('get_temp_dir')
    const zipName = `vlt_update_${verId.value}.zip`
    const zipPath = `${tempDir}/${zipName}`

    await handleDownloadZip(zipPath)

    await invoke('extract_archive', { path: zipPath, dest: savedPath })
    await invoke('clean_temp_files', { paths: [zipPath] })

    showDownloadModal.value = false
    toast.show('Файлы проекта обновлены', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    downloadingFileId.value = null
    fileDownloadProgress.value = 0
    downloadVersionId.value = null
  }
}

async function handleDownload(file: any) {
  if (isDesktopApp.value) {
    downloadVersionId.value = verId.value
    showDownloadModal.value = true
  } else {
    await handleDownloadZip()
  }
}


const tasks = ref<VersionTaskOut[]>([])
const taskText = ref('')
const addingTask = ref(false)

interface VersionTaskOut {
  id: string
  version_id: string
  text: string
  is_done: boolean
  position: number
  created_at: string
}

async function fetchTasks() {
  try {
    const res = await useApiFetch<VersionTaskOut[]>(
      `/api/v1/projects/${projectId.value}/versions/${verId.value}/tasks`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } },
    )
    tasks.value = res
  } catch { tasks.value = [] }
}

async function addTask() {
  if (!taskText.value.trim()) return
  addingTask.value = true
  try {
    const task = await useApiFetch<VersionTaskOut>(
      `/api/v1/projects/${projectId.value}/versions/${verId.value}/tasks`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}`, 'Content-Type': 'application/json' },
        body: { text: taskText.value },
      },
    )
    tasks.value.push(task)
    taskText.value = ''
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    addingTask.value = false
  }
}

async function toggleTask(task: VersionTaskOut) {
  const updated = await useApiFetch<VersionTaskOut>(
    `/api/v1/projects/${projectId.value}/versions/${verId.value}/tasks/${task.id}`,
    {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${auth.accessToken}`, 'Content-Type': 'application/json' },
      body: { is_done: !task.is_done },
    },
  )
  Object.assign(task, updated)
}

async function deleteTask(taskId: string) {
  await useApiFetch(
    `/api/v1/projects/${projectId.value}/versions/${verId.value}/tasks/${taskId}`,
    {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    },
  )
  tasks.value = tasks.value.filter(t => t.id !== taskId)
}

onMounted(async () => {
  await versions.fetchVersion(projectId.value, verId.value)
  await versions.fetchComments(projectId.value, verId.value)
  await fetchTasks()
  await versions.fetchFiles(projectId.value, verId.value)
})

async function handleAddComment() {
  if (!commentText.value.trim()) return
  loadingComment.value = true
  try {
    await versions.addComment(projectId.value, verId.value, { text: commentText.value })
    commentText.value = ''
    toast.show('Комментарий добавлен', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    loadingComment.value = false
  }
}

async function handleDeleteComment(commentId: string) {
  if (confirm('Удалить комментарий?')) {
    await versions.deleteComment(projectId.value, verId.value, commentId)
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
    <div v-if="versions.loading" class="animate-pulse space-y-4">
      <div class="h-8 bg-btn-secondary rounded w-1/3" />
      <div class="h-4 bg-btn-secondary rounded w-1/2" />
    </div>

    <template v-else-if="versions.currentVersion">
      <div class="flex items-center gap-3 mb-6">
        <NuxtLink
          :to="`/projects/${projectId}`"
          class="text-secondary hover:text-primary transition-colors"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </NuxtLink>
        <div>
          <h1 class="text-2xl font-semibold">
            v{{ versions.currentVersion.version_number }} — {{ versions.currentVersion.title }}
          </h1>
          <p class="text-sm text-secondary">
            {{ new Date(versions.currentVersion.created_at).toLocaleDateString() }}
            <span v-if="versions.currentVersion.file_size">
              · {{ (versions.currentVersion.file_size / 1024 / 1024).toFixed(1) }} MB
            </span>
          </p>
        </div>
      </div>

      <!-- Audio Preview -->
      <div v-if="versions.currentVersion.audio_previews?.length" class="card p-4 mb-6">
        <h3 class="text-sm font-medium mb-3">Аудио-превью</h3>
        <AudioPlayer
          v-for="preview in versions.currentVersion.audio_previews"
          :key="preview.id"
          :src="resolveApiUrl(`/api/v1/projects/${projectId}/versions/${verId}/previews/${preview.id}/stream`)"
          :title="preview.title"
          :disabled="deletingPreviewId === preview.id"
          @delete="handleDeletePreview(preview.id)"
        />
      </div>

      <div class="card p-4 mb-6">
        <h3 class="text-sm font-medium mb-3">Загрузить превью</h3>
        <label class="flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-input-border p-3 cursor-pointer hover:border-primary transition-colors">
          <svg class="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5l7-7 7 7h-2a2 2 0 00-2 2v6" />
          </svg>
          <span class="text-sm text-secondary">{{ previewFile ? previewFile.name : 'Выберите аудиофайл (MP3, WAV, FLAC)' }}</span>
          <input type="file" class="hidden" accept=".mp3,.wav,.flac,.aif,.aiff" @change="onPreviewFileChange" />
        </label>
        <div v-if="previewFile && !uploadingPreview" class="flex items-center justify-between mt-2">
          <span class="text-xs text-secondary">{{ (previewFile.size / 1024 / 1024).toFixed(1) }} MB</span>
          <UiButton size="sm" :loading="uploadingPreview" @click="handlePreviewUpload">Загрузить</UiButton>
        </div>
      </div>

      <!-- Description -->
      <p v-if="versions.currentVersion.description" class="text-sm mb-6">
        {{ versions.currentVersion.description }}
      </p>

      <!-- Files -->
      <div class="card p-4 mb-6">
        <h3 class="text-sm font-medium mb-3">Файлы</h3>
        <div class="space-y-1">
            <div
            v-for="f in versions.files"
            :key="f.file_name"
            class="flex items-center justify-between text-sm py-1"
          >
            <span class="truncate">{{ f.file_name }}</span>
            <div class="flex items-center gap-2 shrink-0">
              <span class="text-secondary text-xs">{{ (f.file_size / 1024).toFixed(1) }} KB</span>
              <div v-if="downloadingFileId === f.id" class="flex items-center gap-1 text-xs text-secondary">
                <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                {{ fileDownloadProgress }}%
              </div>
              <button
                v-else
                class="text-secondary hover:text-primary transition-colors"
                title="Скачать"
                @click="handleDownload(f)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        <div v-if="!versions.files.length" class="text-sm text-secondary py-2">Нет загруженных файлов</div>


      </div>

      <!-- Comments -->
      <!-- Tasks / Checklist -->
      <div class="mt-8 card p-4">
        <h3 class="text-sm font-semibold mb-3">Чеклист</h3>

        <div class="space-y-1 mb-3">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="flex items-center gap-2 group"
          >
            <input
              :checked="task.is_done"
              type="checkbox"
              class="rounded border-border text-primary focus:ring-primary shrink-0"
              @change="toggleTask(task)"
            />
            <span
              class="text-sm flex-1"
              :class="{ 'line-through text-secondary': task.is_done }"
            >
              {{ task.text }}
            </span>
            <button
              class="opacity-0 group-hover:opacity-100 text-secondary hover:text-danger transition-all p-1"
              @click="deleteTask(task.id)"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="flex gap-2">
          <input
            v-model="taskText"
            placeholder="Добавить задачу..."
            class="flex-1 rounded-lg input-control px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            @keyup.enter="addTask"
          />
          <UiButton size="sm" :loading="addingTask" @click="addTask">Добавить</UiButton>
        </div>
      </div>

      <div class="mt-8">
        <h3 class="text-lg font-semibold mb-4">Комментарии ({{ versions.comments.length }})</h3>

        <div class="flex gap-3 mb-6">
          <UiAvatar :src="auth.user?.avatar_url" :alt="auth.user?.nickname" size="sm" />
          <div class="flex-1">
            <UiRichEditor v-model="commentText" placeholder="Напишите комментарий..." />
            <div class="flex justify-end mt-2">
              <UiButton size="sm" :loading="loadingComment" @click="handleAddComment">
                Отправить
              </UiButton>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <div
            v-for="comment in versions.comments"
            :key="comment.id"
            class="flex gap-3"
          >
            <UiAvatarRing :src="comment.avatar_url" :alt="comment.nickname" size="sm" :badge="(comment as any).active_badge" />
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <NuxtLink
                  :to="`/profile/${comment.username}`"
                  class="text-sm font-medium hover:text-primary transition-colors"
                >
                  <span class="flex items-center gap-1">{{ comment.nickname }}<UserBadgeIcon :badge="(comment as any).active_badge" size="sm" /></span>
                </NuxtLink>
                <span class="text-xs text-secondary">
                  {{ new Date(comment.created_at).toLocaleDateString() }}
                </span>
              </div>
              <div class="text-sm" v-html="comment.text" />
            </div>
            <button
              v-if="auth.user?.id === comment.user_id"
              class="text-secondary hover:text-danger transition-colors shrink-0"
              @click="handleDeleteComment(comment.id)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div v-if="versions.comments.length === 0" class="text-sm text-secondary text-center py-8">
            Пока нет комментариев
          </div>
        </div>
      </div>
    </template>
  </div>

  <UiModal v-model="showDownloadModal" title="Скачать версию" max-width="420px">
    <div class="flex flex-col gap-3 p-1">
      <p class="text-sm text-secondary leading-relaxed">
        Выберите способ загрузки:
      </p>
      <UiButton
        class="w-full flex items-center justify-center gap-2 h-10"
        :disabled="downloadingFileId === verId && !downloadVersionId"
        @click="handleDownloadZip()"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Скачать ZIP
      </UiButton>
      <UiButton
        variant="secondary"
        class="w-full flex items-center justify-center gap-2 h-10"
        :disabled="downloadingFileId === verId"
        @click="handleUpdateProjectFiles"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Обновить файлы проекта
      </UiButton>
    </div>
  </UiModal>
</template>
