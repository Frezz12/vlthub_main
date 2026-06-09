<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const dm = useDMStore()

const updateState = useState('updateState', () => 'idle')
const updateVersion = useState('updateVersion', () => '')
const showUpdateModal = useState('showUpdateModal', () => false)

function openUpdate() {
  showUpdateModal.value = true
}

let heartbeatTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  dm.fetchRooms()
  dm.heartbeat()
  heartbeatTimer = setInterval(() => {
    if (document.visibilityState === 'visible') dm.heartbeat()
  }, 60000)
})

onUnmounted(() => {
  if (heartbeatTimer) clearInterval(heartbeatTimer)
})

watch(() => route.path, () => {
  dm.fetchRooms()
})

const isCollapsed = useState('sidebarCollapsed', () => true)
const isHovered = useState('sidebarHovered', () => false)

const isExpanded = computed(() => !isCollapsed.value || isHovered.value)

function onMouseEnter() {
  isHovered.value = true
}

function onMouseLeave() {
  isHovered.value = false
}

const navItems = computed(() => [
  { label: 'Профиль', icon: 'person', to: auth.user?.username ? `/profile/${auth.user.username}` : '/settings' },
  { label: 'Проекты', icon: 'folder', to: '/' },
  { label: 'Чаты', icon: 'chat', to: '/messages' },
  { label: 'Пользователи', icon: 'users', to: '/users' },
])

const adminItems = computed(() => {
  if (!auth.user?.is_admin) return []
  return [{ label: 'Админ', icon: 'shield', to: '/admin' }]
})

const settingsItems = [
  { label: 'Настройки', icon: 'settings', to: '/settings' },
]

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <aside
    class="fixed left-0 top-14 bottom-0 z-30 flex flex-col overflow-hidden transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)] bg-surface-elevated border-r border-separator"
    :class="isExpanded ? 'w-56' : 'w-16'"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
  >
    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto px-2.5 py-3 space-y-0.5">
      <NuxtLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-link overflow-hidden"
        :class="[
          isActive(item.to) ? 'nav-link-active' : 'nav-link-inactive',
          !isExpanded ? 'justify-center px-0' : '',
        ]"
      >
        <!-- Active indicator bar -->
        <span
          v-if="isActive(item.to) && isExpanded"
          class="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-primary"
        />

        <!-- Icon -->
        <span
          class="relative flex items-center justify-center w-5 h-5 shrink-0"
          :class="isActive(item.to) ? 'text-primary' : ''"
        >
          <svg v-if="item.icon === 'folder'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" />
          </svg>
          <svg v-else-if="item.icon === 'person'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
          <svg v-else-if="item.icon === 'users'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
          </svg>
          <svg v-else-if="item.icon === 'chat'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
          <span
            v-if="item.icon === 'chat' && dm.unreadCount > 0"
            class="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-primary text-white text-[10px] font-bold flex items-center justify-center leading-none"
          >
            {{ dm.unreadCount > 99 ? '99+' : dm.unreadCount }}
          </span>
        </span>

        <Transition name="sidebar-fade">
          <span v-if="isExpanded" class="relative whitespace-nowrap">
            {{ item.label }}
            <span v-if="item.label === 'Чаты'" class="text-[8px] font-bold uppercase tracking-wider text-primary align-middle ml-1 px-1 py-0.5 rounded-md bg-primary/10 leading-none">Beta</span>
          </span>
        </Transition>
      </NuxtLink>

      <!-- Admin section -->
      <template v-if="adminItems.length">
        <Transition name="sidebar-fade">
          <div v-if="isExpanded" class="pt-4 pb-1 px-3">
            <span class="text-[10px] font-bold text-secondary tracking-[0.08em] uppercase select-none">Управление</span>
          </div>
        </Transition>

        <NuxtLink
          v-for="item in adminItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="[
            isActive(item.to) ? 'nav-link-active' : 'nav-link-inactive',
            !isExpanded ? 'justify-center px-0' : '',
          ]"
        >
          <span
            v-if="isActive(item.to) && isExpanded"
            class="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-primary"
          />
          <span class="flex items-center justify-center w-5 h-5 shrink-0" :class="isActive(item.to) ? 'text-primary' : ''">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </span>
          <Transition name="sidebar-fade">
            <span v-if="isExpanded" class="whitespace-nowrap">{{ item.label }}</span>
          </Transition>
        </NuxtLink>
      </template>

      <!-- Settings section divider -->
      <Transition name="sidebar-fade">
        <div v-if="isExpanded" class="pt-4 pb-1 px-3">
          <span class="text-[10px] font-bold text-secondary tracking-[0.08em] uppercase select-none">Система</span>
        </div>
      </Transition>

      <NuxtLink
        v-for="item in settingsItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
        :class="[
          isActive(item.to) ? 'nav-link-active' : 'nav-link-inactive',
          !isExpanded ? 'justify-center px-0' : '',
        ]"
      >
        <!-- Active indicator bar -->
        <span
          v-if="isActive(item.to) && isExpanded"
          class="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-primary"
        />

        <span
          class="flex items-center justify-center w-5 h-5 shrink-0"
          :class="isActive(item.to) ? 'text-primary' : ''"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </span>

        <Transition name="sidebar-fade">
          <span v-if="isExpanded" class="whitespace-nowrap">{{ item.label }}</span>
        </Transition>
      </NuxtLink>
    </nav>

    <!-- Update available button -->
    <Transition name="sidebar-fade">
      <button
        v-if="updateState === 'available'"
        class="mx-2.5 mb-1 flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-primary text-white text-sm font-medium transition-all duration-200 hover:bg-primary/90 active:scale-[0.97] shadow-sm"
        :class="!isExpanded ? 'justify-center px-0 mx-1' : ''"
        @click="openUpdate"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        <Transition name="sidebar-fade">
          <span v-if="isExpanded" class="whitespace-nowrap">Обновить до {{ updateVersion }}</span>
        </Transition>
      </button>
    </Transition>

    <!-- User section -->
    <div
      v-if="auth.isAuthenticated"
      class="border-t border-separator p-2.5 space-y-1"
    >
      <div
        class="group relative flex items-center gap-2.5 px-2.5 py-2 rounded-xl transition-all duration-200 hover:bg-hover"
        :class="!isExpanded ? 'justify-center' : ''"
      >
        <template v-if="auth.user?.username">
          <NuxtLink :to="`/profile/${auth.user.username}`" class="shrink-0 no-underline">
            <UiAvatarRing :src="auth.user?.avatar_url" :alt="auth.user?.nickname" size="sm" :badge="auth.user?.active_badge" />
          </NuxtLink>
          <Transition name="sidebar-fade">
            <div v-if="isExpanded" class="min-w-0 flex-1">
              <NuxtLink :to="`/profile/${auth.user.username}`" class="no-underline">
                <p class="text-sm font-medium truncate text-foreground hover:text-primary transition-colors flex items-center gap-1">
                  {{ auth.user?.nickname }}
                  <UserBadgeIcon :badge="auth.user?.active_badge" size="sm" />
                </p>
              </NuxtLink>
              <p class="text-[11px] text-secondary truncate">{{ auth.user?.email }}</p>
            </div>
          </Transition>
        </template>
        <template v-else>
          <div class="shrink-0">
            <UiAvatarRing :src="auth.user?.avatar_url" :alt="auth.user?.nickname" size="sm" :badge="auth.user?.active_badge" />
          </div>
          <Transition name="sidebar-fade">
            <div v-if="isExpanded" class="min-w-0 flex-1">
              <p class="text-sm font-medium truncate text-foreground flex items-center gap-1">{{ auth.user?.nickname || 'Пользователь' }}<UserBadgeIcon :badge="auth.user?.active_badge" size="sm" /></p>
              <p class="text-[11px] text-secondary truncate">{{ auth.user?.email }}</p>
            </div>
          </Transition>
        </template>
        <NuxtLink
          v-if="isExpanded"
          to="/settings"
          class="shrink-0 p-1.5 rounded-lg text-secondary opacity-0 group-hover:opacity-100 hover:text-primary hover:bg-hover transition-all duration-200 no-underline"
          title="Настройки"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </NuxtLink>
      </div>
    </div>
  </aside>
</template>
