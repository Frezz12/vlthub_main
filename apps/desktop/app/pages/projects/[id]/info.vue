<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
import { formatError } from '~/utils/formatError'

const route = useRoute()
const auth = useAuthStore()
const projects = useProjectsStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const isOwner = computed(() => projects.currentProject?.owner_id === auth.user?.id)

const title = ref('')
const artists = ref('')
const bpm = ref<number | null>(null)
const key = ref('')
const status = ref('in_progress')
const description = ref('')
const tags = ref('')
const beatmaker = ref('')

const is_archived = ref(false)
const is_public = ref(false)

const uploadingCover = ref(false)
const coverFile = ref<File | null>(null)
const coverPreview = ref<string | null>(null)

const keyOpen = ref(false)
const keyDropdownRef = ref<HTMLElement | null>(null)

const keyOptions = [
  { value: 'C', label: 'C major' },
  { value: 'Db', label: 'Db major' },
  { value: 'D', label: 'D major' },
  { value: 'Eb', label: 'Eb major' },
  { value: 'E', label: 'E major' },
  { value: 'F', label: 'F major' },
  { value: 'Gb', label: 'Gb major' },
  { value: 'G', label: 'G major' },
  { value: 'Ab', label: 'Ab major' },
  { value: 'A', label: 'A major' },
  { value: 'Bb', label: 'Bb major' },
  { value: 'B', label: 'B major' },
  { value: 'Cm', label: 'C minor' },
  { value: 'C#m', label: 'C# minor' },
  { value: 'Dm', label: 'D minor' },
  { value: 'Ebm', label: 'Eb minor' },
  { value: 'Em', label: 'E minor' },
  { value: 'Fm', label: 'F minor' },
  { value: 'F#m', label: 'F# minor' },
  { value: 'Gm', label: 'G minor' },
  { value: 'Abm', label: 'Ab minor' },
  { value: 'Am', label: 'A minor' },
  { value: 'Bbm', label: 'Bb minor' },
  { value: 'Bm', label: 'B minor' },
]

function handleClickOutside(e: MouseEvent) {
  if (keyDropdownRef.value && !keyDropdownRef.value.contains(e.target as Node)) {
    keyOpen.value = false
  }
}

const statusOptions = [
  { value: 'in_progress', label: 'В работе' },
  { value: 'completed', label: 'Завершён' },
  { value: 'on_hold', label: 'Отложен' },
  { value: 'dropped', label: 'Закрыт' },
]

onMounted(async () => {
  const p = await projects.fetchProject(route.params.id as string)
  if (p) {
    title.value = p.title
    artists.value = p.artists || ''
    bpm.value = p.bpm
    key.value = p.key || ''
    beatmaker.value = p.beatmaker || ''
    status.value = p.status
    description.value = p.description || ''
    tags.value = p.tags?.join(', ') || ''
    is_archived.value = p.is_archived
    is_public.value = p.is_public
  }
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => document.removeEventListener('click', handleClickOutside))

async function handleSave() {
  try {
    await projects.updateProject(route.params.id as string, {
      title: title.value,
      artists: artists.value || null,
      bpm: bpm.value,
      key: key.value || null,
      beatmaker: beatmaker.value || null,
      status: status.value,
      description: description.value || null,
      tags: tags.value ? tags.value.split(',').map((t) => t.trim()) : [],
      is_public: is_public.value,
    })
    toast.show('Проект обновлён', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

async function handleArchive() {
  try {
    await projects.updateProject(route.params.id as string, {
      is_archived: !is_archived.value,
    })
    is_archived.value = !is_archived.value
    toast.show(is_archived.value ? 'Проект архивирован' : 'Проект разархивирован', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

function onCoverFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files?.length) return
  coverFile.value = target.files[0]
  coverPreview.value = URL.createObjectURL(target.files[0])
}

async function handleCoverUpload() {
  if (!coverFile.value) return
  uploadingCover.value = true
  try {
    const formData = new FormData()
    formData.append('file', coverFile.value)
    const api = useApi()
    const res = await api.upload<{ cover_url: string }>(
      `/api/v1/projects/${route.params.id}/cover`,
      formData,
    )
    projects.currentProject!.cover_url = res.cover_url
    coverFile.value = null
    coverPreview.value = null
    toast.show('Обложка обновлена', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    uploadingCover.value = false
  }
}

async function handleLeave() {
  if (!confirm('Вы уверены, что хотите покинуть проект? Все права доступа будут удалены.')) return
  try {
    await projects.leaveProject(route.params.id as string)
    toast.show('Вы покинули проект', 'success')
    navigateTo('/')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}
</script>

<template>
  <div class="page-shell-narrow">
    <div class="flex items-center gap-3 mb-8">
      <NuxtLink
        :to="`/projects/${route.params.id}`"
        class="text-secondary hover:text-primary transition-colors"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
      </NuxtLink>
      <h1 class="text-2xl font-semibold">Настройки проекта</h1>
    </div>

    <div class="card p-6">
      <form class="flex flex-col gap-4" @submit.prevent="handleSave">
        <UiInput v-model="title" label="Название" />
        <UiInput v-model="artists" label="Приглащенные артисты" />
        <div class="grid grid-cols-2 gap-3">
          <UiInput v-model="bpm" label="BPM" type="number" />
          <div class="flex flex-col gap-1.5 relative" ref="keyDropdownRef">
            <label class="text-sm font-medium">Тональность</label>
            <button
              type="button"
              class="w-full flex items-center justify-between rounded-lg input-control px-4 py-2 text-sm hover:border-input-border transition-colors text-left"
              @click="keyOpen = !keyOpen"
            >
              {{ keyOptions.find(o => o.value === key)?.label || '—' }}
              <svg class="w-3.5 h-3.5 text-secondary transition-transform" :class="{ 'rotate-180': keyOpen }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <Transition name="dropdown">
              <div
                v-if="keyOpen"
                class="absolute left-0 top-full mt-1 w-full rounded-lg bg-surface-elevated border border-border shadow-lg z-20 overflow-hidden max-h-48 overflow-y-auto"
              >
                <button
                  v-for="opt in keyOptions"
                  :key="opt.value"
                  type="button"
                  class="w-full px-3.5 py-2 text-sm text-left transition-colors"
                  :class="key === opt.value ? 'bg-primary/5 text-primary font-medium' : 'text-foreground hover:bg-surface'"
                  @click="key = opt.value; keyOpen = false"
                >
                  {{ opt.label }}
                </button>
              </div>
            </Transition>
          </div>
        </div>
        <UiInput v-model="beatmaker" label="Битмейкер" />
        <div>
          <label class="block text-sm font-medium mb-1">Статус</label>
          <select
            v-model="status"
            class="w-full rounded-lg input-control px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
        <UiInput v-model="tags" label="Теги (через запятую)" />
        <UiInput v-model="description" label="Описание" />

        <label class="flex items-center justify-between p-4 rounded-xl bg-input-bg cursor-pointer">
          <div>
            <span class="text-sm font-medium block">Публичный проект</span>
            <span class="text-xs text-secondary">Доступен всем пользователям</span>
          </div>
          <input
            v-model="is_public"
            type="checkbox"
            class="rounded border-border text-primary focus:ring-primary w-4 h-4"
          />
        </label>

        <div class="flex justify-end gap-2 mt-2">
          <NuxtLink :to="`/projects/${route.params.id}`">
            <UiButton variant="secondary">Отмена</UiButton>
          </NuxtLink>
          <UiButton type="submit">Сохранить</UiButton>
        </div>
      </form>
    </div>

    <div class="card p-6 mt-4">
      <h3 class="text-sm font-medium mb-3">Обложка проекта</h3>
      <div class="flex items-start gap-6">
        <div
          class="relative w-48 rounded-xl overflow-hidden bg-gradient-to-br from-btn-secondary to-surface-elevated group cursor-pointer border-2 border-dashed border-input-border hover:border-primary/40 transition-all"
          :class="coverFile || projects.currentProject?.cover_url ? 'border-transparent hover:border-primary/40' : ''"
        >
          <div class="aspect-square relative">
            <img
              v-if="coverPreview || projects.currentProject?.cover_url"
              :src="coverPreview || resolveApiUrl(projects.currentProject?.cover_url || '')"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex flex-col items-center justify-center gap-2">
              <svg class="w-10 h-10 text-secondary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span class="text-xs text-secondary/50">Выберите изображение</span>
            </div>
            <div
              class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all flex items-center justify-center"
            >
              <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
            </div>
            <input
              type="file"
              accept="image/*"
              class="absolute inset-0 opacity-0 cursor-pointer z-10"
              @change="onCoverFileChange"
            />
          </div>
        </div>

        <div v-if="coverFile" class="flex-1 flex flex-col gap-2 pt-2">
          <span class="text-sm font-medium truncate">{{ coverFile.name }}</span>
          <span class="text-xs text-secondary">{{ (coverFile.size / 1024).toFixed(0) }} KB</span>
          <UiButton size="sm" :loading="uploadingCover" @click="handleCoverUpload" class="self-start mt-1">
            Загрузить обложку
          </UiButton>
        </div>
      </div>
    </div>

    <div v-if="isOwner" class="card p-6 mt-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium">Архивировать проект</h3>
          <p class="text-xs text-secondary mt-0.5">Архивные проекты скрыты с главной страницы</p>
        </div>
        <UiButton
          :variant="is_archived ? 'secondary' : 'danger'"
          size="sm"
          @click="handleArchive"
        >
          {{ is_archived ? 'Разархивировать' : 'Архивировать' }}
        </UiButton>
      </div>
    </div>

    <div v-if="!isOwner" class="card p-6 mt-4 border border-danger/30">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium text-danger">Покинуть проект</h3>
          <p class="text-xs text-secondary mt-0.5">Вы перестанете иметь доступ к этому проекту</p>
        </div>
        <UiButton variant="danger" size="sm" @click="handleLeave">
          Покинуть
        </UiButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dropdown-enter-active {
  transition: all 0.15s ease-out;
}
.dropdown-leave-active {
  transition: all 0.1s ease-in;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
