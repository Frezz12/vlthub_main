import { defineStore } from 'pinia'
import type { NotificationOut, NotificationListOut } from '@pjasaver/shared-types'

interface NotificationsState {
  items: NotificationOut[]
  total: number
  unreadCount: number
  loading: boolean
}

export const useNotificationsStore = defineStore('notifications', {
  state: (): NotificationsState => ({
    items: [],
    total: 0,
    unreadCount: 0,
    loading: false,
  }),

  getters: {
    notificationList: (state) => state.items,
    hasUnread: (state) => state.unreadCount > 0,
  },

  actions: {
    _authHeaders(): Record<string, string> {
      const auth = useAuthStore()
      if (!auth.accessToken) return {}
      return { Authorization: `Bearer ${auth.accessToken}` }
    },

    async fetchNotifications(page = 1, limit = 20) {
      this.loading = true
      try {
        const res = await useApiFetch<NotificationListOut>(
          `/api/v1/notifications?page=${page}&limit=${limit}`,
          { headers: this._authHeaders() },
        )
        this.items = res.items
        this.total = res.total
        this.unreadCount = res.unread_count
      } finally {
        this.loading = false
      }
    },

    async markRead(id: string) {
      await useApiFetch(`/api/v1/notifications/${id}/read`, { method: 'PATCH', headers: this._authHeaders() })
      const n = this.items.find((n) => n.id === id)
      if (n) {
        n.is_read = true
        this.unreadCount = Math.max(0, this.unreadCount - 1)
      }
    },

    async markAllRead() {
      await useApiFetch('/api/v1/notifications/read-all', { method: 'PATCH', headers: this._authHeaders() })
      this.items.forEach((n) => (n.is_read = true))
      this.unreadCount = 0
    },
  },
})
