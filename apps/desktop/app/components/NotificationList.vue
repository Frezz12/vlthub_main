<script setup lang="ts">
const notifications = useNotificationsStore()

onMounted(() => {
  notifications.fetchNotifications()
})
</script>

<template>
  <div class="max-h-96 overflow-y-auto">
    <div v-if="notifications.loading" class="p-4 text-sm text-secondary text-center">
      Загрузка...
    </div>

    <div v-else-if="notifications.items.length === 0" class="p-4 text-sm text-secondary text-center">
      Нет уведомлений
    </div>

    <div v-else class="divide-y divide-separator">
      <div
        v-for="n in notifications.items.slice(0, 10)"
        :key="n.id"
        class="px-4 py-3 text-sm cursor-pointer hover:bg-btn-secondary/30 transition-colors flex items-start gap-3"
        :class="{ 'bg-primary/5 font-medium': !n.is_read }"
        @click="notifications.markRead(n.id)"
      >
        <div v-if="n.type === 'new_follower'" class="shrink-0">
          <div class="w-8 h-8 rounded-full bg-btn-secondary flex items-center justify-center text-xs font-medium">
            {{ n.related_user_id ? '👤' : '' }}
          </div>
        </div>
        <div class="min-w-0 flex-1">
          {{ n.message }}
          <p class="text-xs text-secondary mt-0.5">{{ new Date(n.created_at).toLocaleDateString() }}</p>
        </div>
      </div>

      <NuxtLink
        to="/notifications"
        class="block px-4 py-3 text-sm text-primary text-center hover:bg-btn-secondary/30"
      >
        Все уведомления
      </NuxtLink>
    </div>
  </div>
</template>
