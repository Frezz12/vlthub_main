<script setup lang="ts">
import type { ProjectActivityOut } from '@pjasaver/shared-types'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const projects = useProjectsStore()
const toast = inject('toast') as { show: (msg: string, type?: 'success' | 'error' | 'info') => void }

const loading = ref(true)
const items = ref<ProjectActivityOut[]>([])
const total = ref(0)

const EVENT_LABELS: Record<string, string> = {
  create_project: 'Проект создан',
  update_project: 'Проект обновлён',
  create_version: 'Новая версия',
  update_version: 'Версия изменена',
  delete_version: 'Версия удалена',
  set_current_version: 'Текущая версия изменена',
  download_version_zip: 'Скачан архив версии',
  download_version_file: 'Скачан файл из версии',
  upload_version_archive: 'Загружен архив версии',
  upload_version_archive_chunked: 'Загружен архив (чанки)',
  upload_preview: 'Добавлено аудио-превью',
  delete_preview: 'Превью удалено',
  create_comment: 'Комментарий',
  delete_comment: 'Комментарий удалён',
  create_task: 'Задача добавлена',
  complete_task: 'Задача выполнена',
  delete_task: 'Задача удалена',
}

function eventTitle(type: string) {
  return EVENT_LABELS[type] || type
}

function formatWhen(iso: string) {
  try {
    return new Date(iso).toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function detailsSummary(row: ProjectActivityOut): string | null {
  const d = row.details
  if (!d || typeof d !== 'object') return null
  const parts: string[] = []
  if (typeof d.file_name === 'string') parts.push(d.file_name)
  if (typeof d.version_number === 'number') parts.push(`№ ${d.version_number}`)
  if (typeof d.title === 'string' && d.title) parts.push(String(d.title))
  if (Array.isArray(d.fields)) parts.push(`поля: ${(d.fields as string[]).join(', ')}`)
  if (typeof d.snippet === 'string' && d.snippet) parts.push(`«${d.snippet.slice(0, 80)}${d.snippet.length > 80 ? '…' : ''}»`)
  if (typeof d.text === 'string' && d.text) parts.push(`«${d.text.slice(0, 60)}${d.text.length > 60 ? '…' : ''}»`)
  return parts.length ? parts.join(' · ') : null
}

onMounted(async () => {
  const id = route.params.id as string
  loading.value = true
  try {
    await projects.fetchProject(id)
    const res = await projects.fetchProjectActivity(id)
    items.value = res.items
    total.value = res.total
  } catch (e: any) {
    toast.show(e?.message || 'Не удалось загрузить журнал', 'error')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-shell max-w-3xl">
    <div class="flex items-center justify-between gap-4 mb-8">
      <div>
        <NuxtLink :to="`/projects/${route.params.id}`" class="text-sm text-secondary hover:text-primary mb-1 inline-block">
          ← К проекту
        </NuxtLink>
        <h1 class="text-2xl font-semibold">
          Журнал событий
        </h1>
        <p v-if="projects.currentProject" class="text-secondary text-sm mt-1">
          {{ projects.currentProject.title }}
        </p>
      </div>
    </div>

    <div v-if="loading" class="animate-pulse space-y-3">
      <div v-for="i in 6" :key="i" class="h-16 bg-btn-secondary rounded-lg" />
    </div>

    <div v-else-if="!items.length" class="card p-8 text-center text-secondary">
      Пока нет записей. Создавайте версии, загружайте файлы и общайтесь в комментариях — события появятся здесь.
    </div>

    <TransitionGroup v-else name="stagger" tag="ol" class="relative border-l border-separator pl-6 space-y-6 ml-2">
      <li v-for="row in items" :key="row.id" class="relative">
        <span class="absolute -left-[30px] top-1.5 w-3 h-3 rounded-full bg-primary ring-4 ring-[var(--color-avatar-ring)]" />
        <div class="card p-4">
          <div class="flex flex-wrap items-baseline justify-between gap-2 gap-y-1">
            <span class="font-medium">{{ eventTitle(row.event_type) }}</span>
            <span class="text-xs text-secondary tabular-nums">{{ formatWhen(row.created_at) }}</span>
          </div>
          <p class="text-sm text-secondary mt-1">
            <span class="font-medium text-primary">{{ row.user.nickname }}</span>
            <span class="text-secondary"> @{{ row.user.username }}</span>
          </p>
          <p v-if="detailsSummary(row)" class="text-sm mt-2 text-secondary leading-snug">
            {{ detailsSummary(row) }}
          </p>
          <p v-if="row.version_id" class="text-xs text-secondary/80 mt-2 font-mono">
            version: {{ row.version_id.slice(0, 8) }}…
          </p>
        </div>
      </li>
    </TransitionGroup>

    <p v-if="total > items.length" class="text-xs text-secondary mt-6">
      Показано {{ items.length }} из {{ total }} записей.
    </p>
  </div>
</template>
