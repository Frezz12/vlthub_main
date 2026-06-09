<template>
  <Transition name="dm-audio">
    <div
      v-if="dm.playingAudioId"
      class="border-t border-border/20 bg-surface/70 backdrop-blur-2xl"
    >
      <div class="max-w-screen-xl mx-auto flex items-center gap-3 px-5 py-2.5">
        <!-- Play button with progress ring -->
        <div class="relative shrink-0">
          <button
            class="w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 active:scale-90 bg-primary/10 text-primary hover:bg-primary/18"
            @click="dm.toggleAudio(dm.playingAudioId, dm.audioMsgFilePath || '')"
          >
            <svg v-if="dm.audioPlaying" class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
            </svg>
            <svg v-else class="w-[18px] h-[18px] ml-px" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8.75 5.5a.75.75 0 0 0-1.125.65v11.7a.75.75 0 0 0 1.125.65l10.125-5.85a.75.75 0 0 0 0-1.3L8.75 5.5Z"/>
            </svg>
          </button>
          <!-- Circular progress ring -->
          <svg
            v-if="dm.audioPlaying && dm.audioDuration[dm.playingAudioId!]"
            class="absolute inset-0 w-9 h-9 -rotate-90 pointer-events-none"
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
        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold leading-tight truncate text-foreground">{{ dm.audioMsgFileName || '' }}</p>
          <div class="flex items-center gap-2 mt-1">
            <span class="text-[11px] leading-none shrink-0 font-medium tabular-nums text-secondary/50">{{ formatTime(dm.audioProgress[dm.playingAudioId!] || 0) }}</span>
            <div class="flex-1 relative h-[6px] rounded-full bg-primary/10">
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
            <span class="text-[11px] leading-none shrink-0 font-medium tabular-nums text-secondary/50">{{ formatTime(dm.audioDuration[dm.playingAudioId!] || 0) }}</span>
          </div>
        </div>

        <!-- Controls -->
        <div class="flex items-center gap-0.5 shrink-0">
          <button
            class="relative w-8 h-8 rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/40 hover:text-foreground"
            title="Громкость"
            @click="showVolume = !showVolume"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path v-if="dm.volume === 0" stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM23 9l-6 6M17 9l6 6" />
              <path v-else-if="dm.volume < 0.5" stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 010 7.07" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14" />
            </svg>
            <div
              v-if="showVolume"
              class="absolute bottom-full mb-2.5 left-1/2 -translate-x-1/2 bg-surface/95 border border-border/20 rounded-2xl p-3.5 shadow-2xl backdrop-blur-2xl"
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
            class="text-[11px] font-bold leading-none px-2 py-1.5 rounded-xl transition-all hover:scale-105 active:scale-95 tabular-nums text-secondary/40 hover:text-foreground"
            @click="dm.cycleSpeed()"
            title="Скорость воспроизведения"
          >{{ dm.playbackSpeed }}x</button>

          <button
            class="w-8 h-8 rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-secondary/30 hover:text-secondary/60"
            @click="dm.stopAudio()"
            title="Закрыть"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDMStore } from '~/stores/dm'

const dm = useDMStore()
const showVolume = ref(false)

function formatTime(seconds: number): string {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onSeek(e: Event) {
  const input = e.target as HTMLInputElement
  const time = parseFloat(input.value)
  if (dm.playingAudioId) {
    dm.seekAudio(dm.playingAudioId, time)
  }
}

function onVolume(e: Event) {
  const input = e.target as HTMLInputElement
  dm.setVolume(parseFloat(input.value))
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
.volume-slider {
  -webkit-appearance: none;
  appearance: none;
  outline: none;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-text) 12%, transparent);
  cursor: pointer;
}
.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2.5px solid var(--color-surface);
  box-shadow: 0 1px 4px rgba(0,0,0,0.12);
  transition: transform 0.1s ease;
}
.volume-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}
.volume-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2.5px solid var(--color-surface);
}
</style>
