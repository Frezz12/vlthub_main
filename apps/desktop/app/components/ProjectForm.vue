<script setup lang="ts">
import type { DawType } from '@pjasaver/shared-types'
import { formatError } from '~/utils/formatError'

const emit = defineEmits<{ created: [] }>()
const projects = useProjectsStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const title = ref('')
const dawType = ref<DawType>('logic_pro')
const bpm = ref<number | null>(null)
const key = ref('')
const artists = ref('')
const beatmaker = ref('')
const status = ref('in_progress')
const description = ref('')
const tags = ref('')
const isPublic = ref(false)
const coverFile = ref<File | null>(null)
const coverPreview = ref('')
const loading = ref(false)
const dawOpen = ref(false)
const dawDropdownRef = ref<HTMLElement | null>(null)
const keyOpen = ref(false)
const keyDropdownRef = ref<HTMLElement | null>(null)
const statusOpen = ref(false)
const statusDropdownRef = ref<HTMLElement | null>(null)
const coverInputRef = ref<HTMLInputElement | null>(null)

const statusOptions = [
  { value: 'in_progress', label: 'В работе', dotCls: 'bg-blue-500' },
  { value: 'completed', label: 'Завершён', dotCls: 'bg-green-500' },
  { value: 'on_hold', label: 'Отложен', dotCls: 'bg-yellow-500' },
  { value: 'dropped', label: 'Закрыт', dotCls: 'bg-red-500' },
]

const statusOptionCls = computed(() => {
  const found = statusOptions.find(s => s.value === status.value)
  if (!found) return 'bg-btn-secondary/60'
  switch (found.value) {
    case 'in_progress': return 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300'
    case 'completed': return 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-300'
    case 'on_hold': return 'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-700 dark:text-yellow-300'
    case 'dropped': return 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-300'
    default: return 'bg-btn-secondary/60'
  }
})

function handleDawClickOutside(e: MouseEvent) {
  if (dawDropdownRef.value && !dawDropdownRef.value.contains(e.target as Node)) {
    dawOpen.value = false
  }
  if (keyDropdownRef.value && !keyDropdownRef.value.contains(e.target as Node)) {
    keyOpen.value = false
  }
  if (statusDropdownRef.value && !statusDropdownRef.value.contains(e.target as Node)) {
    statusOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleDawClickOutside))
onUnmounted(() => document.removeEventListener('click', handleDawClickOutside))

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

const dawOptions: { value: DawType; label: string }[] = [
  { value: 'logic_pro', label: 'Logic Pro' },
  { value: 'ableton', label: 'Ableton Live' },
  { value: 'fl_studio', label: 'FL Studio' },
  { value: 'cubase', label: 'Cubase' },
  { value: 'reaper', label: 'REAPER' },
  { value: 'studio_one', label: 'Studio One' },
  { value: 'bitwig', label: 'Bitwig' },
  { value: 'other', label: 'Другое' },
]

function onCoverSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  coverFile.value = file
  const reader = new FileReader()
  reader.onload = () => { coverPreview.value = reader.result as string }
  reader.readAsDataURL(file)
}

async function handleSubmit() {
  if (!title.value) return
  loading.value = true
  try {
    const project = await projects.createProject({
      title: title.value,
      daw_type: dawType.value,
      bpm: bpm.value,
      key: key.value || null,
      artists: artists.value || null,
      beatmaker: beatmaker.value || null,
      status: status.value,
      description: description.value || null,
      tags: tags.value ? tags.value.split(',').map((t) => t.trim()) : [],
      is_public: isPublic.value,
    })
    if (coverFile.value) {
      const api = useApi()
      const form = new FormData()
      form.append('file', coverFile.value)
      await api.upload(`/api/v1/projects/${project.id}/cover`, form)
    }
    toast.show('Проект создан', 'success')
    emit('created')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
    <UiInput v-model="title" label="Название проекта" />

    <div class="flex flex-col gap-1.5">
      <label class="text-sm font-medium">Обложка</label>
      <button
        type="button"
        class="relative w-full aspect-video rounded-xl border-2 border-dashed border-border/40 hover:border-primary/40 transition-colors overflow-hidden bg-surface/50 flex items-center justify-center"
        @click="coverInputRef?.click()"
      >
        <img v-if="coverPreview" :src="coverPreview" class="absolute inset-0 w-full h-full object-cover" />
        <div v-else class="flex flex-col items-center gap-1 text-secondary">
          <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <span class="text-xs">Загрузить обложку</span>
        </div>
      </button>
      <input ref="coverInputRef" type="file" accept="image/*" class="hidden" @change="onCoverSelect" />
    </div>

    <div class="flex flex-col gap-1.5 relative" ref="dawDropdownRef">
      <label class="text-sm font-medium">DAW</label>
      <button
        type="button"
        class="w-full flex items-center justify-between rounded-lg input-control px-4 py-2 text-sm hover:border-input-border transition-colors text-left"
        @click="dawOpen = !dawOpen"
      >
        {{ dawOptions.find(o => o.value === dawType)?.label }}
        <svg class="w-3.5 h-3.5 text-secondary transition-transform" :class="{ 'rotate-180': dawOpen }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <Transition name="dropdown">
        <div
          v-if="dawOpen"
          class="absolute left-0 top-full mt-1 w-full rounded-lg bg-surface-elevated border border-border shadow-lg z-20 overflow-hidden"
        >
          <button
            v-for="opt in dawOptions"
            :key="opt.value"
            type="button"
            class="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-left transition-colors"
            :class="dawType === opt.value ? 'bg-primary/5 text-primary font-medium' : 'text-foreground hover:bg-surface'"
            @click="dawType = opt.value; dawOpen = false"
          >
            <span
              class="w-2 h-2 rounded-full shrink-0"
              :class="{
                'bg-[#000000]': opt.value === 'logic_pro',
                'bg-[#0000FF]': opt.value === 'ableton',
                'bg-[#FF6600]': opt.value === 'fl_studio',
                'bg-[#00BFFF]': opt.value === 'cubase',
                'bg-[#6B3FA0]': opt.value === 'reaper',
                'bg-[#00A86B]': opt.value === 'studio_one',
                'bg-[#FF4400]': opt.value === 'bitwig',
                'bg-[#86868B]': opt.value === 'other',
              }"
            />
            {{ opt.label }}
          </button>
        </div>
      </Transition>
    </div>

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
    <UiInput v-model="artists" label="Приглащенные артисты" />
    <UiInput v-model="beatmaker" label="Битмейкер" />

    <div class="flex flex-col gap-1.5 relative" ref="statusDropdownRef">
      <label class="text-sm font-medium">Статус</label>
      <button
        type="button"
        class="w-full flex items-center justify-between rounded-lg input-control px-4 py-2 text-sm hover:border-input-border transition-colors text-left"
        :class="statusOptionCls"
        @click="statusOpen = !statusOpen"
      >
        {{ statusOptions.find(s => s.value === status)?.label }}
        <svg class="w-3.5 h-3.5 text-secondary transition-transform" :class="{ 'rotate-180': statusOpen }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <Transition name="dropdown">
        <div
          v-if="statusOpen"
          class="absolute left-0 top-full mt-1 w-full rounded-lg bg-surface-elevated border border-border shadow-lg z-20 overflow-hidden"
        >
          <button
            v-for="opt in statusOptions"
            :key="opt.value"
            type="button"
            class="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-left transition-colors"
            :class="status === opt.value ? 'bg-primary/5 text-primary font-medium' : 'text-foreground hover:bg-surface'"
            @click="status = opt.value; statusOpen = false"
          >
            <span class="w-2 h-2 rounded-full shrink-0" :class="opt.dotCls" />
            {{ opt.label }}
          </button>
        </div>
      </Transition>
    </div>

    <UiInput v-model="tags" label="Теги (через запятую)" />
    <UiInput v-model="description" label="Описание" />

    <label class="flex items-center justify-between p-4 rounded-xl bg-input-bg cursor-pointer">
      <div>
        <span class="text-sm font-medium block">Публичный проект</span>
        <span class="text-xs text-secondary">Доступен всем пользователям</span>
      </div>
      <input
        v-model="isPublic"
        type="checkbox"
        class="rounded border-border text-primary focus:ring-primary w-4 h-4"
      />
    </label>

    <div class="flex justify-end gap-2 mt-2">
      <UiButton variant="secondary" @click="emit('created')">Отмена</UiButton>
      <UiButton :loading="loading" type="submit">Создать</UiButton>
    </div>
  </form>
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
