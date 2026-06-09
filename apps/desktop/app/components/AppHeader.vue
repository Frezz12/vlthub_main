<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useDMStore } from '~/stores/dm'
import { audioState } from '~/utils/audioState'
import { toggleAudio as globalToggle, seekAudio as globalSeek, cycleSpeed as globalCycleSpeed, setVolume as globalSetVolume, stopAudio as globalStop } from '~/utils/audioService'

const auth = useAuthStore()
const dm = useDMStore()
const notifications = useNotificationsStore()
const { isDark, toggle } = useTheme()
const showVolume = ref(false)
const showGlobalVolume = ref(false)

const AUDIO_KEY = 'dm_audio_state'
const speedOptions = [0.5, 1, 1.5, 2]
const showSpeedMenu = ref(false)
let saveTimer: ReturnType<typeof setTimeout> | null = null

const currentTrackIndex = computed(() =>
  dm.audioTrackList.findIndex(t => t.id === dm.playingAudioId),
)

const globalProgress = computed(() =>
  audioState.duration ? audioState.currentTime / audioState.duration : 0,
)

function onGlobalSeek(e: Event) {
  const input = e.target as HTMLInputElement
  globalSeek(parseFloat(input.value))
}

function onGlobalVolume(e: Event) {
  const v = parseFloat((e.target as HTMLInputElement).value)
  audioState.volume = v
  globalSetVolume(v)
}

function playTrack(index: number) {
  const track = dm.audioTrackList[index]
  if (track && track.filePath) {
    dm.toggleAudio(track.id, track.filePath)
  }
}

function playNext() {
  const idx = currentTrackIndex.value
  if (idx < dm.audioTrackList.length - 1) playTrack(idx + 1)
}

function playPrev() {
  const idx = currentTrackIndex.value
  if (idx > 0) playTrack(idx - 1)
}

function saveAudio() {
  try {
    const data = {
      playingAudioId: dm.playingAudioId || '',
      audioMsgSenderId: dm.audioMsgSenderId,
      audioMsgFileName: dm.audioMsgFileName,
      audioMsgFilePath: dm.audioMsgFilePath,
      audioProgress: dm.audioProgress,
      audioDuration: dm.audioDuration,
      playbackSpeed: dm.playbackSpeed,
      volume: dm.volume,
    }
    localStorage.setItem(AUDIO_KEY, JSON.stringify(data))
  } catch { /* ignore */ }
}

function saveAudioThrottled() {
  if (saveTimer) return
  saveTimer = setTimeout(() => {
    saveAudio()
    saveTimer = null
  }, 3000)
}

watch(
  () => [dm.playingAudioId, dm.audioPlaying, dm.audioProgress, dm.playbackSpeed, dm.volume],
  () => saveAudioThrottled(),
  { deep: true },
)

function formatTime(seconds: number): string {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onSeek(e: Event) {
  const input = e.target as HTMLInputElement
  dm.seekAudio(dm.playingAudioId!, parseFloat(input.value))
}

function onVolume(e: Event) {
  dm.setVolume(parseFloat((e.target as HTMLInputElement).value))
}

let pollTimer: ReturnType<typeof setInterval> | null = null

function closeMenus() {
  showSpeedMenu.value = false
  showVolume.value = false
}

onMounted(() => {
  document.addEventListener('click', closeMenus)
  // Restore audio state from localStorage (client-only)
  try {
    const raw = localStorage.getItem(AUDIO_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      if (data?.playingAudioId) {
        dm.$patch({
          playingAudioId: data.playingAudioId,
          audioMsgSenderId: data.audioMsgSenderId || null,
          audioMsgFileName: data.audioMsgFileName || null,
          audioMsgFilePath: data.audioMsgFilePath || null,
          audioProgress: data.audioProgress || {},
          audioDuration: data.audioDuration || {},
          playbackSpeed: data.playbackSpeed ?? 1,
          volume: data.volume ?? 1,
        })
      }
    }
  } catch { /* ignore */ }

  window.addEventListener('beforeunload', saveAudio)
  if (auth.isAuthenticated) {
    notifications.fetchNotifications()
    pollTimer = setInterval(() => {
      notifications.fetchNotifications()
    }, 30000)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenus)
  window.removeEventListener('beforeunload', saveAudio)
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

    <!-- Center: audio player -->
    <div class="flex-1 flex items-center justify-center min-w-0 h-full">
      <Transition name="dm-audio">
          <div
            v-if="dm.playingAudioId"
            class="flex items-center gap-3 px-4 h-[42px] rounded-xl bg-surface/90 border border-border/20 shadow-sm transition-all duration-300 w-full max-w-xl"
          >
            <!-- Play button with progress ring -->
            <div class="relative shrink-0">
              <button
                class="w-7 h-7 rounded-full flex items-center justify-center shrink-0 transition-all duration-200 active:scale-90 bg-primary/10 text-primary hover:bg-primary/18"
                @click="dm.toggleAudio(dm.playingAudioId, dm.audioMsgFilePath || '')"
              >
                <svg v-if="dm.audioPlaying" class="w-[10px] h-[10px]" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                </svg>
                <svg v-else class="w-[11px] h-[11px] ml-[1px]" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8.75 5.5a.75.75 0 0 0-1.125.65v11.7a.75.75 0 0 0 1.125.65l10.125-5.85a.75.75 0 0 0 0-1.3L8.75 5.5Z"/>
                </svg>
              </button>
              <!-- Circular progress ring -->
              <svg
                v-if="dm.audioPlaying && dm.audioDuration[dm.playingAudioId!]"
                class="absolute inset-0 w-7 h-7 -rotate-90 pointer-events-none"
                viewBox="0 0 40 40"
              >
                <circle
                  cx="20" cy="20" r="17"
                  fill="none"
                  class="chat-audio-progress-bg"
                  stroke-width="2.5"
                />
                <circle
                  cx="20" cy="20" r="17"
                  fill="none"
                  stroke="var(--color-primary)"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  :stroke-dasharray="2 * Math.PI * 17"
                  :stroke-dashoffset="2 * Math.PI * 17 * (1 - dm.calcProgress(dm.playingAudioId!))"
                  class="transition-all duration-300"
                />
              </svg>
            </div>

            <!-- Info column -->
            <div class="min-w-0 flex-[2]">
              <p class="text-xs font-medium truncate text-foreground">{{ dm.audioMsgFileName || '' }}</p>
              <div class="flex items-center gap-1.5 mt-0.5">
              <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums text-secondary/60 w-7 text-right">{{ formatTime(dm.audioProgress[dm.playingAudioId!] || 0) }}</span>
              <div class="flex-1 relative h-1.5 rounded-full bg-primary/10 min-w-[40px]">
                <div
                  class="absolute inset-y-0 left-0 rounded-full transition-all duration-300 bg-primary"
                  :style="{ width: (dm.calcProgress(dm.playingAudioId!) * 100) + '%' }"
                />
                <input
                  type="range"
                  min="0"
                  :max="dm.audioDuration[dm.playingAudioId!] || 0"
                  :value="dm.audioProgress[dm.playingAudioId!] || 0"
                  class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  @input="onSeek($event)"
                />
              </div>
              <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums text-secondary/60 w-7">{{ formatTime(dm.audioDuration[dm.playingAudioId!] || 0) }}</span>
            </div>
          </div>

          <!-- Controls -->
          <div class="flex items-center gap-0.5 shrink-0">
            <button
              class="w-6 h-6 rounded-md flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/40 hover:text-foreground relative"
              title="Громкость"
              @click.stop="showVolume = !showVolume"
            >
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path v-if="dm.volume === 0" stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM23 9l-6 6M17 9l6 6" />
                <path v-else-if="dm.volume < 0.5" stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 010 7.07" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14" />
              </svg>
              <div
                v-if="showVolume"
                class="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-surface border border-border/40 rounded-xl p-3 shadow-lg z-50"
                @click.stop
              >
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  :value="dm.volume"
                  class="volume-slider w-20 h-1"
                  @input="onVolume($event)"
                />
              </div>
            </button>

            <button
              class="w-6 h-6 rounded-md flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/40 hover:text-foreground"
              :class="{ 'opacity-30 pointer-events-none': currentTrackIndex <= 0 }"
              title="Предыдущий трек"
              @click="playPrev()"
            >
              <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
              </svg>
            </button>

            <button
              class="w-6 h-6 rounded-md flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/40 hover:text-foreground"
              :class="{ 'opacity-30 pointer-events-none': currentTrackIndex >= dm.audioTrackList.length - 1 }"
              title="Следующий трек"
              @click="playNext()"
            >
              <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18 6v12h-2V6zm-3.5 6l-8.5 6V6z"/>
              </svg>
            </button>

            <button
              class="min-w-[24px] h-6 flex items-center justify-center text-[10px] font-bold leading-none px-1 rounded-md transition-all hover:scale-105 active:scale-95 tabular-nums text-secondary/40 hover:text-foreground shrink-0 relative"
              @click.stop="showSpeedMenu = !showSpeedMenu"
              title="Скорость воспроизведения"
            >{{ dm.playbackSpeed }}x
              <Transition name="dm-audio">
                <div
                  v-if="showSpeedMenu"
                  class="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-surface border border-border/40 rounded-xl p-1 shadow-lg z-50 min-w-[64px]"
                  @click.stop
                >
                  <button
                    v-for="sp in speedOptions"
                    :key="sp"
                    class="w-full text-[10px] font-bold leading-none px-3 py-1.5 rounded-lg transition-all tabular-nums"
                    :class="sp === dm.playbackSpeed ? 'bg-primary text-white' : 'text-secondary/70 hover:text-foreground hover:bg-hover'"
                    @click="dm.setSpeed(sp); showSpeedMenu = false"
                  >{{ sp }}x</button>
                </div>
              </Transition>
            </button>

            <button
              class="w-6 h-6 rounded-md flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/30 hover:text-secondary/60"
              @click="dm.stopAudio()"
              title="Закрыть"
            >
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </Transition>
      <!-- Global audio player -->
      <Transition name="dm-audio">
        <div
          v-if="audioState.src"
          class="flex items-center gap-2 w-full max-w-md"
        >
          <div class="relative shrink-0">
            <button
              class="w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 active:scale-95 bg-primary/10 text-primary hover:bg-primary/20"
              @click="globalToggle()"
            >
              <svg v-if="audioState.playing" class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
              </svg>
              <svg v-else class="w-4 h-4 ml-[1px]" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </button>
            <svg
              v-if="audioState.playing && audioState.duration"
              class="absolute inset-0 w-9 h-9 -rotate-90 pointer-events-none"
              viewBox="0 0 40 40"
            >
              <circle cx="20" cy="20" r="17" fill="none" class="chat-audio-progress-bg" stroke-width="2.5" />
              <circle cx="20" cy="20" r="17" fill="none" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" :stroke-dasharray="2 * Math.PI * 17" :stroke-dashoffset="2 * Math.PI * 17 * (1 - globalProgress)" class="transition-all duration-300" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-semibold truncate text-foreground">{{ audioState.title }}</p>
            <div class="flex items-center gap-1.5 mt-0.5">
              <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums text-secondary/60 w-7 text-right">{{ formatTime(audioState.currentTime) }}</span>
              <div class="flex-1 relative h-1.5 rounded-full bg-primary/10 min-w-[40px]">
                <div class="absolute inset-y-0 left-0 rounded-full transition-all duration-300 bg-primary" :style="{ width: (globalProgress * 100) + '%' }" />
                <input type="range" min="0" :max="audioState.duration || 0" :value="audioState.currentTime" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" @input="onGlobalSeek($event)" />
              </div>
              <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums text-secondary/60 w-7">{{ formatTime(audioState.duration) }}</span>
            </div>
          </div>
          <div class="flex items-center gap-0.5 shrink-0">
            <button
              class="w-6 h-6 rounded-md flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/40 hover:text-foreground relative"
              title="Громкость"
              @click.stop="showGlobalVolume = !showGlobalVolume"
            >
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path v-if="audioState.volume === 0" stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM23 9l-6 6M17 9l6 6" />
                <path v-else-if="audioState.volume < 0.5" stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 010 7.07" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14" />
              </svg>
              <div
                v-if="showGlobalVolume"
                class="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-surface border border-border/40 rounded-xl p-3 shadow-lg z-50"
                @click.stop
              >
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  :value="audioState.volume"
                  class="volume-slider w-20 h-1"
                  @input="onGlobalVolume($event)"
                />
              </div>
            </button>
            <button class="min-w-[24px] h-6 flex items-center justify-center text-[10px] font-bold leading-none px-1 rounded-md transition-all hover:scale-105 active:scale-95 tabular-nums text-secondary/40 hover:text-foreground shrink-0" @click="globalCycleSpeed()" title="Скорость воспроизведения">{{ audioState.speed }}x</button>
            <button class="w-6 h-6 rounded-md flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/30 hover:text-secondary/60" @click="globalStop()" title="Закрыть">
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
        </div>
      </Transition>
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

<style scoped>
.dm-audio-enter-active,
.dm-audio-leave-active {
  transition: all 0.25s ease;
}
.dm-audio-enter-from,
.dm-audio-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
.volume-slider {
  -webkit-appearance: none;
  appearance: none;
  outline: none;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-text) 15%, transparent);
  cursor: pointer;
}
.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-surface);
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  transition: transform 0.1s ease;
}
.volume-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}
.volume-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-surface);
}
</style>
