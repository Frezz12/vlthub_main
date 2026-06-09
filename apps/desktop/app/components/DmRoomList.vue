<script setup lang="ts">
import type { DirectMessageRoomData } from '~/stores/dm'

interface Props {
  activeUserId: string | null
}

const props = defineProps<Props>()
const emit = defineEmits<{ select: [userId: string] }>()

const dm = useDMStore()
const auth = useAuthStore()

const searchQuery = ref('')
const searchResults = ref<{ id: string; nickname: string; username: string; avatar_url: string | null }[]>([])
const searching = ref(false)
const showSearch = ref(false)
const deleteConfirmRoom = ref<DirectMessageRoomData | null>(null)
const contextMenuRoom = ref<{ room: DirectMessageRoomData; x: number; y: number } | null>(null)

const ONLINE_WINDOW = 5 * 60 * 1000
const onlineTick = ref(0)
let onlineInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  dm.fetchRooms()
  document.addEventListener('mousedown', closeContextMenu)
  onlineInterval = setInterval(() => { onlineTick.value++ }, 30000)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', closeContextMenu)
  if (onlineInterval) clearInterval(onlineInterval)
})

function closeContextMenu() {
  contextMenuRoom.value = null
}

function onContextMenu(e: MouseEvent, room: DirectMessageRoomData) {
  e.preventDefault()
  e.stopPropagation()
  const x = Math.min(e.clientX, window.innerWidth - 180 - 12)
  const y = Math.min(e.clientY, window.innerHeight - 140 - 12)
  contextMenuRoom.value = { room, x: Math.max(12, x), y: Math.max(12, y) }
}

async function searchUsers() {
  const q = searchQuery.value.trim()
  if (!q) { searchResults.value = []; return }
  searching.value = true
  try {
    const res = await useApiFetch<{ id: string; nickname: string; username: string; avatar_url: string | null }[]>(
      `/api/v1/users/search?q=${encodeURIComponent(q)}`,
      { headers: dm._authHeaders() }
    )
    searchResults.value = res.filter(u => u.id !== auth.user?.id)
  } finally {
    searching.value = false
  }
}

function selectUser(userId: string) {
  showSearch.value = false
  searchQuery.value = ''
  searchResults.value = []
  emit('select', userId)
}

async function confirmDeleteRoom(scope: 'all' | 'self') {
  const room = deleteConfirmRoom.value
  if (!room) return
  deleteConfirmRoom.value = null
  await dm.deleteRoom(room.id, scope)
}

function formatTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const today = new Date()
  if (d.toDateString() === today.toDateString()) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString([], { day: 'numeric', month: 'short' })
}

function otherUserBadge(room: DirectMessageRoomData) {
  if (!room.other_user_badge_ring_gradient) return null
  return {
    id: '',
    name: room.other_user_badge_name || '',
    icon_svg: room.other_user_badge_icon_svg || '',
    avatar_ring_gradient: room.other_user_badge_ring_gradient,
    avatar_ring_effect: room.other_user_badge_ring_effect || null,
    is_active: true,
    description: null,
  }
}

function isRoomOnline(room: DirectMessageRoomData): boolean {
  const _ = onlineTick.value
  if (!room.other_user_last_seen_at) return false
  return Date.now() - new Date(room.other_user_last_seen_at).getTime() < ONLINE_WINDOW
}
</script>

<template>
  <div class="flex flex-col h-full bg-surface/40 backdrop-blur-xl">
    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-4 shrink-0">
      <h1 class="text-[22px] font-bold text-foreground tracking-tight">Чаты <span class="text-[9px] font-semibold uppercase tracking-widest text-primary align-middle ml-1.5 px-1.5 py-[3px] rounded-md bg-primary/10 leading-none">Beta</span></h1>
      <button
        class="w-8 h-8 rounded-full bg-surface-elevated/80 text-secondary/40 hover:text-primary hover:bg-primary/8 transition-all flex items-center justify-center shadow-sm border border-border/30"
        title="Новый чат"
        @click="showSearch = !showSearch"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
    </div>

    <!-- Search -->
    <Transition name="slide-search">
      <div v-if="showSearch" class="px-4 pb-3">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск пользователей..."
            class="w-full pl-10 pr-9 py-2.5 rounded-xl bg-surface-elevated/80 border border-border/40 text-sm text-foreground placeholder-secondary/40 outline-none transition-all focus:border-primary/30 focus:shadow-[0_0_0_3px_color-mix(in_srgb,var(--color-primary)_10%,transparent)] backdrop-blur-sm"
            @input="searchUsers"
          />
          <svg class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <svg v-if="searching" class="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-secondary/30" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
        <div v-if="searchResults.length > 0" class="mt-2 rounded-xl bg-surface-elevated/90 border border-border/30 overflow-hidden shadow-lg backdrop-blur-xl">
          <button
            v-for="u in searchResults"
            :key="u.id"
            class="w-full flex items-center gap-3 px-3.5 py-3 hover:bg-primary/5 transition-colors text-left"
            @click="selectUser(u.id)"
          >
            <div class="w-9 h-9 rounded-full bg-gradient-to-br from-primary/12 to-primary/5 text-primary flex items-center justify-center text-xs font-medium shrink-0 shadow-sm">
              {{ u.nickname?.charAt(0)?.toUpperCase() || '?' }}
            </div>
            <div class="min-w-0">
              <p class="text-[15px] font-medium text-foreground truncate leading-tight">{{ u.nickname }}</p>
              <p class="text-[12px] text-secondary/40 mt-0.5">@{{ u.username }}</p>
            </div>
          </button>
        </div>
        <p v-else-if="searchQuery && !searching" class="text-xs text-secondary/40 mt-2 px-1">Ничего не найдено</p>
      </div>
    </Transition>

    <!-- Rooms list -->
    <div class="flex-1 overflow-y-auto px-3 py-1 dm-scrollbar">
      <div v-if="dm.loading" class="flex items-center justify-center py-16">
        <div class="w-6 h-6 border-[2.5px] border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>

      <div v-else-if="dm.sortedRooms.length === 0" class="flex flex-col items-center justify-center py-20 text-center px-8">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/8 to-primary/3 text-primary/30 flex items-center justify-center mb-5 shadow-sm">
          <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
        </div>
        <p class="text-[15px] font-semibold text-foreground/50 mb-1.5">Пока нет чатов</p>
        <p class="text-xs text-secondary/40 leading-relaxed max-w-[220px]">Нажмите «+» чтобы найти собеседника и начать разговор</p>
      </div>

      <div v-else class="space-y-[2px]">
        <div
          v-for="room in dm.sortedRooms"
          :key="room.id"
          class="relative flex items-center gap-3 px-3.5 py-3 rounded-2xl cursor-pointer transition-all duration-150 group"
            :class="room.other_user_id === activeUserId
              ? 'bg-primary/8 ring-1 ring-primary/20'
              : 'hover:bg-surface-elevated/60'"
          @click="selectUser(room.other_user_id)"
          @contextmenu.prevent="onContextMenu($event, room)"
        >
          <div class="relative shrink-0">
            <div class="w-[46px] h-[46px] rounded-full bg-gradient-to-br from-primary/10 to-primary/5 text-primary flex items-center justify-center text-sm font-medium overflow-hidden shadow-sm ring-1 ring-black/[0.03]">
              <img v-if="room.other_user_avatar" :src="room.other_user_avatar" class="w-full h-full object-cover" />
              <span v-else>{{ room.other_user_name?.charAt(0)?.toUpperCase() || '?' }}</span>
            </div>
            <span
              v-if="isRoomOnline(room)"
              class="absolute -bottom-[1px] -right-[1px] w-[12px] h-[12px] rounded-full bg-success ring-[2.5px] ring-surface online-dot"
            />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between gap-2">
              <p class="text-[15px] font-semibold truncate flex items-center gap-1 leading-tight" :class="room.unread_count > 0 ? 'text-foreground' : 'text-foreground/80'">
                {{ room.other_user_name }}<UserBadgeIcon v-if="otherUserBadge(room)" :badge="otherUserBadge(room)!" size="sm" />
              </p>
              <span
                class="text-[11px] shrink-0 leading-none font-medium"
                :class="room.unread_count > 0 ? 'text-primary font-semibold' : 'text-secondary/30'"
              >{{ formatTime(room.last_message_at) }}</span>
            </div>
            <div class="flex items-center justify-between gap-2 mt-1">
              <p
                class="text-[13px] truncate flex-1 leading-relaxed"
                :class="room.unread_count > 0 ? 'text-foreground/60 font-medium' : 'text-secondary/45'"
              >{{ room.last_message_content || 'Нет сообщений' }}</p>
              <div
                v-if="room.unread_count > 0"
                class="min-w-[20px] h-[20px] px-1.5 rounded-full bg-primary text-white text-[10px] font-bold flex items-center justify-center shrink-0 leading-none shadow-sm"
              >
                {{ room.unread_count > 99 ? '99+' : room.unread_count }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Context menu -->
  <Teleport to="body">
    <div v-if="contextMenuRoom" class="fixed inset-0 z-[200]" @mousedown.stop="closeContextMenu">
      <div
        class="absolute bg-surface-elevated/95 border border-border/30 rounded-2xl shadow-2xl py-1 min-w-[180px] overflow-hidden backdrop-blur-2xl"
        :style="{ left: contextMenuRoom.x + 'px', top: contextMenuRoom.y + 'px' }"
        @mousedown.stop
      >
        <button
          class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-danger hover:bg-danger/5 transition-colors text-left font-medium"
          @click="deleteConfirmRoom = contextMenuRoom.room; contextMenuRoom = null"
        >
          <svg class="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
          Удалить чат
        </button>
      </div>
    </div>
  </Teleport>

  <!-- Delete room confirmation -->
  <Teleport to="body">
    <div
      v-if="deleteConfirmRoom"
      class="fixed inset-0 z-[300] flex items-center justify-center bg-black/20 backdrop-blur-sm"
      @click="deleteConfirmRoom = null"
    >
      <div class="bg-surface-elevated/95 border border-border/30 rounded-3xl shadow-2xl p-7 max-w-sm w-full mx-4 backdrop-blur-2xl" @click.stop>
        <div class="w-11 h-11 rounded-2xl bg-danger/10 text-danger flex items-center justify-center mb-4">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-foreground mb-2">Удалить чат?</h3>
        <p class="text-[13px] text-secondary/60 mb-6 leading-relaxed">
          Вы можете удалить чат только у себя или у всех. При удалении у всех все файлы будут безвозвратно удалены.
        </p>
        <div class="flex flex-col gap-2.5">
          <button
            class="w-full px-4 py-3 rounded-2xl bg-danger text-white text-[15px] font-medium hover:bg-danger/90 transition-colors shadow-sm"
            @click="confirmDeleteRoom('all')"
          >
            Удалить у всех
          </button>
          <button
            class="w-full px-4 py-3 rounded-2xl bg-surface text-foreground text-[15px] font-medium border border-border/30 hover:bg-surface-elevated transition-colors"
            @click="confirmDeleteRoom('self')"
          >
            Удалить у себя
          </button>
          <button
            class="w-full px-4 py-2.5 rounded-2xl text-secondary/50 text-[13px] hover:text-foreground transition-colors"
            @click="deleteConfirmRoom = null"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.slide-search-enter-active,
.slide-search-leave-active {
  transition: all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.slide-search-enter-from,
.slide-search-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.online-dot {
  animation: online-pulse 2s ease-in-out infinite;
}
@keyframes online-pulse {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-success) 60%, transparent); }
  50% { box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-success) 18%, transparent); }
}

.dm-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--color-text) 8%, transparent) transparent;
}
.dm-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.dm-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.dm-scrollbar::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--color-text) 8%, transparent);
  border-radius: 2px;
}
</style>
