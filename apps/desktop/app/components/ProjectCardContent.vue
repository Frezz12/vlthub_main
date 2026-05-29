<script setup lang="ts">
import type { ProjectOut } from '@pjasaver/shared-types'

const { getDawName, getDawColor } = useDawIcon()
const auth = useAuthStore()

interface Props {
  project: ProjectOut
  isAccessible?: boolean
  canArchive?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isAccessible: false,
  canArchive: false,
})

const emit = defineEmits<{
  archive: [projectId: string]
  favorite: [projectId: string]
}>()

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 MB'
  const gb = bytes / 1_073_741_824
  if (gb >= 1) return gb.toFixed(2) + ' GB'
  const mb = bytes / 1_048_576
  return mb.toFixed(1) + ' MB'
}

const dawColor = computed(() => getDawColor(props.project.daw_type))
const dawName = computed(() => getDawName(props.project.daw_type))
</script>

<template>
  <div class="relative flex flex-col h-full">
    <div
      class="aspect-[16/9] -mx-4 -mt-4 mb-3 overflow-hidden bg-gradient-to-br from-[#F5F5F7] to-primary/10"
    >
      <img
        v-if="project.cover_url"
        :src="resolveApiUrl(project.cover_url)"
        :alt="project.title"
        class="w-full h-full object-cover"
      />
    </div>
    <div class="flex-1 flex flex-col">
      <!-- Top row: status + actions -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <span
            class="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md"
            :class="{
              'bg-green-100 dark:bg-green-500/15 text-green-700 dark:text-green-300': project.status === 'completed',
              'bg-blue-100 dark:bg-blue-500/15 text-blue-700 dark:text-blue-300': project.status === 'in_progress',
              'bg-yellow-100 dark:bg-yellow-500/15 text-yellow-700 dark:text-yellow-300': project.status === 'on_hold',
              'bg-red-100 dark:bg-red-500/15 text-red-700 dark:text-red-300': project.status === 'dropped',
            }"
          >
            <span
              class="w-1.5 h-1.5 rounded-full shrink-0"
              :class="{
                'bg-green-500': project.status === 'completed',
                'bg-blue-500': project.status === 'in_progress',
                'bg-yellow-500': project.status === 'on_hold',
                'bg-red-500': project.status === 'dropped',
              }"
            />
            {{ project.status === 'in_progress' ? 'В работе' : project.status === 'completed' ? 'Завершён' : project.status === 'on_hold' ? 'Отложен' : 'Закрыт' }}
          </span>
          <div
            class="flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-md bg-surface text-secondary"
          >
            <span
              class="w-2 h-2 rounded-full shrink-0"
              :style="{ backgroundColor: dawColor }"
            />
            {{ dawName }}
          </div>
        </div>
        <div class="flex items-center gap-0.5">
          <button
            class="p-1.5 rounded-lg hover:bg-border/50 transition-colors"
            :class="project.is_favorite ? 'text-yellow-500' : 'text-secondary hover:text-yellow-500'"
            :title="project.is_favorite ? 'Убрать из избранного' : 'В избранное'"
            @click.stop.prevent="emit('favorite', project.id)"
          >
            <svg class="w-4 h-4" :fill="project.is_favorite ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            </svg>
          </button>
          <button
            v-if="canArchive"
            class="p-1.5 rounded-lg hover:bg-border/50 transition-colors text-secondary hover:text-foreground"
            :title="project.is_archived ? 'Разархивировать' : 'Архивировать'"
            @click.stop.prevent="emit('archive', project.id)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Title -->
      <h3 class="text-base font-semibold text-foreground leading-snug mb-2 line-clamp-2">{{ project.title }}</h3>

      <!-- Chips row -->
      <div class="flex flex-wrap items-center gap-1.5 mb-3">
        <span v-if="project.bpm" class="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md bg-surface text-secondary font-medium">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
            <circle cx="12" cy="12" r="10" />
          </svg>
          {{ project.bpm }} BPM
        </span>
        <span v-if="project.key" class="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md bg-surface text-secondary font-medium">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
          </svg>
          {{ project.key }}
        </span>
        <span v-if="project.artists" class="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md bg-surface text-secondary font-medium truncate max-w-[140px]">
          <svg class="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
          feat. {{ project.artists }}
        </span>
      </div>

      <!-- Tags -->
      <div v-if="project.tags?.length" class="flex flex-wrap gap-1 mb-3">
        <span
          v-for="tag in project.tags.slice(0, 3)"
          :key="tag"
          class="text-[10px] px-1.5 py-0.5 rounded-md bg-btn-secondary/60 text-secondary"
        >
          #{{ tag }}
        </span>
        <span
          v-if="project.tags.length > 3"
          class="text-[10px] px-1.5 py-0.5 rounded-md bg-btn-secondary/60 text-secondary"
        >
          +{{ project.tags.length - 3 }}
        </span>
      </div>

      <!-- Spacer -->
      <div class="flex-1" />

      <!-- Bottom meta -->
      <div class="flex items-center justify-between pt-3 border-t border-separator/50">
        <div class="flex items-center gap-2 text-xs text-secondary min-w-0">
          <span v-if="project.owner" class="flex items-center gap-1.5 truncate">
            <span
              class="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0"
              :style="{ backgroundColor: dawColor + '20', color: dawColor }"
            >
              {{ project.owner.nickname?.[0]?.toUpperCase() || '?' }}
            </span>
            <span class="truncate flex items-center gap-1">{{ project.owner.nickname }}<UserBadgeIcon :badge="(project.owner as any).active_badge" size="sm" /></span>
          </span>
          <span class="shrink-0">·</span>
          <span class="shrink-0">{{ formatSize(project.total_size || 0) }}</span>
          <span class="shrink-0">·</span>
          <span class="shrink-0">{{ (project.collaborators?.length || 0) + 1 }} уч.</span>
        </div>
        <div class="flex items-center gap-1.5 shrink-0">
          <span
            v-if="isAccessible && project.access_granted_at"
            class="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-md text-success bg-success/10"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ new Date(project.access_granted_at).toLocaleDateString('ru-RU') }}
          </span>
          <span
            v-if="project.owner_id !== auth.user?.id && project.is_public"
            class="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-md text-emerald-500 bg-emerald-500/10"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
            Публичный
          </span>
          <span v-if="project.is_archived" class="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-md text-blue-400 bg-blue-500/10">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            Архив
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
