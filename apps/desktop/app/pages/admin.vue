<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

definePageMeta({ middleware: 'auth' })
import { formatError } from '~/utils/formatError'

const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const activeTab = ref<'users' | 'dashboard' | 'badges'>('dashboard')

// ── Users tab ──

interface UserAdminItem {
  id: string
  email: string
  nickname: string
  username: string
  avatar_url: string | null
  is_admin: boolean
  storage_limit: number
  storage_used: number
  created_at: string
}

interface StorageSummary {
  total_users: number
  total_used: number
  total_limit: number
}

const users = ref<UserAdminItem[]>([])
const storageSummary = ref<StorageSummary | null>(null)
const loading = ref(false)
const editingLimit = ref<string | null>(null)
const limitInput = ref(5)
const searchQuery = ref('')

const filteredUsers = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return users.value
  return users.value.filter(
    u =>
      u.nickname?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q) ||
      u.username?.toLowerCase().includes(q),
  )
})

async function fetchUsers() {
  loading.value = true
  try {
    const [u, s] = await Promise.all([
      useApiFetch<UserAdminItem[]>('/api/v1/admin/users', {
        headers: auth._authHeaders(),
      }),
      useApiFetch<StorageSummary>('/api/v1/admin/storage', {
        headers: auth._authHeaders(),
      }),
    ])
    users.value = u
    storageSummary.value = s
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    loading.value = false
  }
}

async function setLimit(userId: string) {
  try {
    await useApiFetch(`/api/v1/admin/users/${userId}/storage-limit`, {
      method: 'PATCH',
      headers: auth._authHeaders(),
      body: { storage_limit_gb: limitInput.value },
    })
    toast.show('Лимит обновлён', 'success')
    editingLimit.value = null
    await fetchUsers()
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

const deletingId = ref<string | null>(null)
const confirmDelete = ref<{ id: string; name: string } | null>(null)

async function deleteUser(userId: string) {
  deletingId.value = userId
  confirmDelete.value = null
  try {
    await useApiFetch(`/api/v1/admin/users/${userId}`, {
      method: 'DELETE',
      headers: auth._authHeaders(),
    })
    toast.show('Пользователь удалён', 'success')
    await fetchUsers()
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    deletingId.value = null
  }
}

// ── Badges tab ──

interface BadgeAdminItem {
  id: string
  name: string
  icon_svg: string
  description: string | null
  avatar_ring_gradient: string | null
  avatar_ring_effect: string | null
  created_at: string
}

const badges = ref<BadgeAdminItem[]>([])
const badgesLoading = ref(false)
const newBadgeName = ref('')
const newBadgeSvg = ref('<svg class="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" /></svg>')
const newBadgeDesc = ref('')
const newBadgeGradient = ref('')
const newBadgeEffect = ref('')
const showCreateBadge = ref(false)
const deletingBadgeId = ref<string | null>(null)

// ── Badge editing ──

const editingBadge = ref<BadgeAdminItem | null>(null)
const editBadgeName = ref('')
const editBadgeSvg = ref('')
const editBadgeDesc = ref('')
const editBadgeGradient = ref('')
const editBadgeEffect = ref('')

function openEditBadge(b: BadgeAdminItem) {
  editingBadge.value = b
  editBadgeName.value = b.name
  editBadgeSvg.value = b.icon_svg
  editBadgeDesc.value = b.description || ''
  editBadgeGradient.value = b.avatar_ring_gradient || ''
  editBadgeEffect.value = b.avatar_ring_effect || ''
}

async function saveEditBadge() {
  if (!editingBadge.value) return
  if (!editBadgeName.value.trim()) {
    toast.show('Введите название значка', 'error')
    return
  }
  if (!editBadgeSvg.value.trim()) {
    toast.show('Введите SVG значка', 'error')
    return
  }
  try {
    await useApiFetch(`/api/v1/admin/badges/${editingBadge.value.id}`, {
      method: 'PUT',
      headers: auth._authHeaders(),
      body: {
        name: editBadgeName.value.trim(),
        icon_svg: editBadgeSvg.value.trim(),
        description: editBadgeDesc.value.trim() || null,
        avatar_ring_gradient: editBadgeGradient.value.trim() || null,
        avatar_ring_effect: editBadgeEffect.value.trim() || null,
      },
    })
    toast.show('Значок обновлён', 'success')
    editingBadge.value = null
    await fetchBadgeList()
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

async function fetchBadgeList() {
  badgesLoading.value = true
  try {
    badges.value = await useApiFetch<BadgeAdminItem[]>('/api/v1/admin/badges', {
      headers: auth._authHeaders(),
    })
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    badgesLoading.value = false
  }
}

async function createBadge() {
  if (!newBadgeName.value.trim()) {
    toast.show('Введите название значка', 'error')
    return
  }
  if (!newBadgeSvg.value.trim()) {
    toast.show('Введите SVG значка', 'error')
    return
  }
  try {
    await useApiFetch('/api/v1/admin/badges', {
      method: 'POST',
      headers: auth._authHeaders(),
      body: {
        name: newBadgeName.value.trim(),
        icon_svg: newBadgeSvg.value.trim(),
        description: newBadgeDesc.value.trim() || null,
        avatar_ring_gradient: newBadgeGradient.value.trim() || null,
        avatar_ring_effect: newBadgeEffect.value.trim() || null,
      },
    })
    toast.show('Значок создан', 'success')
    showCreateBadge.value = false
    newBadgeName.value = ''
    newBadgeSvg.value = '<svg class="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" /></svg>'
    newBadgeDesc.value = ''
    newBadgeGradient.value = ''
    newBadgeEffect.value = ''
    await fetchBadgeList()
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

async function deleteBadge(badgeId: string) {
  deletingBadgeId.value = badgeId
  try {
    await useApiFetch(`/api/v1/admin/badges/${badgeId}`, {
      method: 'DELETE',
      headers: auth._authHeaders(),
    })
    toast.show('Значок удалён', 'success')
    await fetchBadgeList()
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    deletingBadgeId.value = null
  }
}

// ── Badge assignment per user ──

const badgeAssignUserId = ref<string | null>(null)
const badgeAssignData = ref<{ badge: BadgeAdminItem; is_active: boolean }[]>([])

async function openBadgeAssign(userId: string) {
  badgeAssignUserId.value = userId
  try {
    const [allBadges, userBadges] = await Promise.all([
      useApiFetch<BadgeAdminItem[]>('/api/v1/admin/badges', { headers: auth._authHeaders() }),
      useApiFetch<{ badge: BadgeAdminItem; is_active: boolean }[]>(`/api/v1/admin/users/${userId}/badges`, { headers: auth._authHeaders() }),
    ])
    badgeAssignData.value = allBadges.map(b => ({
      badge: b,
      is_active: userBadges.some(ub => ub.badge.id === b.id),
    }))
  } catch (e: any) {
    toast.show(formatError(e), 'error')
    badgeAssignUserId.value = null
  }
}

async function toggleBadgeAssign(badgeId: string, currentlyAssigned: boolean) {
  try {
    if (currentlyAssigned) {
      await useApiFetch(`/api/v1/admin/users/${badgeAssignUserId.value}/badges/${badgeId}`, {
        method: 'DELETE',
        headers: auth._authHeaders(),
      })
    } else {
      await useApiFetch(`/api/v1/admin/users/${badgeAssignUserId.value}/badges/${badgeId}`, {
        method: 'POST',
        headers: auth._authHeaders(),
      })
    }
    await openBadgeAssign(badgeAssignUserId.value!)
    toast.show(currentlyAssigned ? 'Значок отозван' : 'Значок выдан', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

// ── Dashboard tab ──

interface DashboardStats {
  total_users: number
  total_projects: number
  total_versions: number
  total_storage_used: number
  total_storage_limit: number
  users_online_5min: number
  users_online_30min: number
  versions_today: number
  projects_today: number
  activity_chart: { date: string; count: number }[]
}

const stats = ref<DashboardStats | null>(null)
const statsLoading = ref(false)
const activityCanvas = ref<HTMLCanvasElement | null>(null)
let activityChart: Chart | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null

async function fetchStats() {
  statsLoading.value = true
  try {
    stats.value = await useApiFetch<DashboardStats>('/api/v1/admin/stats', {
      headers: auth._authHeaders(),
    })
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    statsLoading.value = false
  }
}

function buildActivityChart() {
  if (!activityCanvas.value || !stats.value) return
  if (activityChart) activityChart.destroy()

  const data = stats.value.activity_chart
  activityChart = new Chart(activityCanvas.value, {
    type: 'line',
    data: {
      labels: data.map(d => {
        const parts = d.date.split(/[ :-]/)
        return `${parts[2]}.${parts[1]} ${String(parts[3]).padStart(2, '0')}:00`
      }),
      datasets: [{
        label: 'Действия',
        data: data.map(d => d.count),
        borderColor: 'rgba(59, 130, 246, 0.9)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: 'rgba(59, 130, 246, 0.9)',
        fill: true,
        tension: 0.3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { font: { size: 10 }, maxRotation: 45, autoSkip: true },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: {
            font: { size: 10 },
            stepSize: 1,
          },
          grid: { color: 'rgba(128,128,128,0.08)' },
        },
      },
    },
  })
}

watch(() => stats.value?.activity_chart, () => {
  nextTick(buildActivityChart)
})

onMounted(() => {
  fetchUsers()
  fetchStats()
  pollTimer = setInterval(fetchStats, 10000)
  watch(activeTab, (tab) => {
    if (tab === 'dashboard') {
      fetchStats()
      nextTick(buildActivityChart)
    }
  })
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (activityChart) activityChart.destroy()
})

// ── Helpers ──

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 MB'
  const gb = bytes / 1_073_741_824
  if (gb >= 1) return gb.toFixed(2) + ' GB'
  const mb = bytes / 1_048_576
  return mb.toFixed(1) + ' MB'
}

function usagePercent(used: number, limit: number): number {
  if (limit === 0) return 0
  return Math.round((used / limit) * 100)
}

function formatShortNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}
</script>

<template>
  <div class="max-w-6xl mx-auto p-6">
    <!-- Tab navigation -->
    <div class="flex items-center gap-1 mb-6 p-1 rounded-xl bg-muted-surface w-fit">
      <button
        class="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200"
        :class="activeTab === 'dashboard'
          ? 'bg-surface-elevated text-foreground shadow-sm'
          : 'text-secondary hover:text-foreground'"
        @click="activeTab = 'dashboard'"
      >
        <span class="flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
          Dashboard
        </span>
      </button>
      <button
        class="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200"
        :class="activeTab === 'users'
          ? 'bg-surface-elevated text-foreground shadow-sm'
          : 'text-secondary hover:text-foreground'"
        @click="activeTab = 'users'"
      >
        <span class="flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
          </svg>
          Пользователи
        </span>
      </button>
      <button
        class="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200"
        :class="activeTab === 'badges'
          ? 'bg-surface-elevated text-foreground shadow-sm'
          : 'text-secondary hover:text-foreground'"
        @click="activeTab = 'badges'; fetchBadgeList()"
      >
        <span class="flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
          </svg>
          Значки
        </span>
      </button>
    </div>

    <!-- ═══════════════════ Users Tab ═══════════════════ -->
    <template v-if="activeTab === 'users'">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-xl font-bold">Пользователи</h1>
        <button
          class="text-sm text-primary hover:text-primary/80 transition-colors"
          @click="fetchUsers"
        >
          Обновить
        </button>
      </div>

      <div v-if="storageSummary" class="card p-5 mb-6 flex items-center gap-8">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold tabular-nums">{{ formatBytes(storageSummary.total_used) }}</p>
            <p class="text-xs text-secondary">Занято</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold tabular-nums">{{ formatBytes(storageSummary.total_limit) }}</p>
            <p class="text-xs text-secondary">Лимит</p>
          </div>
        </div>
        <div class="flex-1">
          <div class="flex items-center justify-between text-xs text-secondary mb-1.5">
            <span>{{ formatBytes(storageSummary.total_used) }} / {{ formatBytes(storageSummary.total_limit) }}</span>
            <span>{{ Math.round((storageSummary.total_used / Math.max(storageSummary.total_limit, 1)) * 100) }}%</span>
          </div>
          <div class="h-2 rounded-full bg-btn-secondary overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="(storageSummary.total_used / Math.max(storageSummary.total_limit, 1)) > 0.9 ? 'bg-red-500' : 'bg-primary'"
              :style="{ width: Math.min(100, Math.round((storageSummary.total_used / Math.max(storageSummary.total_limit, 1)) * 100)) + '%' }"
            />
          </div>
          <p class="text-[11px] text-secondary mt-1">{{ storageSummary.total_users }} {{ storageSummary.total_users === 1 ? 'пользователь' : 'пользователей' }}</p>
        </div>
      </div>

      <!-- Search -->
      <div class="relative mb-4">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Поиск по имени, email или username..."
          class="w-full pl-10 pr-4 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground placeholder-secondary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
        />
      </div>

      <div v-if="loading" class="text-center py-12 text-secondary">Загрузка...</div>

      <div v-else class="space-y-3">
        <div
          v-for="user in filteredUsers"
          :key="user.id"
          class="card p-4 flex items-center gap-4"
        >
          <div class="shrink-0 w-10 h-10 rounded-full bg-btn-secondary flex items-center justify-center text-sm font-medium">
            {{ user.nickname?.slice(0, 2)?.toUpperCase() || '?' }}
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="font-medium text-sm truncate flex items-center gap-1">{{ user.nickname }}<UserBadgeIcon :badge="(user as any).active_badge" size="sm" /></span>
              <span class="text-xs text-secondary truncate">{{ user.email }}</span>
              <span
                v-if="user.is_admin"
                class="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-medium shrink-0"
              >admin</span>
            </div>

            <div class="mt-2">
              <div class="flex items-center justify-between text-xs text-secondary mb-1">
                <span>{{ formatBytes(user.storage_used) }} / {{ formatBytes(user.storage_limit) }}</span>
                <span>{{ usagePercent(user.storage_used, user.storage_limit) }}%</span>
              </div>
              <div class="h-1.5 rounded-full bg-btn-secondary overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :class="usagePercent(user.storage_used, user.storage_limit) > 90 ? 'bg-red-500' : 'bg-primary'"
                  :style="{ width: usagePercent(user.storage_used, user.storage_limit) + '%' }"
                />
              </div>
            </div>
          </div>

          <div class="shrink-0 flex items-center gap-2">
            <template v-if="editingLimit === user.id">
              <div class="flex items-center gap-2">
                <input
                  v-model.number="limitInput"
                  type="number"
                  min="1"
                  class="w-20 px-2 py-1 text-sm rounded-lg bg-surface-elevated border border-input-border text-center"
                />
                <span class="text-xs text-secondary">GB</span>
                <button
                  class="text-xs px-2 py-1 rounded-lg bg-primary text-white font-medium"
                  @click="setLimit(user.id)"
                >OK</button>
                <button
                  class="text-xs px-2 py-1 rounded-lg text-secondary hover:bg-btn-secondary"
                  @click="editingLimit = null"
                >Отмена</button>
              </div>
            </template>
            <button
              v-else
              class="text-xs px-3 py-1.5 rounded-lg border border-input-border text-secondary hover:bg-btn-secondary transition-colors"
              @click="editingLimit = user.id; limitInput = Math.round(user.storage_limit / 1_073_741_824)"
            >
              Лимит {{ Math.round(user.storage_limit / 1_073_741_824) }} GB
            </button>
            <button
                class="text-xs px-3 py-1.5 rounded-lg border border-input-border text-secondary hover:bg-btn-secondary transition-colors"
                @click="openBadgeAssign(user.id)"
              >
                Значки
              </button>
              <button
                class="text-xs px-3 py-1.5 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors"
                :disabled="deletingId === user.id"
                @click="confirmDelete = { id: user.id, name: user.nickname || user.email }"
              >
                {{ deletingId === user.id ? '...' : 'Удалить' }}
              </button>
            </div>
          </div>
          <div v-if="!loading && filteredUsers.length === 0 && searchQuery" class="text-center py-12 text-secondary">
            Ничего не найдено
          </div>
        </div>
      </template>

    <!-- ═══════════════════ Badges Tab ═══════════════════ -->
    <template v-if="activeTab === 'badges'">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-xl font-bold">Значки</h1>
        <button
          class="text-sm text-primary hover:text-primary/80 transition-colors"
          @click="showCreateBadge = !showCreateBadge"
        >
          {{ showCreateBadge ? 'Отмена' : '+ Создать' }}
        </button>
      </div>

      <!-- Create form -->
      <div v-if="showCreateBadge" class="card p-5 mb-6 space-y-4">
        <h2 class="text-sm font-semibold">Новый значок</h2>
        <div>
          <label class="block text-xs text-secondary mb-1">Название</label>
          <input v-model="newBadgeName" type="text" placeholder="F11" class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20" />
        </div>
        <div>
          <label class="block text-xs text-secondary mb-1">SVG-иконка (вставьте полный SVG-код)</label>
          <textarea v-model="newBadgeSvg" rows="3" placeholder='<svg ...>' class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 font-mono" />
          <div class="mt-2 flex items-center gap-2 text-xs text-secondary">
            <span>Предпросмотр:</span>
            <span class="w-6 h-6 inline-flex items-center justify-center" v-html="newBadgeSvg" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-secondary mb-1">Описание (необязательно)</label>
          <input v-model="newBadgeDesc" type="text" placeholder="Награда за..." class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20" />
        </div>
        <div>
          <label class="block text-xs text-secondary mb-1">Градиент обводки аватара (CSS gradient, необязательно)</label>
          <input v-model="newBadgeGradient" type="text" placeholder="conic-gradient(from 0deg, #3b82f6, #8b5cf6)" class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 font-mono" />
        </div>
        <div>
          <label class="block text-xs text-secondary mb-1">Эффект обводки (glow / pulse, необязательно)</label>
          <input v-model="newBadgeEffect" type="text" placeholder="glow" class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20" />
        </div>
        <UiButton @click="createBadge">Создать</UiButton>
      </div>

      <div v-if="badgesLoading" class="text-center py-12 text-secondary">Загрузка...</div>

      <div v-else class="space-y-3">
        <div
          v-for="b in badges"
          :key="b.id"
          class="card p-4 flex items-center gap-4"
        >
          <div class="w-8 h-8 rounded-lg bg-btn-secondary flex items-center justify-center" v-html="b.icon_svg" />
          <div class="min-w-0 flex-1">
            <p class="font-medium text-sm">{{ b.name }}</p>
            <p v-if="b.description" class="text-xs text-secondary">{{ b.description }}</p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button
              class="text-xs px-3 py-1.5 rounded-lg border border-border text-secondary hover:bg-surface-elevated transition-colors"
              @click="openEditBadge(b)"
            >
              Изменить
            </button>
            <button
              class="text-xs px-3 py-1.5 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-50"
              :disabled="deletingBadgeId === b.id"
              @click="deleteBadge(b.id)"
            >
              {{ deletingBadgeId === b.id ? '...' : 'Удалить' }}
            </button>
          </div>
        </div>
        <div v-if="!badgesLoading && badges.length === 0" class="text-center py-12 text-secondary">
          Нет значков. Создайте первый!
        </div>
      </div>

      <!-- Edit modal -->
      <UiModal v-if="editingBadge" :model-value="true" @update:model-value="editingBadge = null">
        <div class="space-y-4">
          <h2 class="text-base font-semibold">Изменить значок</h2>
          <div>
            <label class="block text-xs text-secondary mb-1">Название</label>
            <input v-model="editBadgeName" type="text" class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20" />
          </div>
          <div>
            <label class="block text-xs text-secondary mb-1">SVG-иконка</label>
            <textarea v-model="editBadgeSvg" rows="3" class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 font-mono" />
            <div class="mt-2 flex items-center gap-2 text-xs text-secondary">
              <span>Предпросмотр:</span>
              <span class="w-6 h-6 inline-flex items-center justify-center" v-html="editBadgeSvg" />
            </div>
          </div>
          <div>
            <label class="block text-xs text-secondary mb-1">Описание</label>
            <input v-model="editBadgeDesc" type="text" class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20" />
          </div>
          <div>
            <label class="block text-xs text-secondary mb-1">Градиент обводки аватара</label>
            <input v-model="editBadgeGradient" type="text" class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 font-mono" />
          </div>
          <div>
            <label class="block text-xs text-secondary mb-1">Эффект обводки (glow / pulse / spin)</label>
            <input v-model="editBadgeEffect" type="text" class="w-full px-3 py-2 text-sm rounded-xl bg-surface-elevated border border-input-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20" />
          </div>
          <div class="flex justify-end gap-2">
            <UiButton variant="secondary" @click="editingBadge = null">Отмена</UiButton>
            <UiButton @click="saveEditBadge">Сохранить</UiButton>
          </div>
        </div>
      </UiModal>
    </template>

    <!-- ═══════════════════ Dashboard Tab ═══════════════════ -->
    <template v-if="activeTab === 'dashboard'">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-xl font-bold">Dashboard</h1>
        <div class="flex items-center gap-2">
          <span class="text-xs text-secondary">Автообновление каждые 10с</span>
          <button
            class="text-sm text-primary hover:text-primary/80 transition-colors"
            @click="fetchStats"
          >
            Обновить
          </button>
        </div>
      </div>

      <template v-if="statsLoading && !stats">
        <div class="text-center py-12 text-secondary">Загрузка...</div>
      </template>

      <template v-if="stats">
        <!-- Stat cards row -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          <div class="card p-4">
            <p class="text-xs text-secondary mb-1">Пользователи</p>
            <p class="text-2xl font-bold tabular-nums">{{ formatShortNumber(stats.total_users) }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-secondary mb-1">Проекты</p>
            <p class="text-2xl font-bold tabular-nums">{{ formatShortNumber(stats.total_projects) }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-secondary mb-1">Версии</p>
            <p class="text-2xl font-bold tabular-nums">{{ formatShortNumber(stats.total_versions) }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-secondary mb-1">Хранилище</p>
            <p class="text-2xl font-bold tabular-nums">{{ formatBytes(stats.total_storage_used) }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-secondary mb-1">Онлайн (5 мин)</p>
            <p class="text-2xl font-bold tabular-nums text-emerald-500">{{ stats.users_online_5min }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-secondary mb-1">Онлайн (30 мин)</p>
            <p class="text-2xl font-bold tabular-nums text-amber-500">{{ stats.users_online_30min }}</p>
          </div>
        </div>

        <!-- Today stats -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          <div class="card p-4 flex items-center gap-4">
            <div class="shrink-0 w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.41a2.25 2.25 0 013.182 0l2.909 2.91m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
              </svg>
            </div>
            <div>
              <p class="text-xs text-secondary">Проектов за 24ч</p>
              <p class="text-xl font-bold tabular-nums">{{ stats.projects_today }}</p>
            </div>
          </div>
          <div class="card p-4 flex items-center gap-4">
            <div class="shrink-0 w-12 h-12 rounded-xl bg-violet-500/10 flex items-center justify-center">
              <svg class="w-6 h-6 text-violet-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <div>
              <p class="text-xs text-secondary">Версий за 24ч</p>
              <p class="text-xl font-bold tabular-nums">{{ stats.versions_today }}</p>
            </div>
          </div>
        </div>

        <!-- Activity chart -->
        <div class="card p-5 mb-6">
          <h2 class="text-sm font-semibold mb-4">Активность за 24 часа</h2>
          <div class="h-48">
            <canvas ref="activityCanvas" />
          </div>
          <p v-if="stats.activity_chart.length === 0" class="text-xs text-secondary text-center py-8">
            Нет данных за последние 24 часа
          </p>
        </div>

        <!-- Storage card -->
        <div class="card p-5">
          <h2 class="text-sm font-semibold mb-3">Хранилище</h2>
          <div class="flex items-center justify-between text-xs text-secondary mb-1.5">
            <span>{{ formatBytes(stats.total_storage_used) }} / {{ formatBytes(stats.total_storage_limit) }}</span>
            <span>{{ Math.round((stats.total_storage_used / Math.max(stats.total_storage_limit, 1)) * 100) }}%</span>
          </div>
          <div class="h-3 rounded-full bg-btn-secondary overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="(stats.total_storage_used / Math.max(stats.total_storage_limit, 1)) > 0.9 ? 'bg-red-500' : 'bg-primary'"
              :style="{ width: Math.min(100, Math.round((stats.total_storage_used / Math.max(stats.total_storage_limit, 1)) * 100)) + '%' }"
            />
          </div>
        </div>
      </template>
    </template>
  </div>

  <!-- Confirm delete modal -->
  <Teleport to="body">
    <div
      v-if="confirmDelete"
      class="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="confirmDelete = null"
    >
      <div class="bg-surface-elevated rounded-2xl shadow-2xl p-6 max-w-sm w-full mx-4 border border-border/50">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <div>
            <h3 class="text-sm font-semibold">Удалить пользователя</h3>
            <p class="text-xs text-secondary mt-0.5">Это действие необратимо</p>
          </div>
        </div>
        <p class="text-sm text-foreground/80 mb-6">
          Вы уверены, что хотите удалить <strong>{{ confirmDelete.name }}</strong>? Все данные пользователя будут безвозвратно удалены.
        </p>
        <div class="flex justify-end gap-2">
          <button
            class="px-4 py-2 text-sm font-medium rounded-xl text-secondary hover:bg-hover transition-colors"
            @click="confirmDelete = null"
          >
            Отмена
          </button>
          <button
            class="px-4 py-2 text-sm font-medium rounded-xl bg-red-500 text-white hover:bg-red-600 transition-colors disabled:opacity-50"
            :disabled="deletingId === confirmDelete.id"
            @click="deleteUser(confirmDelete.id)"
          >
            {{ deletingId === confirmDelete?.id ? 'Удаление...' : 'Удалить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Badge assignment modal -->
    <div
      v-if="badgeAssignUserId"
      class="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="badgeAssignUserId = null"
    >
      <div class="bg-surface-elevated rounded-2xl shadow-2xl p-6 max-w-md w-full mx-4 border border-border/50">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold">Управление значками</h3>
          <button
            class="text-secondary hover:text-foreground p-1 rounded-lg hover:bg-hover transition-colors"
            @click="badgeAssignUserId = null"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-2">
          <div
            v-for="item in badgeAssignData"
            :key="item.badge.id"
            class="flex items-center justify-between p-3 rounded-xl bg-hover"
          >
            <div class="flex items-center gap-3">
              <span class="w-6 h-6 inline-flex items-center justify-center" v-html="item.badge.icon_svg" />
              <span class="text-sm font-medium">{{ item.badge.name }}</span>
            </div>
            <button
              class="text-xs px-3 py-1.5 rounded-lg transition-colors"
              :class="item.is_active
                ? 'bg-danger/10 text-danger hover:bg-danger/20'
                : 'bg-primary/10 text-primary hover:bg-primary/20'"
              @click="toggleBadgeAssign(item.badge.id, item.is_active)"
            >
              {{ item.is_active ? 'Отозвать' : 'Выдать' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
