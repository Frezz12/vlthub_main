<script setup lang="ts">
import { audioState } from '~/utils/audioState'
import { playAudio, toggleAudio, seekAudio, setSpeed, setVolume, stopAudio } from '~/utils/audioService'

interface Props {
  src: string
  title?: string
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{ delete: [] }>()

const localPlaying = ref(false)
const localCurrentTime = ref(0)
const localDuration = ref(0)
const localSpeed = ref(1)
const speeds = [0.5, 1, 1.5, 2]

function play() {
  localPlaying.value = true
  localCurrentTime.value = 0
  localDuration.value = 0
  localSpeed.value = audioState.speed
  playAudio(props.src, props.title || 'Превью')
}

function toggle() {
  if (audioState.src === props.src && audioState.playing) {
    toggleAudio()
  } else {
    play()
  }
}

function onSeek(e: Event) {
  const input = e.target as HTMLInputElement
  seekAudio(parseFloat(input.value))
}

function cycle() {
  const idx = speeds.indexOf(localSpeed.value)
  localSpeed.value = speeds[(idx + 1) % speeds.length]
  setSpeed(localSpeed.value)
}

watch(() => audioState.src, (src) => {
  if (src !== props.src) {
    localPlaying.value = false
  }
})

watch(() => audioState.playing, (playing) => {
  if (audioState.src === props.src) {
    localPlaying.value = playing
  }
})

watch(() => audioState.currentTime, (t) => {
  if (audioState.src === props.src) {
    localCurrentTime.value = t
  }
})

watch(() => audioState.duration, (d) => {
  if (audioState.src === props.src) {
    localDuration.value = d
  }
})

const progress = computed(() =>
  localDuration.value ? (localCurrentTime.value / localDuration.value) * 100 : 0,
)

function formatTime(s: number) {
  if (!s || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}
</script>

<template>
  <div class="chat-audio-player">
    <div class="flex items-center gap-2.5 px-3.5 py-2.5">
      <div class="relative shrink-0">
        <button
          class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 active:scale-95 bg-primary/10 text-primary hover:bg-primary/20 disabled:opacity-50"
          @click="toggle"
        >
          <svg v-if="localPlaying" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
          </svg>
          <svg v-else class="w-4.5 h-4.5 ml-[1px]" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        </button>
        <svg
          v-if="localPlaying && localDuration"
          class="absolute inset-0 w-10 h-10 -rotate-90 pointer-events-none"
          viewBox="0 0 40 40"
        >
          <circle cx="20" cy="20" r="17" fill="none" class="chat-audio-progress-bg" stroke-width="2.5" />
          <circle cx="20" cy="20" r="17" fill="none" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" :stroke-dasharray="2 * Math.PI * 17" :stroke-dashoffset="2 * Math.PI * 17 * (1 - progress / 100)" class="transition-all duration-300" />
        </svg>
      </div>

      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold truncate leading-tight text-foreground">{{ title || 'Превью' }}</p>
        <div class="flex items-center gap-2 mt-1.5">
          <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums text-secondary">{{ formatTime(localCurrentTime) }}</span>
          <div class="flex-1 relative h-2 rounded-full bg-primary/10">
            <div class="absolute inset-y-0 left-0 rounded-full transition-all duration-300 bg-primary" :style="{ width: `${progress}%` }" />
            <input type="range" min="0" :max="localDuration || 0" :value="localCurrentTime" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" @input="onSeek" />
          </div>
          <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums text-secondary">{{ formatTime(localDuration) }}</span>
        </div>
      </div>

      <div class="flex flex-col items-center gap-1 shrink-0">
        <button class="text-[10px] font-bold leading-none px-2 py-1.5 rounded-md transition-all duration-200 hover:scale-105 active:scale-95 tabular-nums text-secondary hover:text-primary hover:bg-primary/10" title="Скорость воспроизведения" @click="cycle">{{ localSpeed }}x</button>
        <button class="w-7 h-7 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95 text-secondary/60 hover:text-danger hover:bg-danger/10 disabled:opacity-50 disabled:cursor-not-allowed" title="Удалить" :disabled="disabled" @click="emit('delete')">
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
  </div>
</template>
