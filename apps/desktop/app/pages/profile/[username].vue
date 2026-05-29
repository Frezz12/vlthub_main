<script setup lang="ts">
import type { FollowOut, UserProfileOut } from '@pjasaver/shared-types'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const auth = useAuthStore()
const { getDawName, getDawColor } = useDawIcon()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }
const { openExternal } = useExternalLink()

const profile = ref<UserProfileOut | null>(null)
const loading = ref(true)
const activeTab = ref<'overview' | 'projects'>('overview')

const followersModal = ref(false)
const followingModal = ref(false)
const followersList = ref<FollowOut[]>([])
const followingList = ref<FollowOut[]>([])
const listLoading = ref(false)

const isOwnProfile = computed(() => profile.value?.id === auth.user?.id)

const memberSince = computed(() => {
  if (!profile.value?.created_at) return ''
  return new Date(profile.value.created_at).toLocaleDateString('ru-RU', {
    month: 'long',
    year: 'numeric',
  })
})

const stats = computed(() => {
  if (!profile.value) return []
  return [
    { key: 'projects', label: 'Проекты', value: profile.value.project_count },
    { key: 'versions', label: 'Версии', value: profile.value.version_count },
    { key: 'collabs', label: 'Коллаборации', value: profile.value.collaboration_count },
    { key: 'followers', label: 'Подписчики', value: profile.value.follower_count, clickable: true },
    { key: 'following', label: 'Подписки', value: profile.value.following_count, clickable: true },
  ]
})

const tabs = [
  { id: 'overview' as const, label: 'Обзор' },
  { id: 'projects' as const, label: 'Проекты' },
]

function authHeaders() {
  return { Authorization: `Bearer ${auth.accessToken}` }
}

function copyProfileLink() {
  const apiBase = typeof __API_BASE_URL__ !== 'undefined' && __API_BASE_URL__ ? __API_BASE_URL__ : 'https://vlthub.ru'
  const appUrl = apiBase
  const profileUrl = `${appUrl}/profile/${route.params.username}`
  navigator.clipboard.writeText(profileUrl)
  toast.show('Ссылка скопирована', 'success')
}

function socialIcon(platform: string): string {
  const p = platform.toLowerCase()
  if (p.includes('instagram')) return 'instagram'
  if (p.includes('soundcloud')) return 'soundcloud'
  if (p.includes('youtube')) return 'youtube'
  if (p.includes('twitter') || p.includes('x')) return 'twitter'
  if (p.includes('telegram')) return 'telegram'
  if (p.includes('discord')) return 'discord'
  if (p.includes('tiktok')) return 'tiktok'
  if (p.includes('spotify')) return 'spotify'
  if (p.includes('vk') || p.includes('vkontakte')) return 'vk'
  return 'link'
}

const socialColors: Record<string, string> = {
  instagram: '#E4405F',
  soundcloud: '#FF7700',
  youtube: '#FF0000',
  twitter: '#1DA1F2',
  telegram: '#0088CC',
  discord: '#5865F2',
  tiktok: '#000000',
  spotify: '#1DB954',
  vk: '#0077FF',
}

const socialGradients: Record<string, string> = {
  instagram: 'linear-gradient(135deg, #405DE6, #5851DB, #833AB4, #C13584, #E1306C, #FD1D1D, #F56040, #FCAF45)',
  soundcloud: 'linear-gradient(135deg, #FF7700, #FF5500)',
  youtube: 'linear-gradient(135deg, #FF0000, #CC0000)',
  twitter: 'linear-gradient(135deg, #1DA1F2, #0d8bd9)',
  telegram: 'linear-gradient(135deg, #0088CC, #006D9F)',
  discord: 'linear-gradient(135deg, #5865F2, #4752C4)',
  tiktok: 'linear-gradient(135deg, #00F2EA, #FF0050)',
  spotify: 'linear-gradient(135deg, #1DB954, #169C46)',
  vk: 'linear-gradient(135deg, #0077FF, #005DD1)',
}

const socialIcons: Record<string, string> = {
  instagram: 'M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6m9.65 1.5a1.25 1.25 0 0 1 0 2.5 1.25 1.25 0 0 1 0-2.5M12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10m0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  soundcloud: 'M11.56 8.87V17h8.87a1.57 1.57 0 0 0 1.57-1.57v-2.6a1.57 1.57 0 0 0-1.57-1.57h-.44l.04-.47c.03-.55-.03-1.1-.25-1.6a3.8 3.8 0 0 0-6.22-1.32',
  youtube: 'M23.5 6.19A3.02 3.02 0 0 0 21.36 4C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.36.5A3.02 3.02 0 0 0 .5 6.19 31.6 31.6 0 0 0 0 12c0 1.95.16 3.88.5 5.81A3.02 3.02 0 0 0 2.64 20c1.86.5 9.36.5 9.36.5s7.5 0 9.36-.5a3.02 3.02 0 0 0 2.14-2.19c.34-1.93.5-3.86.5-5.81 0-1.95-.16-3.88-.5-5.81zM9.55 15.57V8.43L15.82 12l-6.27 3.57z',
  twitter: 'M18.24 2.25h3.3l-7.22 8.26 8.5 11.24h-6.65l-5.21-6.82-5.97 6.82H1.7l7.73-8.84L1.3 2.25h6.82l4.71 6.23 5.41-6.23zm-1.16 17.52h1.83L7.08 4.13H5.11l11.97 15.64z',
  telegram: 'M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.9-.88.2-1.3l13.73-5.3c.73-.27 1.44.18 1.16 1.3l-2.36 11.14c-.2.87-.66 1.08-1.33.67l-3.67-2.71-1.77 1.71c-.2.2-.36.36-.72.36z',
  discord: 'M19.27 5.33C17.94 4.71 16.5 4.26 15 4a.09.09 0 0 0-.07.03c-.18.33-.39.76-.53 1.09a16.09 16.09 0 0 0-4.8 0c-.14-.34-.35-.76-.54-1.09c-.01-.02-.04-.03-.07-.03c-1.5.26-2.93.71-4.27 1.33c-.01 0-.02.01-.03.02c-2.72 4.07-3.47 8.03-3.1 11.95c0 .02.01.04.03.05c1.8 1.32 3.53 2.12 5.24 2.65c.03.01.06 0 .07-.02c.4-.55.76-1.13 1.07-1.74c.02-.04 0-.08-.04-.09c-.57-.22-1.11-.48-1.64-.78c-.04-.02-.04-.08-.01-.11c.11-.08.22-.17.33-.25c.02-.02.05-.02.07-.01c3.44 1.57 7.15 1.57 10.55 0c.02-.01.05-.01.07.01c.11.08.22.17.34.25c.04.03.04.09-.01.11c-.52.31-1.07.56-1.64.78c-.04.01-.05.06-.04.09c.32.61.68 1.19 1.07 1.74c.03.01.06.02.09.01c1.72-.53 3.45-1.33 5.25-2.65c.02-.01.03-.03.03-.05c.44-4.53-.73-8.46-3.1-11.95c-.01-.01-.02-.02-.04-.02zM8.52 14.91c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.84 2.12-1.89 2.12zm6.97 0c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.83 2.12-1.89 2.12z',
  tiktok: 'M16.6 5.82s.51.5 0 0A4.28 4.28 0 0 1 15.54 3h-3.09v12.4a2.59 2.59 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6c0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64c0 3.35 2.72 5.7 5.68 5.7c3.14 0 5.7-2.56 5.7-5.7V9.68c.89.7 2 1.11 3.2 1.11V7.72c-1.18 0-2.24-.82-2.56-1.9z',
  spotify: 'M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.52 17.34c-.24.36-.72.48-1.08.24-2.88-1.8-6.48-2.16-10.68-1.2-.36.12-.72-.12-.84-.48-.12-.36.12-.72.48-.84 4.56-1.08 8.52-.6 11.76 1.44.36.12.48.6.36.84zm1.44-3c-.36.48-.96.6-1.44.24-3.24-2.04-8.16-2.64-12-1.44-.48.12-1.08-.12-1.2-.6-.12-.48.12-1.08.6-1.2 4.44-1.32 9.84-.72 13.56 1.56.48.36.6 1.08.24 1.44zm.12-3.36c-3.84-2.28-10.2-2.52-13.8-1.44-.6.12-1.2-.24-1.32-.84-.12-.6.24-1.2.84-1.32 4.2-1.2 11.04-.96 15.48 1.68.48.24.72.84.48 1.32-.24.48-.84.72-1.32.48z',
  vk: 'M15.07 2H8.93C3.33 2 2 3.33 2 8.93v6.14C2 20.67 3.33 22 8.93 22h6.14c5.6 0 6.93-1.33 6.93-6.93V8.93C22 3.33 20.67 2 15.07 2zm1.45 13.5h-1.3c-.57 0-.75-.42-1.78-1.45-.9-.82-1.3-.92-1.52-.92-.3 0-.38.12-.38.45v1.1c0 .33-.1.52-.97.52-1.43 0-3.02-.88-4.12-2.52-1.6-2.28-2.04-3.98-2.04-4.34 0-.2.1-.38.45-.38h1.3c.32 0 .45.15.56.52.6 1.9 1.63 3.57 2.05 3.57.16 0 .23-.07.23-.5v-1.78c-.04-.9-.52-1-.52-1.33 0-.16.13-.3.3-.3h2.05c.26 0 .35.14.35.43v2.32c0 .25.12.33.18.33.15 0 .28-.08.43-.22.8-.9 1.36-2.3 1.36-2.3.07-.17.18-.26.36-.26h1.3c.36 0 .47.2.38.5-.26 1.1-2.03 3.04-2.03 3.04-.17.22-.2.33 0 .56.14.18.6.58.92.94.58.66.96 1.22.77 1.45-.04.05-.08.1-.15.1z',
}

function socialGradientBg(platform: string): string {
  const key = socialIcon(platform)
  const grad = socialGradients[key]
  if (!grad) return ''
  return grad.replace(/#[0-9a-fA-F]{6}/g, (hex) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g2 = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r},${g2},${b},0.06)`
  })
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    in_progress: 'В работе',
    completed: 'Завершён',
    on_hold: 'Отложен',
    archived: 'Архив',
    dropped: 'Закрыт',
  }
  return map[status] || status
}

function statusClass(status: string) {
  const map: Record<string, string> = {
    in_progress: 'bg-blue-500/10 text-blue-600',
    completed: 'bg-emerald-500/10 text-emerald-600',
    on_hold: 'bg-amber-500/10 text-amber-600',
    archived: 'bg-zinc-500/10 text-zinc-600',
    dropped: 'bg-red-500/10 text-red-600',
  }
  return map[status] || 'bg-zinc-500/10 text-zinc-600'
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

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

async function loadProfile() {
  if (!route.params.username) return
  loading.value = true
  try {
    profile.value = await useApiFetch<UserProfileOut>(
      `/api/v1/users/${route.params.username}`,
      { headers: authHeaders() },
    )
  } catch {
    toast.show('Пользователь не найден', 'error')
  } finally {
    loading.value = false
  }
}

async function openFollowers() {
  if (!profile.value) return
  followersModal.value = true
  listLoading.value = true
  try {
    followersList.value = await useApiFetch<FollowOut[]>(
      `/api/v1/users/${profile.value.username}/followers`,
      { headers: authHeaders() },
    )
  } catch {
    toast.show('Не удалось загрузить подписчиков', 'error')
  } finally {
    listLoading.value = false
  }
}

async function openFollowing() {
  if (!profile.value) return
  followingModal.value = true
  listLoading.value = true
  try {
    followingList.value = await useApiFetch<FollowOut[]>(
      `/api/v1/users/${profile.value.username}/following`,
      { headers: authHeaders() },
    )
  } catch {
    toast.show('Не удалось загрузить подписки', 'error')
  } finally {
    listLoading.value = false
  }
}

function onStatClick(key: string) {
  if (key === 'followers') openFollowers()
  if (key === 'following') openFollowing()
}

async function toggleFollow() {
  if (!profile.value) return
  try {
    if (profile.value.is_following) {
      await useApiFetch(`/api/v1/users/${profile.value.username}/follow`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      profile.value.is_following = false
      profile.value.follower_count--
    } else {
      await useApiFetch(`/api/v1/users/${profile.value.username}/follow`, {
        method: 'POST',
        headers: authHeaders(),
      })
      profile.value.is_following = true
      profile.value.follower_count++
    }
  } catch (e: any) {
    toast.show(e.message || 'Ошибка', 'error')
  }
}

onMounted(loadProfile)
</script>

<template>
  <div class="min-h-screen pb-16" :class="profile?.username === 'RR' ? 'profile-page--custom' : ''">
    <!-- Skeleton -->
    <div v-if="loading" class="page-shell-profile pt-6 space-y-6">
      <div class="profile-cover animate-pulse !bg-border/50" />
      <div class="card p-6 -mt-20 animate-pulse">
        <div class="flex gap-5">
          <div class="w-28 h-28 rounded-full bg-btn-secondary" />
          <div class="flex-1 space-y-3 pt-4">
            <div class="h-7 bg-btn-secondary rounded-lg w-48" />
            <div class="h-4 bg-btn-secondary rounded w-32" />
            <div class="h-10 bg-btn-secondary rounded-xl w-full max-w-md" />
          </div>
        </div>
      </div>
    </div>

    <template v-else-if="profile">
      <div
        class="profile-cover"
        :style="profile.cover_url ? { backgroundImage: `url(${resolveApiUrl(profile.cover_url)})`, backgroundSize: 'cover', backgroundPosition: 'center' } : {}"
      >
        <div v-if="profile.cover_url" class="cover-fade" />
      </div>

      <div class="page-shell-profile -mt-20 relative z-10 pb-8">
        <!-- Profile card -->
        <div class="card p-6 sm:p-8 mb-6 shadow-xl shadow-black/[0.04] border-border/25">
          <div class="flex flex-col lg:flex-row lg:items-end gap-6">
            <!-- Avatar -->
            <div class="shrink-0 -mt-16 sm:-mt-20 mx-auto lg:mx-0 relative z-10 ring-spin-on-hover ring-spin-continuous">
              <div
                v-if="profile.active_badge?.avatar_ring_gradient"
                class="inline-flex rounded-full p-[3px] shadow-lg avatar-ring-effect"
                :class="profile.active_badge.avatar_ring_effect ? 'ring-effect-' + profile.active_badge.avatar_ring_effect : ''"
                :style="{ background: profile.active_badge.avatar_ring_gradient, '--ring-gradient': profile.active_badge.avatar_ring_gradient }"
              >
                <div class="rounded-full bg-surface-elevated">
                  <UiAvatar
                    :src="profile.avatar_url"
                    :alt="profile.nickname"
                    size="profile"
                  />
                </div>
              </div>
              <div v-else class="rounded-full bg-surface-elevated p-1 shadow-lg ring-4 ring-[var(--color-avatar-ring)]">
                <UiAvatar
                  :src="profile.avatar_url"
                  :alt="profile.nickname"
                  size="profile"
                />
              </div>
            </div>

            <!-- Info -->
            <div class="flex-1 text-center lg:text-left min-w-0">
              <div class="flex flex-wrap items-center justify-center lg:justify-start gap-2 mb-2">
                <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
                  {{ profile.nickname }}
                  <UserBadgeIcon :badge="profile.active_badge" size="md" />
                </h1>
                <UiBadge v-if="profile.is_public" size="sm" class="bg-emerald-500/10 text-emerald-700 border-0">
                  Публичный
                </UiBadge>
                <UiBadge v-else size="sm" class="bg-zinc-500/10 text-zinc-600 border-0">
                  Приватный
                </UiBadge>
              </div>

              <div class="flex flex-wrap items-center justify-center lg:justify-start gap-2 text-secondary mb-3">
                <span class="text-sm font-medium">@{{ profile.username }}</span>
                <span class="text-[#C7C7CC]">·</span>
                <span class="text-sm">с {{ memberSince }}</span>
              </div>

              <p
                v-if="profile.bio"
                class="text-sm text-[#48484A] leading-relaxed max-w-xl mx-auto lg:mx-0 mb-4"
              >
                {{ profile.bio }}
              </p>
              <p v-else-if="isOwnProfile" class="text-sm text-secondary italic mb-4">
                Добавьте описание в настройках профиля
              </p>

              <!-- Actions -->
              <div class="flex flex-wrap items-center justify-center lg:justify-start gap-2">
                <NuxtLink
                  v-if="isOwnProfile"
                  to="/settings"
                  class="inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200 px-3 py-1.5 text-xs bg-primary text-white hover:bg-primary/90 no-underline"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                  </svg>
                  Редактировать
                </NuxtLink>
                <UiButton
                  v-else
                  size="sm"
                  :variant="profile.is_following ? 'secondary' : 'primary'"
                  @click="toggleFollow"
                >
                  {{ profile.is_following ? 'Отписаться' : 'Подписаться' }}
                </UiButton>
                <UiButton variant="secondary" size="sm" @click="copyProfileLink">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Поделиться
                </UiButton>
              </div>
            </div>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-8 pt-6 border-t border-separator">
            <button
              v-for="stat in stats"
              :key="stat.key"
              type="button"
              class="stat-tile"
              :class="stat.clickable ? 'stat-tile-clickable' : 'cursor-default'"
              @click="stat.clickable && onStatClick(stat.key)"
            >
              <p class="text-2xl font-bold text-foreground tabular-nums">{{ stat.value }}</p>
              <p class="text-xs text-secondary mt-0.5">{{ stat.label }}</p>
            </button>
          </div>
        </div>

        <div class="tabs-bar mb-6 w-fit mx-auto sm:mx-0">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            class="tab-btn"
            :class="activeTab === tab.id ? 'tab-btn-active' : 'tab-btn-inactive'"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab: Overview -->
        <div v-show="activeTab === 'overview'" class="grid lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2 space-y-6">
            <!-- Recent projects preview -->
            <section v-if="profile.projects?.length" class="card p-6">
              <div class="flex items-center justify-between mb-5">
                <h2 class="text-lg font-semibold">Недавние проекты</h2>
                <button
                  type="button"
                  class="text-sm text-primary font-medium hover:underline"
                  @click="activeTab = 'projects'"
                >
                  Все →
                </button>
              </div>
              <div class="grid sm:grid-cols-2 gap-4">
                <NuxtLink
                  v-for="p in profile.projects.slice(0, 4)"
                  :key="p.id"
                  :to="`/projects/${p.id}`"
                  class="group rounded-2xl overflow-hidden border border-border/15 hover:border-primary/20 hover:shadow-lg transition-all no-underline"
                >
                  <div
                    class="aspect-square relative overflow-hidden"
                    :class="p.cover_url ? '' : 'bg-gradient-to-br from-[#F5F5F7] to-primary/10'"
                  >
                    <img
                      v-if="p.cover_url"
                      :src="resolveApiUrl(p.cover_url)"
                      :alt="p.title"
                      class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div v-else class="absolute inset-0 flex items-center justify-center">
                      <svg class="w-10 h-10 text-primary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                      </svg>
                    </div>
                    <span
                      class="absolute top-2 right-2 text-[10px] font-semibold px-2 py-0.5 rounded-full backdrop-blur-md bg-surface-elevated/90"
                      :style="{ color: getDawColor(p.daw_type) }"
                    >
                      {{ getDawName(p.daw_type) }}
                    </span>
                  </div>
                  <div class="p-4">
                    <p class="font-semibold text-foreground truncate group-hover:text-primary transition-colors">
                      {{ p.title }}
                    </p>
                    <p class="text-xs text-secondary mt-1">
                      {{ p.version_count }} {{ p.version_count === 1 ? 'версия' : 'версий' }}
                      <span v-if="p.bpm"> · {{ p.bpm }} BPM</span>
                    </p>
                  </div>
                </NuxtLink>
              </div>
            </section>

            <section v-else class="card p-12 text-center">
              <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-surface flex items-center justify-center">
                <svg class="w-8 h-8 text-secondary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
              </div>
              <p class="text-secondary text-sm">
                {{ isOwnProfile ? 'Создайте первый проект на главной' : 'Пока нет публичных проектов' }}
              </p>
              <NuxtLink
                v-if="isOwnProfile"
                to="/"
                class="inline-flex items-center justify-center mt-4 rounded-lg font-medium px-3 py-1.5 text-xs bg-primary text-white hover:bg-primary/90 no-underline"
              >
                К проектам
              </NuxtLink>
            </section>
          </div>

          <!-- Sidebar -->
          <aside class="space-y-6">
            <!-- Quick stats -->
            <div class="card p-6">
              <h3 class="text-sm font-semibold text-secondary uppercase tracking-wider mb-4">Статистика</h3>
              <ul class="space-y-3">
                <li class="flex justify-between text-sm">
                  <span class="text-secondary">Версий сохранено</span>
                  <span class="font-semibold">{{ profile.version_count }}</span>
                </li>
                <li class="flex justify-between text-sm">
                  <span class="text-secondary">Коллабораций</span>
                  <span class="font-semibold">{{ profile.collaboration_count }}</span>
                </li>
                <li class="flex justify-between text-sm">
                  <span class="text-secondary">Проектов</span>
                  <span class="font-semibold">{{ profile.project_count }}</span>
                </li>
              </ul>
            </div>

            <!-- Storage (own profile only) -->
            <div v-if="isOwnProfile" class="card p-6">
              <h3 class="text-sm font-semibold text-secondary uppercase tracking-wider mb-4">Хранилище</h3>
              <div class="flex items-center justify-between text-xs text-secondary mb-1.5">
                <span>{{ formatBytes(auth.user?.storage_used || 0) }} / {{ formatBytes(auth.user?.storage_limit || 0) }}</span>
                <span>{{ usagePercent(auth.user?.storage_used || 0, auth.user?.storage_limit || 0) }}%</span>
              </div>
              <div class="h-2 rounded-full bg-btn-secondary overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :class="usagePercent(auth.user?.storage_used || 0, auth.user?.storage_limit || 0) > 90 ? 'bg-red-500' : 'bg-primary'"
                  :style="{ width: usagePercent(auth.user?.storage_used || 0, auth.user?.storage_limit || 0) + '%' }"
                />
              </div>
            </div>

            <!-- Social -->
            <div v-if="profile.social_links?.length" class="card p-6">
              <h3 class="text-sm font-semibold text-secondary uppercase tracking-wider mb-4">Ссылки</h3>
              <div class="flex flex-col gap-2">
                <a
                  v-for="link in profile.social_links"
                  :key="link.platform + link.url"
                  :href="link.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-primary/5 hover:text-primary transition-colors no-underline text-sm font-medium text-foreground"
                  :style="{ background: socialGradientBg(link.platform) || undefined }"
                  @click.prevent="openExternal(link.url)"
                >
                  <span
                    class="w-9 h-9 rounded-lg flex items-center justify-center shadow-sm"
                    :style="{ backgroundColor: (socialColors[socialIcon(link.platform)] || '#888') + '20' }"
                  >
                    <svg
                      class="w-4 h-4"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      :style="{ color: socialColors[socialIcon(link.platform)] || '#888' }"
                    >
                      <path v-if="socialIcons[socialIcon(link.platform)]" :d="socialIcons[socialIcon(link.platform)]" />
                      <template v-else>
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </template>
                    </svg>
                  </span>
                  <span class="truncate">{{ link.platform }}</span>
                </a>
              </div>
            </div>
            <div v-else-if="isOwnProfile" class="card p-6">
              <h3 class="text-sm font-semibold text-secondary uppercase tracking-wider mb-2">Ссылки</h3>
              <p class="text-sm text-secondary mb-3">Instagram, SoundCloud, YouTube</p>
              <NuxtLink
                to="/settings"
                class="flex items-center justify-center w-full rounded-lg font-medium px-3 py-1.5 text-xs bg-btn-secondary text-foreground hover:bg-[#D1D1D6] no-underline transition-colors"
              >
                Добавить ссылки
              </NuxtLink>
            </div>
          </aside>
        </div>

        <!-- Tab: Projects -->
        <div v-show="activeTab === 'projects'">
          <div v-if="profile.projects?.length" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <NuxtLink
              v-for="p in profile.projects"
              :key="p.id"
              :to="`/projects/${p.id}`"
              class="card overflow-hidden no-underline group hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300 p-0"
            >
              <div
                class="aspect-square relative"
                :class="p.cover_url ? '' : 'bg-gradient-to-br from-[#1D1D1F]/5 to-primary/15'"
              >
                <img
                  v-if="p.cover_url"
                  :src="resolveApiUrl(p.cover_url)"
                  :alt="p.title"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div
                  v-else
                  class="absolute inset-0 flex items-center justify-center"
                >
                  <div
                    class="w-14 h-14 rounded-2xl flex items-center justify-center text-white text-xl font-bold shadow-lg"
                    :style="{ backgroundColor: getDawColor(p.daw_type) }"
                  >
                    {{ getDawName(p.daw_type).charAt(0) }}
                  </div>
                </div>
                <span
                  class="absolute top-3 left-3 text-[10px] font-semibold px-2.5 py-1 rounded-full backdrop-blur-md"
                  :class="statusClass(p.status)"
                >
                  {{ statusLabel(p.status) }}
                </span>
              </div>
              <div class="p-5">
                <h3 class="font-semibold text-foreground truncate group-hover:text-primary transition-colors">
                  {{ p.title }}
                </h3>
                <div class="flex flex-wrap gap-1.5 mt-2">
                  <span v-if="p.bpm" class="text-[11px] px-2 py-0.5 rounded-md bg-surface text-secondary">
                    {{ p.bpm }} BPM
                  </span>
                  <span v-if="p.key" class="text-[11px] px-2 py-0.5 rounded-md bg-surface text-secondary">
                    {{ p.key }}
                  </span>
                  <span class="text-[11px] px-2 py-0.5 rounded-md bg-surface text-secondary">
                    {{ getDawName(p.daw_type) }}
                  </span>
                </div>
                <div class="flex items-center justify-between mt-4 pt-4 border-t border-separator text-xs text-secondary">
                  <span>{{ p.version_count }} версий</span>
                  <span>{{ formatDate(p.updated_at) }}</span>
                </div>
              </div>
            </NuxtLink>
          </div>
          <div v-else class="card p-16 text-center">
            <p class="text-secondary">Нет проектов для отображения</p>
          </div>
        </div>

      </div>
    </template>

    <!-- Followers modal -->
    <UiModal v-model="followersModal" title="Подписчики" max-width="420px">
      <div v-if="listLoading" class="py-8 text-center text-secondary text-sm">Загрузка...</div>
      <ul v-else-if="followersList.length" class="max-h-80 overflow-y-auto divide-y divide-separator -mx-2">
        <li v-for="u in followersList" :key="u.id">
          <NuxtLink
            :to="`/profile/${u.username}`"
            class="flex items-center gap-3 px-2 py-3 hover:bg-surface rounded-xl transition-colors no-underline"
            @click="followersModal = false"
          >
            <UiAvatarRing :src="u.avatar_url" :alt="u.nickname" size="sm" :badge="(u as any).active_badge" />
            <div class="min-w-0">
              <p class="text-sm font-medium text-foreground truncate flex items-center gap-1">
                {{ u.nickname }}
                <UserBadgeIcon :badge="(u as any).active_badge" size="sm" />
              </p>
              <p class="text-xs text-secondary">@{{ u.username }}</p>
            </div>
          </NuxtLink>
        </li>
      </ul>
      <p v-else class="py-8 text-center text-secondary text-sm">Пока нет подписчиков</p>
    </UiModal>

    <!-- Following modal -->
    <UiModal v-model="followingModal" title="Подписки" max-width="420px">
      <div v-if="listLoading" class="py-8 text-center text-secondary text-sm">Загрузка...</div>
      <ul v-else-if="followingList.length" class="max-h-80 overflow-y-auto divide-y divide-separator -mx-2">
        <li v-for="u in followingList" :key="u.id">
          <NuxtLink
            :to="`/profile/${u.username}`"
            class="flex items-center gap-3 px-2 py-3 hover:bg-surface rounded-xl transition-colors no-underline"
            @click="followingModal = false"
          >
            <UiAvatarRing :src="u.avatar_url" :alt="u.nickname" size="sm" :badge="(u as any).active_badge" />
            <div class="min-w-0">
              <p class="text-sm font-medium text-foreground truncate flex items-center gap-1">
                {{ u.nickname }}
                <UserBadgeIcon :badge="(u as any).active_badge" size="sm" />
              </p>
              <p class="text-xs text-secondary">@{{ u.username }}</p>
            </div>
          </NuxtLink>
        </li>
      </ul>
      <p v-else class="py-8 text-center text-secondary text-sm">Нет подписок</p>
    </UiModal>
  </div>
</template>
