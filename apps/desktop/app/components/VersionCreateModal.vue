<script setup lang="ts">
interface Props {
  projectId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ created: [] }>()
const versions = useVersionsStore()
const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

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

const dawInfo = computed(() => {
  if (!folderFiles.value?.length) return null
  const { daw, projectFile } = archiver.detectDaw(folderFiles.value)
  return { daw, projectFile: projectFile?.name || null }
})

const folderSize = computed(() => {
  if (!folderFiles.value) return '0 MB'
  const total = folderFiles.value.reduce((s, f) => s + f.size, 0)
  return (total / 1024 / 1024).toFixed(1) + ' MB'
})

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    file.value = input.files[0]
    selectedMode.value = 'file'
    folderFiles.value = null
  }
}

async function onPickFolder() {
  const files = await archiver.pickFolder(false, props.projectId)
  if (files.length) {
    folderFiles.value = files
    selectedMode.value = 'folder'
    file.value = null
    const name = archiver.getPickedFolderName() || files[0].webkitRelativePath.split('/')[0]
    projectName.value = name
  }
}

async function handleSubmit() {
  if (!title.value) return
  loading.value = true
  uploadProgress.value = 0
  uploading.value = false

  try {
    const version = await versions.createVersion(props.projectId, {
      title: title.value,
      description: description.value || null,
    })

    if (selectedMode.value === 'folder' && folderFiles.value?.length) {
      uploading.value = true
      toast.show('Архивация проекта...', 'info')

      const tauriPath = archiver.getTauriArchivePath()
      if (tauriPath) {
        const up = useUploadProgress()
        up.registerUpload(version.id, props.projectId, projectName.value || 'project')
        await archiver.uploadTauriArchiveFromPath(tauriPath, props.projectId, version.id, auth.accessToken!, projectName.value || undefined)
      } else {
        const { blob } = await archiver.archiveProject(folderFiles.value, (pct) => {
          uploadProgress.value = pct
        })
        toast.show('Загрузка архива...', 'info')
        await archiver.uploadArchive(blob, props.projectId, version.id, auth.accessToken!, (pct) => {
          uploadProgress.value = 50 + Math.round(pct / 2)
        }, projectName.value || undefined)
      }
    } else if (selectedMode.value === 'file' && file.value) {
      uploading.value = true
      uploadProgress.value = 0

      const chunkSize = 8 * 1024 * 1024
      const totalSize = file.value.size
      const totalChunks = Math.ceil(totalSize / chunkSize)

      for (let i = 0; i < totalChunks; i++) {
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
        })

        uploadProgress.value = Math.round(((i + 1) / totalChunks) * 100)
      }
    }

    toast.show('Версия создана', 'success')
    emit('created')
  } catch (e: any) {
    const msg = e.message || ''
    if (msg.includes('Storage limit') || msg.includes('413')) {
      toast.show('Лимит хранилища исчерпан. Освободите место или увеличьте лимит.', 'error', 5000)
    } else {
      toast.show(msg || 'Ошибка', 'error')
    }
  } finally {
    loading.value = false
    uploading.value = false
  }
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
          <span class="text-sm text-secondary">{{ file ? file.name : 'ZIP, WAV, MP3...' }}</span>
          <input type="file" class="hidden" accept=".zip,.wav,.mp3,.aif,.aiff,.flac" @change="onFileChange" />
        </label>
        <span v-if="file" class="text-xs text-secondary shrink-0">{{ (file.size / 1024 / 1024).toFixed(1) }} MB</span>
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
    </div>

    <div class="flex justify-end gap-2 mt-2">
      <UiButton variant="secondary" @click="emit('created')">Отмена</UiButton>
      <UiButton :loading="loading" type="submit">{{ uploading ? 'Загрузка...' : 'Создать версию' }}</UiButton>
    </div>
  </form>
</template>
