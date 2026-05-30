<script setup lang="ts">
import { formatError } from '~/utils/formatError'
const auth = useAuthStore()
const route = useRoute()

const appVersion = ref('0.8.12')

const isAuthPage = computed(() =>
  ['/login', '/register', '/forgot-password', '/reset-password', '/confirm-email'].includes(route.path),
)

const showSidebar = computed(() => !isAuthPage.value && auth.isAuthenticated)
const isDownloadPage = computed(() => route.path === '/download')
const isLandingPage = computed(() => isAuthPage.value || isDownloadPage.value)

type UpdateState = 'idle' | 'checking' | 'available' | 'downloading' | 'ready' | 'error'

const updateState = ref<UpdateState>('idle')
const updateVersion = ref('')
const downloadProgress = ref<{ current: number; total: number } | null>(null)
const updateError = ref('')
const showUpdateModal = ref(false)

let updateHandle: any = null

onMounted(async () => {
  useTheme().init()

  if ('__TAURI_INTERNALS__' in window) {
    const { onOpenUrl, getCurrent } = await import('@tauri-apps/plugin-deep-link')

    const urls = await getCurrent()
    if (urls?.length) {
      const match = urls[0].match(/vlthub:\/\/shared\/(.+)/)
      if (match) navigateTo(`/shared/${match[1]}`)
    }

    await onOpenUrl((urls) => {
      for (const url of urls) {
        const match = url.match(/vlthub:\/\/shared\/(.+)/)
        if (match) {
          navigateTo(`/shared/${match[1]}`)
          return
        }
      }
    })

    silentCheck()

    try {
      const { getVersion } = await import('@tauri-apps/api/app')
      appVersion.value = await getVersion()
    } catch {}
  }
})

async function silentCheck() {
  updateState.value = 'checking'
  try {
    const { check } = await import('@tauri-apps/plugin-updater')
    updateHandle = await check()
    if (updateHandle?.available) {
      updateVersion.value = updateHandle.version
      updateState.value = 'available'
    } else {
      updateState.value = 'idle'
    }
  } catch {
    updateState.value = 'idle'
  }
}

function openUpdate() {
  if (updateState.value === 'available') {
    showUpdateModal.value = true
  }
}

async function startDownload() {
  if (!updateHandle) return
  updateState.value = 'downloading'
  downloadProgress.value = null
  try {
    await updateHandle.downloadAndInstall((event: any) => {
      if (event.event === 'DownloadProgress') {
        downloadProgress.value = {
          current: event.data.chunkLength || 0,
          total: event.data.contentLength || 0,
        }
      }
    })
    updateState.value = 'ready'
  } catch (e: any) {
    updateError.value = formatError(e)
    console.error('[updater]', e)
    updateState.value = 'error'
  }
}

function closeModal() {
  showUpdateModal.value = false
}

const progressPercent = computed(() => {
  if (!downloadProgress.value || !downloadProgress.value.total) return 0
  return Math.round((downloadProgress.value.current / downloadProgress.value.total) * 100)
})

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'F11') {
    e.preventDefault()
    if ('__TAURI_INTERNALS__' in window) {
      import('@tauri-apps/api/window').then(async ({ getCurrentWindow }) => {
        const win = getCurrentWindow()
        const isFull = await win.isFullscreen()
        await win.setFullscreen(!isFull)
      })
    } else {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen()
      } else {
        document.exitFullscreen()
      }
    }
  }
}

if (import.meta.client) {
  window.addEventListener('keydown', onKeydown)
}
</script>

<template>
  <div class="min-h-screen app-bg transition-colors duration-200">
    <AppHeader v-if="!isLandingPage" />
    <div class="flex" :class="isLandingPage ? '' : 'pt-14'">
      <AppSidebar v-if="showSidebar" />
      <main
        class="flex-1 transition-all duration-300"
        :class="showSidebar ? 'ml-16' : ''"
      >
        <div v-if="isAuthPage" class="flex items-center justify-center min-h-[calc(100vh-3.5rem)]">
          <slot />
        </div>
        <slot v-else />
      </main>
    </div>
    <UploadProgressToast />
    <DownloadProgressToast />
    <button
      v-if="!isDownloadPage"
      class="fixed bottom-4 right-4 z-[200] text-[11px] select-none transition-colors flex items-center gap-1.5"
      :class="updateState === 'available' ? 'text-primary/60 hover:text-primary cursor-pointer' : 'text-white/20 pointer-events-none'"
      @click="openUpdate"
    >
      <span v-if="updateState === 'available'" class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
      {{ appVersion }}
    </button>
  </div>

  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="showUpdateModal"
        class="fixed inset-0 z-[300] flex items-center justify-center bg-black/40 backdrop-blur-sm"
        @click.self="closeModal"
      >
        <Transition name="slide" appear>
          <div
            v-if="showUpdateModal"
            class="card w-full max-w-sm mx-4 p-6"
          >
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-base font-semibold">Обновление VLTHub</h2>
              <button class="text-secondary hover:text-foreground transition-colors" @click="closeModal">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <template v-if="updateState === 'available'">
              <p class="text-sm text-secondary mb-4">
                Доступна новая версия <strong class="text-foreground">{{ updateVersion }}</strong>.
                Хотите обновить сейчас?
              </p>
              <div class="flex gap-2 justify-end">
                <button class="btn btn-secondary text-sm" @click="closeModal">Позже</button>
                <button class="btn btn-primary text-sm" @click="startDownload">Обновить</button>
              </div>
            </template>

            <template v-else-if="updateState === 'downloading'">
              <p class="text-sm text-secondary mb-3">Загрузка обновления...</p>
              <div class="w-full h-2 bg-border rounded-full overflow-hidden">
                <div
                  class="h-full bg-primary rounded-full transition-all duration-300"
                  :style="{ width: `${progressPercent}%` }"
                />
              </div>
              <p class="text-xs text-secondary mt-2 text-right">{{ progressPercent }}%</p>
            </template>

            <template v-else-if="updateState === 'ready'">
              <p class="text-sm text-secondary mb-4">
                Обновление загружено. Приложение перезапустится для установки.
              </p>
              <div class="flex justify-end">
                <button class="btn btn-primary text-sm" @click="closeModal">OK</button>
              </div>
            </template>

            <template v-else-if="updateState === 'error'">
              <p class="text-sm text-red-500 mb-4">{{ updateError }}</p>
              <div class="flex justify-end">
                <button class="btn btn-primary text-sm" @click="closeModal">Закрыть</button>
              </div>
            </template>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
