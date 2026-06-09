<script setup lang="ts">
const { allDownloads, removeDownload } = useDownloadProgress()

const dismissTimers = new Map<string, ReturnType<typeof setTimeout>>()

watch(allDownloads, (list) => {
  for (const d of list) {
    if ((d.status === 'complete' || d.status === 'error') && !dismissTimers.has(d.id)) {
      dismissTimers.set(d.id, setTimeout(() => {
        removeDownload(d.id)
        dismissTimers.delete(d.id)
      }, 5000))
    }
  }
}, { deep: true })

onUnmounted(() => {
  for (const t of dismissTimers.values()) clearTimeout(t)
  dismissTimers.clear()
})

function dismiss(id: string) {
  const t = dismissTimers.get(id)
  if (t) { clearTimeout(t); dismissTimers.delete(id) }
  const entry = allDownloads.value.find(d => d.id === id)
  if (entry && entry.status === 'downloading') {
    entry.onCancel?.()
  }
  removeDownload(id)
}

const phaseLabel: Record<string, string> = {
  downloading: 'Скачивание',
  complete: 'Готово',
  error: 'Ошибка',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-4 right-4 z-[200] flex flex-col gap-2 max-w-sm pointer-events-none">
      <TransitionGroup name="upload-slide">
        <div
          v-for="dl in allDownloads"
          :key="dl.id"
          class="pointer-events-auto bg-[#1c1c1e] border border-white/10 rounded-xl shadow-2xl overflow-hidden transition-all duration-300 dark:border-transparent"
          :class="{
            'border-red-500/40': dl.status === 'error',
            'border-emerald-500/40': dl.status === 'complete',
            'border-white/10': dl.status !== 'error' && dl.status !== 'complete',
          }"
        >
          <div class="flex items-start gap-3 p-4">
            <div
              class="shrink-0 w-9 h-9 rounded-full flex items-center justify-center"
              :class="{
                'bg-blue-500/20 text-blue-400': dl.status === 'downloading',
                'bg-emerald-500/20 text-emerald-400': dl.status === 'complete',
                'bg-red-500/20 text-red-400': dl.status === 'error',
              }"
            >
              <svg v-if="dl.status === 'downloading'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <svg v-else-if="dl.status === 'complete'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>

            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-2">
                <p class="text-sm font-semibold text-white truncate">{{ dl.fileName }}</p>
                <span
                  class="text-xs font-medium shrink-0"
                  :class="{
                    'text-blue-400': dl.status === 'downloading',
                    'text-emerald-400': dl.status === 'complete',
                    'text-red-400': dl.status === 'error',
                  }"
                >{{ phaseLabel[dl.status] || dl.status }}</span>
              </div>

              <div v-if="dl.status === 'downloading'" class="mt-2">
                <div class="flex items-center justify-between text-xs text-white/50 mb-1">
                  <span>{{ dl.progress }}%</span>
                </div>
                <div class="h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-300 bg-blue-500"
                    :style="{ width: dl.progress + '%' }"
                  />
                </div>
              </div>

              <p v-if="dl.status === 'error' && dl.errorMessage" class="mt-1 text-xs text-red-400/80 break-words">
                {{ dl.errorMessage }}
              </p>
            </div>

            <button
              type="button"
              class="shrink-0 rounded-md text-white/30 hover:text-white/60 hover:bg-white/5 transition-colors"
              :class="dl.status === 'downloading' ? 'px-2 py-1 text-xs text-danger/70 hover:text-danger' : 'p-1'"
              @click="dismiss(dl.id)"
            >
              <span v-if="dl.status === 'downloading'">Отмена</span>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.upload-slide-enter-active,
.upload-slide-leave-active {
  transition: all 0.3s ease;
}
.upload-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.upload-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
.upload-slide-move {
  transition: transform 0.3s ease;
}
</style>
