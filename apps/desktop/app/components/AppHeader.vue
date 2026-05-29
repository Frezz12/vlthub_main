<script setup lang="ts">
const auth = useAuthStore()
const notifications = useNotificationsStore()
const { isDark, toggle } = useTheme()

let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (auth.isAuthenticated) {
    notifications.fetchNotifications()
    pollTimer = setInterval(() => {
      notifications.fetchNotifications()
    }, 30000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-40 h-14 px-4 sm:px-6 flex items-center justify-between glass"
  >
    <div class="flex items-center gap-2">
      <NuxtLink to="/" class="no-underline group">
        <AppLogo />
      </NuxtLink>
    </div>

    <div class="flex items-center gap-1">
      <button
        type="button"
        class="p-2 rounded-xl text-secondary hover:text-foreground hover:bg-hover transition-colors"
        :title="isDark ? 'Светлая тема' : 'Тёмная тема'"
        @click="toggle"
      >
        <svg v-if="isDark" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1.5m0 15V21m9-9h-1.5m-15 0H3m15.364 6.364l-1.06-1.06M6.697 6.697L5.636 5.636m12.728 0l-1.06 1.06M6.697 17.303l-1.061 1.061M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
        </svg>
      </button>

      <NuxtLink
        to="/notifications"
        class="p-2 rounded-xl text-secondary hover:text-foreground hover:bg-hover transition-colors relative no-underline"
        title="Уведомления"
      >
        <svg class="w-5 h-5" :class="{ 'animate-bounce text-primary': notifications.hasUnread }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        <span
          v-if="notifications.hasUnread"
          class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 bg-danger text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-[var(--color-avatar-ring)] shadow-sm"
        >{{ notifications.unreadCount > 99 ? '99+' : notifications.unreadCount }}</span>
      </NuxtLink>

      <div v-if="auth.isAuthenticated" class="flex items-center gap-1 ml-2">
        <NuxtLink
          v-if="auth.user?.username"
          :to="`/profile/${auth.user.username}`"
          class="flex items-center p-0.5 rounded-full ring-spin-on-hover transition-all no-underline"
        >
          <UiAvatarRing :src="auth.user?.avatar_url" :alt="auth.user?.nickname" size="sm" :badge="auth.user?.active_badge" shadow="" />
        </NuxtLink>
        <div v-else class="p-0.5">
          <UiAvatarRing :src="auth.user?.avatar_url" :alt="auth.user?.nickname" size="sm" :badge="auth.user?.active_badge" shadow="" />
        </div>

      </div>
    </div>
  </header>
</template>
