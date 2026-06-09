<script setup lang="ts">
interface Props {
  projectId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ created: [] }>()
const versions = useVersionsStore()
const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }
import { formatError } from '~/utils/formatError'
import { useApiFetch } from '~/composables/useApiFetch'

const archiver = useProjectArchiver()

const title = ref('')
const description = ref('')
const file = ref<File | null>(null)
const folderFiles = ref<File[] | null>(null)
const selectedMode = ref<'file' | 'folder' | null>(null)
const loading = ref(false)
const uploadProgress = ref(0)
const uploading = ref(false)
const projectName = ref('')
const archiveAbort = ref<AbortController | null>(null)
const createdVersionId = ref<string | null>(null)
const cancelled = ref(false)
const previewFile = ref<File | null>(null)
const uploadingPreview = ref(false)
const folderInput = ref<HTMLInputElement | null>(null)

function isTauri(): boolean {
  try {
    return typeof window !== 'undefined' && ((window as any).__TAURI__ !== undefined || (window as any).__TAURI_INTERNALS__ !== undefined)
  } catch { return false }
}

function onFolderChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files ? Array.from(input.files) : []
  if (!files.length) return
  selectedMode.value = 'folder'
  file.value = null
  folderFiles.value = files
  projectName.value = files[0].webkitRelativePath.split('/')[0]
}

const dawInfo = computed(() => folderFiles.value?.length ? archiver.detectDaw(folderFiles.value) : null)
const folderSize = computed(() => {
  if (!folderFiles.value?.length) return ''
  const total = folderFiles.value.reduce((s, f) => s + f.size, 0)
  return total > 1024 * 1024
    ? (total / 1024 / 1024).toFixed(1) + ' MB'
    : (total / 1024).toFixed(1) + ' KB'
})

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    file.value = input.files[0]
    selectedMode.value = 'file'
    folderFiles.value = null
  }
}

function onPreviewFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) previewFile.value = input.files[0]
}

async function onPickFolder() {
  if (isTauri()) {
    archiver.clearCache()
    const files = await archiver.pickFolder(true, props.projectId)
    if (files.length) {
      folderFiles.value = files
      selectedMode.value = 'folder'
      file.value = null
      projectName.value = archiver.getPickedFolderName() || files[0].webkitRelativePath.split('/')[0]
    }
  } else {
    folderInput.value?.click()
  }
}

async function handleSubmit() {
  if (!title.value || cancelled.value) return
  loading.value = true
  uploadProgress.value = 0
  uploading.value = false
  cancelled.value = false

  archiveAbort.value = new AbortController()

  try {
    // Create version on backend but don't add to frontend list yet
    const verRes = await fetch(__API_BASE_URL__ + `/api/v1/projects/${props.projectId}/versions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${auth.accessToken}` },
      body: JSON.stringify({ title: title.value, description: description.value || null }),
    })
    if (!verRes.ok) throw new Error('Failed to create version')
    const version = await verRes.json()
    createdVersionId.value = version.id

    if (cancelled.value) return

    if (selectedMode.value === 'folder' && folderFiles.value?.length) {
      uploading.value = true
      toast.show('Архивация проекта...', 'info')

      const tauriPath = archiver.getTauriArchivePath()
      if (tauriPath) {
        uploadProgress.value = 30
        const up = useUploadProgress()
        up.registerUpload(version.id, props.projectId, projectName.value || 'project', cancelArchive)
        await archiver.uploadTauriArchiveFromPath(tauriPath, props.projectId, version.id, auth.accessToken!, projectName.value || undefined)
        uploadProgress.value = 100
      } else {
        uploadProgress.value = 5
        const { blob } = await archiver.archiveProject(folderFiles.value, (pct) => {
          if (cancelled.value) return
          uploadProgress.value = pct
        }, archiveAbort.value.signal)
        if (cancelled.value) return
        uploadProgress.value = 50
        toast.show('Загрузка архива...', 'info')
        await archiver.uploadArchive(blob, props.projectId, version.id, auth.accessToken!, (pct) => {
          if (cancelled.value) return
          uploadProgress.value = 50 + Math.round(pct / 2)
        }, projectName.value || undefined, archiveAbort.value.signal)
        uploadProgress.value = 100
      }
    } else if (selectedMode.value === 'file' && file.value) {
      uploading.value = true
      uploadProgress.value = 0

      const chunkSize = 8 * 1024 * 1024
      const totalSize = file.value.size
      const totalChunks = Math.ceil(totalSize / chunkSize)

      for (let i = 0; i < totalChunks; i++) {
        if (cancelled.value) return
        const start = i * chunkSize
        const end = Math.min(start + chunkSize, totalSize)
        const chunk = file.value.slice(start, end)
        const formData = new FormData()
        formData.append('file', chunk, file.value.name)
        const params = new URLSearchParams({ offset: String(start), total_size: String(totalSize) })

        await fetch(__API_BASE_URL__ + `/api/v1/projects/${props.projectId}/versions/${version.id}/upload/chunk?${params}`, {
          method: 'PUT',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: formData,
          signal: archiveAbort.value.signal,
        })

        uploadProgress.value = Math.round(((i + 1) / totalChunks) * 100)
      }
    }

    if (cancelled.value) return

    // Upload audio preview if selected
    if (previewFile.value) {
      uploadingPreview.value = true
      try {
        const fd = new FormData()
        fd.append('file', previewFile.value)
        fd.append('title', previewFile.value.name.replace(/\.[^/.]+$/, ''))
        await fetch(__API_BASE_URL__ + `/api/v1/projects/${props.projectId}/versions/${version.id}/previews`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: fd,
        })
      } catch { /* preview is optional */ }
      uploadingPreview.value = false
    }

    // Add version to frontend list only after successful upload
    versions.items.unshift(version)
    versions.total++
    toast.show('Версия создана', 'success')
    emit('created')
  } catch (e: any) {
    if (e.name === 'AbortError' || cancelled.value) return
    toast.show(formatError(e), 'error', 5000)
  } finally {
    loading.value = false
    uploading.value = false
    if (cancelled.value) {
      const verId = createdVersionId.value
      if (verId) {
        try {
          await useApiFetch(`/api/v1/projects/${props.projectId}/versions/${verId}`, {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${auth.accessToken}` },
          })
        } catch { /* ignore */ }
      }
    }
    archiveAbort.value = null
    createdVersionId.value = null
  }
}

function cancelArchive() {
  cancelled.value = true
  archiveAbort.value?.abort()
  emit('created')
}


</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
    <UiInput v-model="title" label="Название версии" placeholder="Сведение" />
    <UiInput v-model="description" label="Описание" placeholder="Что изменилось..." />

    <div class="border-t border-separator pt-4 space-y-4">
      <div>
        <label class="text-sm font-medium mb-2 block">Папка проекта DAW</label>
        <div
          class="flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-input-border p-4 cursor-pointer hover:border-primary transition-colors"
          @click="onPickFolder"
        >
          <svg class="w-5 h-5 text-secondary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <span class="text-sm text-secondary">
            {{ folderFiles ? `Выбрано: ${projectName}` : 'Выберите папку проекта (Logic, Ableton, FL...)' }}
          </span>
          <input ref="folderInput" type="file" class="hidden" webkitdirectory @change="onFolderChange" />
        </div>

        <div v-if="dawInfo" class="mt-2 flex items-center gap-2 text-xs text-secondary">
          <span class="px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">{{ dawInfo.daw || 'Неизвестная DAW' }}</span>
          <span>{{ folderFiles?.length }} файлов</span>
          <span>{{ folderSize }}</span>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <span class="text-xs text-secondary shrink-0">Или загрузите файл:</span>
        <label class="flex-1 flex items-center justify-center gap-2 rounded-lg border border-dashed border-input-border p-3 cursor-pointer hover:border-primary transition-colors">
          <svg class="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span class="text-sm text-secondary">{{ file ? file.name : 'ZIP' }}</span>
          <input type="file" class="hidden" accept=".zip" @change="onFileChange" />
        </label>
        <span v-if="file" class="text-xs text-secondary shrink-0">{{ (file.size / 1024 / 1024).toFixed(1) }} MB</span>
      </div>

      <div class="flex items-center gap-3">
        <span class="text-xs text-secondary shrink-0">Превью версии:</span>
        <label class="flex-1 flex items-center justify-center gap-2 rounded-lg border border-dashed border-input-border p-3 cursor-pointer hover:border-primary transition-colors">
          <svg class="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
          </svg>
          <span class="text-sm text-secondary">{{ previewFile ? previewFile.name : 'MP3, WAV, FLAC...' }}</span>
          <input type="file" class="hidden" accept=".mp3,.wav,.flac,.aif,.aiff" @change="onPreviewFileChange" />
        </label>
        <span v-if="previewFile" class="text-xs text-secondary shrink-0">{{ (previewFile.size / 1024 / 1024).toFixed(1) }} MB</span>
      </div>
    </div>

    <div v-if="uploading" class="flex flex-col gap-1">
      <div class="flex items-center justify-between text-xs text-secondary">
        <span>{{ selectedMode === 'folder' ? 'Архивация и загрузка...' : 'Загрузка...' }}</span>
        <span>{{ uploadProgress }}%</span>
      </div>
      <div class="h-1.5 rounded-full bg-btn-secondary overflow-hidden">
        <div class="h-full rounded-full bg-primary transition-all duration-300" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <button
        type="button"
        class="mt-1 text-xs text-danger/70 hover:text-danger transition-colors self-end"
        @click="cancelArchive"
      >
        Отмена
      </button>
    </div>

    <div class="flex justify-end gap-2 mt-2">
      <UiButton variant="secondary" @click="emit('created')">Отмена</UiButton>
      <UiButton :loading="loading" type="submit">{{ uploading ? 'Загрузка...' : 'Создать версию' }}</UiButton>
    </div>
  </form>
</template>
