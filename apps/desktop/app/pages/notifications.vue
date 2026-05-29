<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
import { formatError } from '~/utils/formatError'

const notifications = useNotificationsStore()
const projectsStore = useProjectsStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

onMounted(async () => {
  await notifications.fetchNotifications()
})

async function handleApprove(n: { id: string; related_project_id: string | null; related_user_id: string | null }) {
  if (!n.related_project_id || !n.related_user_id) return
  try {
    await projectsStore.resolveAccessRequest(n.related_project_id, n.related_user_id, 'approve')
    await notifications.markRead(n.id)
    toast.show('Доступ предоставлен', 'success')
    notifications.fetchNotifications()
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

async function handleDeny(n: { id: string; related_project_id: string | null; related_user_id: string | null }) {
  if (!n.related_project_id || !n.related_user_id) return
  try {
    await projectsStore.resolveAccessRequest(n.related_project_id, n.related_user_id, 'deny')
    await notifications.markRead(n.id)
    toast.show('Запрос отклонён', 'info')
    notifications.fetchNotifications()
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}
</script>

<template>
  <div class="page-shell-narrow">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="page-title">Уведомления</h1>
        <p class="page-subtitle">События по проектам и подпискам</p>
      </div>
      <UiButton
        v-if="notifications.items.length"
        variant="ghost"
        size="sm"
        @click="notifications.markAllRead()"
      >
        Прочитать все
      </UiButton>
    </div>

    <div v-if="notifications.loading" class="space-y-2">
      <div v-for="i in 5" :key="i" class="card p-4 animate-pulse">
        <div class="h-4 bg-btn-secondary rounded w-3/4" />
      </div>
    </div>

    <div v-else-if="notifications.items.length === 0" class="empty-state">
      <svg class="w-12 h-12 mx-auto text-secondary/40 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
        <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
      </svg>
      <p class="text-sm text-secondary">Нет уведомлений</p>
    </div>

    <TransitionGroup v-else name="stagger" tag="div" class="space-y-2">
      <div
        v-for="n in notifications.items"
        :key="n.id"
        class="card p-4 transition-all duration-200"
        :class="{ 'ring-2 ring-primary/20 border-primary/20': !n.is_read }"
      >
        <div class="flex items-start gap-3">
          <!-- Icon -->
          <div class="shrink-0 mt-0.5">
            <div
              v-if="n.type === 'new_follower'"
              class="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center"
            >
              <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM4 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 0110.374 21c-2.331 0-4.512-.645-6.374-1.766z" />
              </svg>
            </div>
            <div
              v-else-if="n.type === 'access_request'"
              class="w-9 h-9 rounded-full bg-warning/10 flex items-center justify-center"
            >
              <svg class="w-4 h-4 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m0 0v2m0-2h2m-2 0H10m9.364-7.364A9 9 0 1112 3a9 9 0 017.364 4.636z" />
              </svg>
            </div>
            <div
              v-else-if="n.type === 'access_granted'"
              class="w-9 h-9 rounded-full bg-success/10 flex items-center justify-center"
            >
              <svg class="w-4 h-4 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div
              v-else-if="n.type === 'access_denied'"
              class="w-9 h-9 rounded-full bg-danger/10 flex items-center justify-center"
            >
              <svg class="w-4 h-4 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div
              v-else-if="n.type === 'setup_pin'"
              class="w-9 h-9 rounded-full bg-warning/10 flex items-center justify-center"
            >
              <svg class="w-4 h-4 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <div
              v-else
              class="w-9 h-9 rounded-full bg-btn-secondary flex items-center justify-center"
            >
              <svg class="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
              </svg>
            </div>
          </div>

          <div class="min-w-0 flex-1">
            <p class="text-sm" :class="{ 'font-medium': !n.is_read }">{{ n.message }}</p>
            <p class="text-xs text-secondary mt-1">{{ new Date(n.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }) }}</p>

            <!-- Access request actions -->
            <div v-if="n.type === 'access_request' && !n.is_read" class="flex items-center gap-2 mt-3">
              <UiButton size="xs" @click="handleApprove(n)">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Принять
              </UiButton>
              <UiButton size="xs" variant="secondary" @click="handleDeny(n)">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                Отклонить
              </UiButton>
            </div>
          </div>

          <!-- Read indicator -->
          <button
            v-if="!n.is_read"
            class="shrink-0 p-1 text-secondary hover:text-primary transition-colors"
            title="Отметить прочитанным"
            @click="notifications.markRead(n.id)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>
