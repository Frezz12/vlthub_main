<script setup lang="ts">
interface Props {
  src: string
  title?: string
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{ delete: [] }>()

const audioRef = ref<HTMLAudioElement | null>(null)
const playing = ref(false)
const loading = ref(true)
const error = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(1)

function togglePlay() {
  if (!audioRef.value || error.value) return
  if (playing.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play().catch(() => { error.value = true })
  }
}

function onTimeUpdate() {
  if (!audioRef.value) return
  currentTime.value = audioRef.value.currentTime
}

function onLoaded() {
  if (!audioRef.value) return
  loading.value = false
  error.value = false
  duration.value = audioRef.value.duration || 0
}

function onError() {
  loading.value = false
  error.value = true
  playing.value = false
}

function seek(e: MouseEvent) {
  if (!audioRef.value || !duration.value) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const pct = (e.clientX - rect.left) / rect.width
  audioRef.value.currentTime = pct * duration.value
}

function setVolume(e: Event) {
  const v = parseFloat((e.target as HTMLInputElement).value)
  volume.value = v
  if (audioRef.value) audioRef.value.volume = v
}

function formatTime(s: number) {
  if (!s || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

const progress = computed(() => (duration.value ? (currentTime.value / duration.value) * 100 : 0))
</script>

<template>
  <div class="flex items-center gap-2 py-1.5 group">
    <audio
      ref="audioRef"
      :src="src"
      preload="auto"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoaded"
      @loadeddata="onLoaded"
      @canplay="onLoaded"
      @error="onError"
      @ended="playing = false; loading = false"
      @play="playing = true; loading = false"
      @pause="playing = false"
    />

    <button
      class="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center shrink-0 hover:bg-primary/90 transition-colors disabled:opacity-50"
      :disabled="loading || error"
      @click="togglePlay"
    >
      <svg v-if="loading" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <svg v-else-if="error" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <svg v-else-if="playing" class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
      </svg>
      <svg v-else class="w-3.5 h-3.5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M8 5v14l11-7z" />
      </svg>
    </button>

    <div class="flex-1 min-w-0">
      <div class="text-xs text-secondary truncate mb-0.5">{{ title || 'Превью' }}</div>
      <div
        class="h-1.5 bg-btn-secondary rounded-full cursor-pointer hover:h-2 transition-all"
        @click="seek"
      >
        <div
          class="h-full bg-primary rounded-full transition-all duration-100"
          :style="{ width: error ? '0%' : `${progress}%` }"
        />
      </div>
    </div>

    <div class="flex items-center gap-2 shrink-0">
      <div class="hidden group-hover:flex items-center gap-1">
        <svg class="w-3.5 h-3.5 text-secondary" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0014 8.5v7a4.49 4.49 0 002.5-3.5zM14 3.23v2.06a7.007 7.007 0 010 13.42v2.06A9.01 9.01 0 0014 3.23z" />
        </svg>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          :value="volume"
          class="w-16 h-1 accent-primary"
          @input="setVolume"
        />
      </div>

      <span class="text-xs text-secondary tabular-nums w-20 text-right">
        {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
      </span>

      <button
        class="opacity-0 group-hover:opacity-100 text-secondary hover:text-danger transition-all p-1 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Удалить"
        :disabled="disabled"
        @click="emit('delete')"
      >
        <svg v-if="disabled" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>
</template>
