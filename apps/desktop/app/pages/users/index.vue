<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const query = ref('')
const results = ref<UserSearchResult[]>([])
const loading = ref(false)
const searchHistory = ref<UserSearchResult[]>([])

const HISTORY_KEY = 'user_search_history'

interface UserSearchResult {
  id: string
  nickname: string
  username: string
  avatar_url: string | null
  is_following: boolean
  active_badge?: { id: string; name: string; icon_svg: string; is_active: boolean } | null
}

const showResults = computed(() => query.value.trim().length > 0 && !loading.value)
const showNotFound = computed(() => showResults.value && results.value.length === 0)
const showIdle = computed(() => !query.value.trim() && !loading.value && searchHistory.value.length === 0)

onMounted(() => {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (raw) searchHistory.value = JSON.parse(raw)
  } catch {}
})

function saveToHistory(user: UserSearchResult) {
  searchHistory.value = searchHistory.value.filter(u => u.id !== user.id)
  searchHistory.value.unshift(user)
  if (searchHistory.value.length > 10) searchHistory.value = searchHistory.value.slice(0, 10)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value))
}

function clearHistory() {
  searchHistory.value = []
  localStorage.removeItem(HISTORY_KEY)
}

let debounceTimer: ReturnType<typeof setTimeout>
function onSearch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    if (!query.value.trim()) {
      results.value = []
      return
    }
    loading.value = true
    try {
      const res = await useApiFetch<UserSearchResult[]>(
        `/api/v1/users/search?q=${encodeURIComponent(query.value)}`,
        { headers: { Authorization: `Bearer ${auth.accessToken}` } },
      )
      results.value = res
    } catch {
      results.value = []
    } finally {
      loading.value = false
    }
  }, 300)
}

async function toggleFollow(user: UserSearchResult) {
  if (user.is_following) {
    await useApiFetch(`/api/v1/users/${user.username}/follow`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    user.is_following = false
    toast.show(`Отписались от ${user.nickname}`, 'info')
  } else {
    await useApiFetch(`/api/v1/users/${user.username}/follow`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    user.is_following = true
    toast.show(`Подписались на ${user.nickname}`, 'success')
  }
  saveToHistory(user)
}
</script>

<template>
  <div class="page-shell-narrow">
    <div class="mb-8">
      <h1 class="page-title">Пользователи</h1>
      <p class="page-subtitle">Найдите артистов и продюсеров для коллабораций</p>
    </div>

    <UiInput
      v-model="query"
      placeholder="Имя, nickname или @username..."
      class="mb-6"
      @update:model-value="onSearch"
    />

    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="card p-4 animate-pulse flex items-center gap-3">
        <div class="w-11 h-11 rounded-full bg-btn-secondary" />
        <div class="flex-1">
          <div class="h-3 bg-btn-secondary rounded w-1/3" />
          <div class="h-2.5 bg-btn-secondary rounded w-1/4 mt-1.5" />
        </div>
      </div>
    </div>

    <!-- Ничего не найдено -->
    <div v-else-if="showNotFound" class="empty-state">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-surface flex items-center justify-center">
        <svg class="w-8 h-8 text-secondary/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-foreground mb-2">Никого не найдено</h2>
      <p class="text-sm text-secondary max-w-xs mx-auto mb-1">
        По запросу «{{ query.trim() }}» пользователей нет
      </p>
      <p class="text-xs text-secondary">
        Проверьте написание или попробуйте username без @
      </p>
    </div>

    <!-- Подсказка до поиска -->
    <div v-else-if="showIdle" class="empty-state">
      <div
        class="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center"
        style="background-color: color-mix(in srgb, var(--color-primary) 10%, transparent)"
      >
        <svg class="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-foreground mb-2">Найдите коллег</h2>
      <p class="text-sm text-secondary max-w-sm mx-auto">
        Введите имя артиста или @username, чтобы добавить в коллаборацию или подписаться
      </p>
    </div>

    <!-- Недавние -->
    <div v-else-if="!query.trim() && searchHistory.length" class="space-y-2">
      <div class="flex items-center justify-between mb-3">
        <h2 class="section-title !normal-case !tracking-normal text-sm text-foreground">Недавние</h2>
        <button class="text-xs text-secondary hover:text-primary transition-colors" @click="clearHistory">
          Очистить
        </button>
      </div>
      <TransitionGroup name="stagger" tag="div" class="space-y-2">
        <div
          v-for="u in searchHistory"
          :key="u.id"
          class="card card-interactive p-4 flex items-center justify-between"
        >
        <NuxtLink :to="`/profile/${u.username}`" class="flex items-center gap-3 min-w-0 no-underline">
          <UiAvatarRing :src="u.avatar_url" :alt="u.nickname" size="md" :badge="(u as any).active_badge" />
          <div class="min-w-0">
            <p class="text-sm font-medium text-foreground truncate flex items-center gap-1">
              {{ u.nickname }}
              <UserBadgeIcon :badge="(u as any).active_badge" size="sm" />
            </p>
            <p class="text-xs text-secondary">@{{ u.username }}</p>
          </div>
        </NuxtLink>
        <UiButton
          size="sm"
          :variant="u.is_following ? 'secondary' : 'primary'"
          @click="toggleFollow(u)"
        >
          {{ u.is_following ? 'Отписаться' : 'Подписаться' }}
        </UiButton>
      </div>
    </TransitionGroup>
    </div>

    <!-- Результаты -->
    <div v-else class="space-y-2">
      <p class="text-xs text-secondary mb-2">
        Найдено: {{ results.length }}
      </p>
      <TransitionGroup name="stagger" tag="div" class="space-y-2">
        <div
          v-for="u in results"
          :key="u.id"
          class="card card-interactive p-4 flex items-center justify-between"
        >
          <NuxtLink :to="`/profile/${u.username}`" class="flex items-center gap-3 min-w-0 no-underline">
            <UiAvatarRing :src="u.avatar_url" :alt="u.nickname" size="md" :badge="(u as any).active_badge" />
            <div class="min-w-0">
            <p class="text-sm font-medium text-foreground truncate flex items-center gap-1">
              {{ u.nickname }}
              <UserBadgeIcon :badge="(u as any).active_badge" size="sm" />
            </p>
            <p class="text-xs text-secondary">@{{ u.username }}</p>
          </div>
        </NuxtLink>
        <UiButton
            size="sm"
            :variant="u.is_following ? 'secondary' : 'primary'"
            @click="toggleFollow(u)"
          >
            {{ u.is_following ? 'Отписаться' : 'Подписаться' }}
          </UiButton>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>
