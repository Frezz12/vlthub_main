<template>
  <Transition name="dm-audio">
    <div
      v-if="state.src"
      class="border-t border-border/30 bg-surface/60"
    >
      <div class="max-w-screen-xl mx-auto flex items-center gap-2.5 px-4 py-2">
        <div class="relative shrink-0">
          <button
            class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 active:scale-95 bg-primary/10 text-primary hover:bg-primary/20"
            @click="state.controls?.toggle()"
          >
            <svg v-if="state.playing" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
            </svg>
            <svg v-else class="w-4.5 h-4.5 ml-[1px]" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </button>
          <svg
            v-if="state.playing && state.duration"
            class="absolute inset-0 w-10 h-10 -rotate-90 pointer-events-none"
            viewBox="0 0 40 40"
          >
            <circle cx="20" cy="20" r="17" fill="none" class="chat-audio-progress-bg" stroke-width="2.5" />
            <circle
              cx="20" cy="20" r="17" fill="none" stroke="var(--color-primary)" stroke-width="2.5"
              stroke-linecap="round"
              :stroke-dasharray="2 * Math.PI * 17"
              :stroke-dashoffset="2 * Math.PI * 17 * (1 - progress)"
              class="transition-all duration-300"
            />
          </svg>
        </div>

        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold leading-tight truncate text-foreground">{{ state.title }}</p>
          <div class="flex items-center gap-2 mt-1.5">
            <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums text-secondary">{{ formatTime(state.currentTime) }}</span>
            <div class="flex-1 relative h-2 rounded-full bg-primary/10">
              <div class="absolute inset-y-0 left-0 rounded-full transition-all duration-300 bg-primary" :style="{ width: `${progress * 100}%` }" />
              <input
                type="range" min="0" :max="state.duration || 0" :value="state.currentTime"
                class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                @input="onSeek"
              />
            </div>
            <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums text-secondary">{{ formatTime(state.duration) }}</span>
          </div>
        </div>

        <div class="flex items-center gap-1 shrink-0">
          <button
            class="text-[10px] font-bold leading-none px-1.5 py-1 rounded-lg transition-all hover:scale-105 active:scale-95 tabular-nums text-secondary/40 hover:text-foreground"
            @click="state.controls?.cycleSpeed()"
            title="Скорость воспроизведения"
          >{{ state.speed }}x</button>

          <button
            class="w-7 h-7 rounded-lg flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/30 hover:text-secondary/60"
            @click="state.controls?.stop()"
            title="Закрыть"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { audioState } from '~/utils/audioState'

const state = audioState

const progress = computed(() =>
  state.duration ? state.currentTime / state.duration : 0,
)

function onSeek(e: Event) {
  const input = e.target as HTMLInputElement
  state.controls?.seek(parseFloat(input.value))
}

function formatTime(s: number) {
  if (!s || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.dm-audio-enter-active,
.dm-audio-leave-active {
  transition: all 0.25s ease;
}
.dm-audio-enter-from,
.dm-audio-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
