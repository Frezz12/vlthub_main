<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
import { formatError } from '~/utils/formatError'

const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }
const { mode, setMode } = useTheme()

const route = useRoute()

// --- PIN section ---
const pin = ref('')
const pinConfirm = ref('')
const pinLoading = ref(false)

onMounted(() => {
  if (route.query.setup_pin === '1') {
    nextTick(() => {
      document.getElementById('pin-section')?.scrollIntoView({ behavior: 'smooth' })
    })
  }
})

async function handleSetPin() {
  if (pin.value.length < 4 || pin.value.length > 6 || !/^\d{4,6}$/.test(pin.value)) {
    toast.show('PIN должен быть 4-6 цифр', 'error')
    return
  }
  if (pin.value !== pinConfirm.value) {
    toast.show('PIN-коды не совпадают', 'error')
    return
  }
  pinLoading.value = true
  try {
    await useApiFetch('/api/v1/auth/pin', {
      method: 'PUT',
      headers: auth._authHeaders(),
      body: { pin: pin.value },
    })
    await auth.fetchPinStatus()
    toast.show('PIN-код установлен', 'success')
    pin.value = ''
    pinConfirm.value = ''
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    pinLoading.value = false
  }
}

// --- Badges section ---
import type { UserBadgeOut } from '@pjasaver/shared-types'

const userBadges = ref<UserBadgeOut[]>([])
const badgeLoading = ref(false)

async function fetchBadges() {
  badgeLoading.value = true
  try {
    userBadges.value = await useApiFetch<UserBadgeOut[]>('/api/v1/users/me/badges', {
      headers: auth._authHeaders(),
    })
  } catch { /* ignore */ }
  finally { badgeLoading.value = false }
}

async function selectBadge(badgeId: string) {
  try {
    await useApiFetch(`/api/v1/users/me/badges/${badgeId}/activate`, {
      method: 'POST',
      headers: auth._authHeaders(),
    })
    await fetchBadges()
    await auth.fetchMe()
    toast.show('Значок выбран', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

async function deactivateBadge() {
  try {
    await useApiFetch('/api/v1/users/me/badges/deactivate', {
      method: 'POST',
      headers: auth._authHeaders(),
    })
    await fetchBadges()
    await auth.fetchMe()
    toast.show('Значок убран', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

onMounted(() => {
  fetchBadges()
})

const themeOptions: { value: 'light' | 'dark' | 'system'; label: string; hint: string }[] = [
  { value: 'light', label: 'Светлая', hint: 'Всегда светлый интерфейс' },
  { value: 'dark', label: 'Тёмная', hint: 'Всегда тёмный интерфейс' },
  { value: 'system', label: 'Системная', hint: 'Как в настройках ОС' },
]

// --- Profile section ---
const nickname = ref(auth.user?.nickname || '')
const bio = ref(auth.user?.bio || '')
const isPublic = ref(auth.user?.is_public ?? true)
const profileLoading = ref(false)
const avatarUploading = ref(false)
const coverUploading = ref(false)
const avatarInput = ref<HTMLInputElement>()
const coverInput = ref<HTMLInputElement>()
const cropModal = ref(false)
const cropImageSrc = ref('')
const cropFile = ref<File | null>(null)

const socialLinks = ref<{ platform: string; url: string }[]>(
  JSON.parse(JSON.stringify(auth.user?.social_links || [])),
)

const knownPlatforms: Record<string, { icon: string; color: string; gradient: string; placeholder: string }> = {
  instagram: { icon: 'M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6m9.65 1.5a1.25 1.25 0 0 1 0 2.5 1.25 1.25 0 0 1 0-2.5M12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10m0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z', color: '#E4405F', gradient: 'linear-gradient(135deg, #405DE6, #5851DB, #833AB4, #C13584, #E1306C, #FD1D1D, #F56040, #FCAF45)', placeholder: 'username' },
  soundcloud: { icon: 'M11.56 8.87V17h8.87a1.57 1.57 0 0 0 1.57-1.57v-2.6a1.57 1.57 0 0 0-1.57-1.57h-.44l.04-.47c.03-.55-.03-1.1-.25-1.6a3.8 3.8 0 0 0-6.22-1.32', color: '#FF7700', gradient: 'linear-gradient(135deg, #FF7700, #FF5500)', placeholder: 'username' },
  youtube: { icon: 'M23.5 6.19A3.02 3.02 0 0 0 21.36 4C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.36.5A3.02 3.02 0 0 0 .5 6.19 31.6 31.6 0 0 0 0 12c0 1.95.16 3.88.5 5.81A3.02 3.02 0 0 0 2.64 20c1.86.5 9.36.5 9.36.5s7.5 0 9.36-.5a3.02 3.02 0 0 0 2.14-2.19c.34-1.93.5-3.86.5-5.81 0-1.95-.16-3.88-.5-5.81zM9.55 15.57V8.43L15.82 12l-6.27 3.57z', color: '#FF0000', gradient: 'linear-gradient(135deg, #FF0000, #CC0000)', placeholder: 'channel URL or @username' },
  twitter: { icon: 'M18.24 2.25h3.3l-7.22 8.26 8.5 11.24h-6.65l-5.21-6.82-5.97 6.82H1.7l7.73-8.84L1.3 2.25h6.82l4.71 6.23 5.41-6.23zm-1.16 17.52h1.83L7.08 4.13H5.11l11.97 15.64z', color: '#1DA1F2', gradient: 'linear-gradient(135deg, #1DA1F2, #0d8bd9)', placeholder: 'username' },
  telegram: { icon: 'M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.9-.88.2-1.3l13.73-5.3c.73-.27 1.44.18 1.16 1.3l-2.36 11.14c-.2.87-.66 1.08-1.33.67l-3.67-2.71-1.77 1.71c-.2.2-.36.36-.72.36z', color: '#0088CC', gradient: 'linear-gradient(135deg, #0088CC, #006D9F)', placeholder: 'username' },
  discord: { icon: 'M19.27 5.33C17.94 4.71 16.5 4.26 15 4a.09.09 0 0 0-.07.03c-.18.33-.39.76-.53 1.09a16.09 16.09 0 0 0-4.8 0c-.14-.34-.35-.76-.54-1.09c-.01-.02-.04-.03-.07-.03c-1.5.26-2.93.71-4.27 1.33c-.01 0-.02.01-.03.02c-2.72 4.07-3.47 8.03-3.1 11.95c0 .02.01.04.03.05c1.8 1.32 3.53 2.12 5.24 2.65c.03.01.06 0 .07-.02c.4-.55.76-1.13 1.07-1.74c.02-.04 0-.08-.04-.09c-.57-.22-1.11-.48-1.64-.78c-.04-.02-.04-.08-.01-.11c.11-.08.22-.17.33-.25c.02-.02.05-.02.07-.01c3.44 1.57 7.15 1.57 10.55 0c.02-.01.05-.01.07.01c.11.08.22.17.34.25c.04.03.04.09-.01.11c-.52.31-1.07.56-1.64.78c-.04.01-.05.06-.04.09c.32.61.68 1.19 1.07 1.74c.03.01.06.02.09.01c1.72-.53 3.45-1.33 5.25-2.65c.02-.01.03-.03.03-.05c.44-4.53-.73-8.46-3.1-11.95c-.01-.01-.02-.02-.04-.02zM8.52 14.91c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.84 2.12-1.89 2.12zm6.97 0c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.83 2.12-1.89 2.12z', color: '#5865F2', gradient: 'linear-gradient(135deg, #5865F2, #4752C4)', placeholder: 'username' },
  tiktok: { icon: 'M16.6 5.82s.51.5 0 0A4.28 4.28 0 0 1 15.54 3h-3.09v12.4a2.59 2.59 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6c0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64c0 3.35 2.72 5.7 5.68 5.7c3.14 0 5.7-2.56 5.7-5.7V9.68c.89.7 2 1.11 3.2 1.11V7.72c-1.18 0-2.24-.82-2.56-1.9z', color: '#000000', gradient: 'linear-gradient(135deg, #00F2EA, #FF0050)', placeholder: 'username' },
  spotify: { icon: 'M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.52 17.34c-.24.36-.72.48-1.08.24-2.88-1.8-6.48-2.16-10.68-1.2-.36.12-.72-.12-.84-.48-.12-.36.12-.72.48-.84 4.56-1.08 8.52-.6 11.76 1.44.36.12.48.6.36.84zm1.44-3c-.36.48-.96.6-1.44.24-3.24-2.04-8.16-2.64-12-1.44-.48.12-1.08-.12-1.2-.6-.12-.48.12-1.08.6-1.2 4.44-1.32 9.84-.72 13.56 1.56.48.36.6 1.08.24 1.44zm.12-3.36c-3.84-2.28-10.2-2.52-13.8-1.44-.6.12-1.2-.24-1.32-.84-.12-.6.24-1.2.84-1.32 4.2-1.2 11.04-.96 15.48 1.68.48.24.72.84.48 1.32-.24.48-.84.72-1.32.48z', color: '#1DB954', gradient: 'linear-gradient(135deg, #1DB954, #169C46)', placeholder: 'track/artist URL' },
  vk: { icon: 'M15.07 2H8.93C3.33 2 2 3.33 2 8.93v6.14C2 20.67 3.33 22 8.93 22h6.14c5.6 0 6.93-1.33 6.93-6.93V8.93C22 3.33 20.67 2 15.07 2zm1.45 13.5h-1.3c-.57 0-.75-.42-1.78-1.45-.9-.82-1.3-.92-1.52-.92-.3 0-.38.12-.38.45v1.1c0 .33-.1.52-.97.52-1.43 0-3.02-.88-4.12-2.52-1.6-2.28-2.04-3.98-2.04-4.34 0-.2.1-.38.45-.38h1.3c.32 0 .45.15.56.52.6 1.9 1.63 3.57 2.05 3.57.16 0 .23-.07.23-.5v-1.78c-.04-.9-.52-1-.52-1.33 0-.16.13-.3.3-.3h2.05c.26 0 .35.14.35.43v2.32c0 .25.12.33.18.33.15 0 .28-.08.43-.22.8-.9 1.36-2.3 1.36-2.3.07-.17.18-.26.36-.26h1.3c.36 0 .47.2.38.5-.26 1.1-2.03 3.04-2.03 3.04-.17.22-.2.33 0 .56.14.18.6.58.92.94.58.66.96 1.22.77 1.45-.04.05-.08.1-.15.1z', color: '#0077FF', gradient: 'linear-gradient(135deg, #0077FF, #005DD1)', placeholder: 'username' },
}

function platformInfo(platform: string) {
  return knownPlatforms[platform.toLowerCase().trim()]
}

function platformGradientBg(platform: string): string {
  const info = platformInfo(platform)
  if (!info?.gradient) return ''
  return info.gradient.replace(/#[0-9a-fA-F]{6}/g, (hex) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r},${g},${b},0.06)`
  })
}

async function handleAvatarUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  avatarUploading.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const api = useApi()
    await api.upload('/api/v1/users/me/avatar', form)
    await auth.fetchMe()
    toast.show('Аватар обновлён', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    avatarUploading.value = false
  }
}

async function handleCoverSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    cropImageSrc.value = reader.result as string
    cropFile.value = file
    cropModal.value = true
  }
  reader.readAsDataURL(file)
  if (coverInput.value) coverInput.value.value = ''
}

async function handleCoverCrop(blob: Blob) {
  cropModal.value = false
  coverUploading.value = true
  try {
    const form = new FormData()
    form.append('file', blob, cropFile.value?.name || 'cover.jpg')
    const api = useApi()
    await api.upload('/api/v1/users/me/cover', form)
    await auth.fetchMe()
    toast.show('Фон профиля обновлён', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    coverUploading.value = false
  }
}

async function handleProfileSave() {
  profileLoading.value = true
  try {
    const api = useApi()
    await api.patch('/api/v1/users/me', { nickname: nickname.value, bio: bio.value, is_public: isPublic.value })
    if (socialLinks.value.length) {
      await api.patch('/api/v1/users/me/social-links', JSON.parse(JSON.stringify(socialLinks.value)))
    }
    await auth.fetchMe()
    toast.show('Профиль обновлён', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    profileLoading.value = false
  }
}

function addSocial() {
  socialLinks.value.push({ platform: '', url: '' })
}
function removeSocial(index: number) {
  socialLinks.value.splice(index, 1)
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

function copyReferralCode() {
  if (auth.user?.referral_code) {
    navigator.clipboard.writeText(auth.user.referral_code)
    toast.show('Код скопирован', 'success')
  }
}

</script>

<template>
  <div class="page-shell-narrow space-y-8">
    <div>
      <h1 class="page-title">Настройки</h1>
      <p class="page-subtitle">Профиль</p>
    </div>

    <!-- Appearance -->
    <div class="card p-6">
      <h2 class="text-base font-semibold mb-1">Оформление</h2>
      <p class="text-sm text-secondary mb-5">Выберите тему интерфейса приложения</p>
      <div class="grid sm:grid-cols-3 gap-3">
        <button
          v-for="opt in themeOptions"
          :key="opt.value"
          type="button"
          class="rounded-xl border p-4 text-left transition-all duration-200"
          :class="mode === opt.value
            ? 'border-primary bg-primary/10 ring-2 ring-primary/20'
            : 'border-border bg-surface hover:border-primary/30'"
          @click="setMode(opt.value)"
        >
          <span class="text-sm font-semibold block text-foreground">{{ opt.label }}</span>
          <span class="text-xs text-secondary mt-1 block">{{ opt.hint }}</span>
        </button>
      </div>
    </div>

    <!-- Profile -->
    <div class="card p-6">
        <div class="flex flex-col sm:flex-row sm:items-center gap-5 mb-6 pb-6 border-b border-separator">
          <div class="relative shrink-0 mx-auto sm:mx-0">
            <div
              v-if="auth.user?.active_badge?.avatar_ring_gradient"
              class="inline-flex rounded-full p-[3px] shadow-md avatar-ring-effect"
              :class="auth.user.active_badge.avatar_ring_effect ? 'ring-effect-' + auth.user.active_badge.avatar_ring_effect : ''"
              :style="{ background: auth.user.active_badge.avatar_ring_gradient, '--ring-gradient': auth.user.active_badge.avatar_ring_gradient }"
            >
              <div class="rounded-full bg-surface-elevated">
                <UiAvatar
                  :src="auth.user?.avatar_url"
                  :alt="auth.user?.nickname"
                  size="xl"
                />
              </div>
            </div>
            <div v-else class="rounded-full bg-surface-elevated p-1 shadow-md ring-4 ring-[var(--color-avatar-ring)]">
              <UiAvatar
                :src="auth.user?.avatar_url"
                :alt="auth.user?.nickname"
                size="xl"
              />
            </div>
            <div
              v-if="avatarUploading"
              class="absolute inset-0 rounded-full bg-surface-elevated/80 flex items-center justify-center"
            >
              <svg class="w-6 h-6 text-primary animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          </div>
          <div class="flex-1 flex flex-wrap justify-center sm:justify-start gap-2">
            <input
              ref="avatarInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleAvatarUpload"
            />
            <UiButton
              variant="secondary"
              size="sm"
              :loading="avatarUploading"
              @click="avatarInput?.click()"
            >
              Загрузить фото
            </UiButton>
            <NuxtLink
              v-if="auth.user?.username"
              :to="`/profile/${auth.user.username}`"
              class="inline-flex items-center justify-center gap-2 rounded-xl font-medium px-3 py-1.5 text-xs text-primary no-underline transition-colors"
              style="background-color: color-mix(in srgb, var(--color-primary) 10%, transparent)"
            >
              Посмотреть профиль
            </NuxtLink>
          </div>
        </div>

        <!-- Cover -->
        <div class="flex flex-col sm:flex-row sm:items-center gap-5 mb-6 pb-6 border-b border-separator">
          <div class="relative w-full h-32 rounded-xl overflow-hidden bg-surface shrink-0 sm:w-48">
            <div
              v-if="auth.user?.cover_url"
              class="w-full h-full bg-cover bg-center"
              :style="{ backgroundImage: `url(${resolveApiUrl(auth.user.cover_url)})` }"
            />
            <div class="w-full h-full flex items-center justify-center text-secondary text-sm">
              {{ auth.user?.cover_url ? '' : 'Нет фона' }}
            </div>
            <div
              v-if="coverUploading"
              class="absolute inset-0 bg-surface-elevated/80 flex items-center justify-center"
            >
              <svg class="w-6 h-6 text-primary animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          </div>
          <div class="flex-1">
            <p class="text-sm font-medium mb-1">Фон профиля</p>
            <p class="text-xs text-secondary mb-3">Изображение в шапке профиля</p>
            <input
              ref="coverInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleCoverSelect"
            />
            <UiButton
              variant="secondary"
              size="sm"
              :loading="coverUploading"
              @click="coverInput?.click()"
            >
              {{ auth.user?.cover_url ? 'Сменить фон' : 'Загрузить фон' }}
            </UiButton>
          </div>
        </div>

        <UiModal v-model="cropModal" title="Кадрирование фона" max-width="600px">
          <UiImageCropper v-if="cropImageSrc" :image="cropImageSrc" :aspect-ratio="3" @crop="handleCoverCrop" @cancel="cropModal = false" />
        </UiModal>

        <form class="flex flex-col gap-5" @submit.prevent="handleProfileSave">
          <div class="grid sm:grid-cols-2 gap-4">
            <UiInput v-model="nickname" label="Имя артиста" />
            <div>
              <label class="block text-sm font-medium text-foreground mb-1.5">Username</label>
              <p class="rounded-lg input-control px-3 py-2.5 text-sm text-secondary">
                <span>@{{ auth.user?.username }}</span>
              </p>
            </div>
          </div>

          <UiInput
            v-model="bio"
            label="О себе"
            placeholder="Продюсер, битмейкер, звукорежиссёр..."
          />

          <label
            class="flex items-center justify-between p-4 rounded-xl bg-input-bg cursor-pointer"
          >
            <div>
              <span class="text-sm font-medium block">Публичный профиль</span>
              <span class="text-xs text-secondary">Другие пользователи смогут найти вас</span>
            </div>
            <input
              v-model="isPublic"
              type="checkbox"
              class="rounded border-border text-primary focus:ring-primary w-4 h-4"
            />
          </label>

          <div class="border-t border-separator pt-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <span class="text-sm font-semibold block">Социальные сети</span>
                <span class="text-xs text-secondary">Instagram, SoundCloud, YouTube</span>
              </div>
              <UiButton variant="ghost" size="sm" @click="addSocial">+ Добавить</UiButton>
            </div>

            <div
              v-for="(link, i) in socialLinks"
              :key="i"
              class="flex items-center gap-2 mb-2 p-3 rounded-xl"
              :style="{ background: platformGradientBg(link.platform) || undefined }"
            >
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                :style="{ backgroundColor: (platformInfo(link.platform)?.color || '#888') + '20' }"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  :style="{ color: platformInfo(link.platform)?.color || '#888' }"
                >
                  <path :d="platformInfo(link.platform)?.icon || ''" />
                </svg>
              </div>
              <select
                v-model="link.platform"
                class="rounded-lg input-control px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 min-w-[130px]"
              >
                <option value="" disabled>Платформа</option>
                <option v-for="(info, key) in knownPlatforms" :key="key" :value="key">
                  {{ key.charAt(0).toUpperCase() + key.slice(1) }}
                </option>
              </select>
              <input
                v-model="link.url"
                :placeholder="platformInfo(link.platform)?.placeholder || 'https://...'"
                class="flex-1 rounded-lg input-control px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
              <button
                type="button"
                class="text-secondary hover:text-danger p-2 rounded-lg hover:bg-danger/10 transition-colors shrink-0"
                @click="removeSocial(i)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div class="flex justify-end pt-2">
            <UiButton :loading="profileLoading" type="submit">Сохранить профиль</UiButton>
          </div>
        </form>
    </div>

    <!-- Storage -->
    <div v-if="auth.user" class="card p-6">
      <h2 class="text-base font-semibold mb-1">Хранилище</h2>
      <p class="text-sm text-secondary mb-5">Использование дискового пространства</p>
      <div class="flex items-center justify-between text-sm text-secondary mb-1.5">
        <span>{{ formatBytes(auth.user.storage_used || 0) }} / {{ formatBytes(auth.user.storage_limit || 0) }}</span>
        <span>{{ usagePercent(auth.user.storage_used || 0, auth.user.storage_limit || 0) }}%</span>
      </div>
      <div class="h-2.5 rounded-full bg-btn-secondary overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-300"
          :class="usagePercent(auth.user.storage_used || 0, auth.user.storage_limit || 0) > 90 ? 'bg-red-500' : 'bg-primary'"
          :style="{ width: usagePercent(auth.user.storage_used || 0, auth.user.storage_limit || 0) + '%' }"
        />
      </div>
    </div>

    <!-- Referral -->
    <div v-if="auth.user?.referral_code" class="card p-6">
      <h2 class="text-base font-semibold mb-1">Реферальная программа</h2>
      <p class="text-sm text-secondary mb-3">Приглашайте друзей и получайте +1 ГБ за каждого!</p>
      <div class="flex items-center gap-3 mb-2">
        <span class="text-lg font-mono font-bold tracking-wider text-primary">{{ auth.user.referral_code }}</span>
        <button
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-primary text-white hover:opacity-90 transition-opacity border-none cursor-pointer"
          @click="copyReferralCode"
        >
          Скопировать
        </button>
      </div>
      <p class="text-xs text-secondary">Приглашено: <span class="text-foreground font-medium">{{ auth.user.referrals_count || 0 }}</span></p>
    </div>

    <!-- Badges -->
    <div v-if="auth.user" class="card p-6">
      <h2 class="text-base font-semibold mb-1">Значки</h2>
      <p class="text-sm text-secondary mb-5">Выберите значок для отображения рядом с ником</p>
      <div v-if="userBadges.length === 0" class="text-sm text-secondary italic">
        У вас пока нет значков
      </div>
      <div v-else class="flex flex-wrap gap-2">
        <button
          type="button"
          class="flex items-center gap-2 px-3 py-2 rounded-xl border transition-all duration-200"
          :class="!auth.user?.active_badge
            ? 'border-primary bg-primary/10 ring-2 ring-primary/20'
            : 'border-border bg-surface hover:border-primary/30'"
          @click="deactivateBadge"
        >
          <span class="w-5 h-5 inline-flex items-center justify-center text-sm text-secondary">—</span>
          <span class="text-sm font-medium">Без значка</span>
        </button>
        <button
          v-for="ub in userBadges"
          :key="ub.badge.id"
          type="button"
          class="flex items-center gap-2 px-3 py-2 rounded-xl border transition-all duration-200"
          :class="ub.is_active
            ? 'border-primary bg-primary/10 ring-2 ring-primary/20'
            : 'border-border bg-surface hover:border-primary/30'"
          @click="selectBadge(ub.badge.id)"
        >
          <span class="w-5 h-5 inline-flex items-center justify-center" v-html="ub.badge.icon_svg" />
          <span class="text-sm font-medium">{{ ub.badge.name }}</span>
        </button>
      </div>
    </div>

    <!-- PIN -->
    <div id="pin-section" class="card p-6">
      <div class="flex items-start gap-3 mb-4">
        <div class="w-9 h-9 rounded-xl bg-warning/20 flex items-center justify-center shrink-0 mt-0.5">
          <svg class="w-5 h-5 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
          </svg>
        </div>
        <div>
          <h2 class="text-base font-semibold">PIN-код восстановления</h2>
          <p class="text-sm text-secondary mt-1">
            PIN-код используется для сброса пароля, если вы его забудете.
            Без PIN-кода восстановить доступ к аккаунту будет невозможно.
            Код должен содержать 4–6 цифр.
          </p>
          <p v-if="auth.hasPin" class="text-xs text-success mt-1">
            ✓ PIN-код установлен
          </p>
        </div>
      </div>

      <form class="flex flex-col gap-3 max-w-xs" @submit.prevent="handleSetPin">
        <UiInput v-model="pin" label="Новый PIN-код" type="password" maxlength="6" />
        <UiInput v-model="pinConfirm" label="Подтвердите PIN" type="password" maxlength="6" />
        <UiButton :loading="pinLoading" type="submit" size="sm" class="self-start">
          {{ auth.hasPin ? 'Изменить PIN' : 'Установить PIN' }}
        </UiButton>
      </form>
    </div>

    <!-- Auth -->
    <div class="card p-6 flex items-center justify-between">
      <div>
        <h2 class="text-base font-semibold">Аккаунт</h2>
        <p class="text-sm text-secondary mt-1">Выйти из аккаунта на этом устройстве</p>
      </div>
      <UiButton variant="danger" @click="auth.logout()">Выйти</UiButton>
    </div>
  </div>
</template>
