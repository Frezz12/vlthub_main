<script setup lang="ts">
export interface ToastDownloadPayload {
  title: string
  fileLabel: string
  path: string
}

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
  action?: { label: string; onClick: () => void }
  download?: ToastDownloadPayload
}

const topToasts = ref<Toast[]>([])
const bottomToasts = ref<Toast[]>([])
let nextId = 0

function show(
  message: string,
  type: Toast['type'] = 'info',
  duration = 3000,
  action?: { label: string; onClick: () => void },
  position: 'top' | 'bottom' = 'top',
  download?: ToastDownloadPayload,
) {
  const id = nextId++
  const effectiveDuration = download ? Math.max(duration, 8000) : duration
  const toast: Toast = { id, message, type, action, download }
  const target = position === 'bottom' ? bottomToasts : topToasts
  target.value.push(toast)
  setTimeout(() => {
    target.value = target.value.filter((t) => t.id !== id)
  }, effectiveDuration)
}

function dismiss(id: number, position: 'top' | 'bottom') {
  const target = position === 'bottom' ? bottomToasts : topToasts
  target.value = target.value.filter((t) => t.id !== id)
}

defineExpose({ show })

const typeConfig: Record<Toast['type'], { label: string; cssVar: string; icon: string }> = {
  success: { label: 'Успешно', cssVar: '--color-success', icon: 'M5 13l4 4L19 7' },
  error: { label: 'Ошибка', cssVar: '--color-danger', icon: 'M6 18L18 6M6 6l12 12' },
  info: { label: 'Информация', cssVar: '--color-primary', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
}

const iconBg: Record<Toast['type'], string> = {
  success: 'bg-emerald-100 dark:bg-emerald-500/20',
  error: 'bg-red-100 dark:bg-red-500/20',
  info: 'bg-blue-100 dark:bg-blue-500/20',
}

const iconColor: Record<Toast['type'], string> = {
  success: 'text-emerald-700 dark:text-emerald-400',
  error: 'text-red-700 dark:text-red-400',
  info: 'text-blue-700 dark:text-blue-400',
}

function pathTail(path: string, max = 56) {
  if (path.length <= max) return path
  return `…${path.slice(-(max - 1))}`
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[100] flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      <TransitionGroup name="slide">
        <div
          v-for="toast in topToasts"
          :key="toast.id"
          class="pointer-events-auto bg-surface-elevated shadow-2xl ring-1 ring-black/5 dark:ring-white/10 transition-all duration-300 overflow-hidden rounded-xl border-l-4"
          :style="{ borderLeftColor: `var(${typeConfig[toast.type].cssVar})` }"
        >
          <template v-if="toast.download">
            <div class="flex gap-3 p-4 items-start">
              <div
                class="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
                :class="[iconBg[toast.type], iconColor[toast.type]]"
                aria-hidden="true"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-xs text-secondary font-medium uppercase tracking-wide">
                  {{ toast.download.title }}
                </p>
                <p class="text-sm font-semibold text-foreground mt-0.5 truncate">
                  {{ toast.download.fileLabel }}
                </p>
                <p class="text-xs text-secondary font-mono mt-1 break-all leading-snug">
                  {{ pathTail(toast.download.path) }}
                </p>
              </div>
              <button
                v-if="toast.action"
                type="button"
                class="shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold bg-hover hover:bg-btn-secondary-hover transition-colors text-foreground"
                @click="toast.action.onClick"
              >
                {{ toast.action.label }}
              </button>
              <button
                type="button"
                class="shrink-0 self-start -mr-1 -mt-1 p-1.5 rounded-full text-secondary hover:text-foreground hover:bg-hover transition-colors"
                @click="dismiss(toast.id, 'top')"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </template>
          <div v-else class="flex gap-3 p-4 items-start">
            <div
              class="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
              :class="[iconBg[toast.type], iconColor[toast.type]]"
              aria-hidden="true"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" :d="typeConfig[toast.type].icon" />
              </svg>
            </div>
            <div class="min-w-0 flex-1 pt-0.5">
              <p class="text-xs font-semibold uppercase tracking-wider text-secondary">
                {{ typeConfig[toast.type].label }}
              </p>
              <p class="text-sm text-foreground mt-0.5 leading-snug">
                {{ toast.message }}
              </p>
            </div>
            <div class="flex items-center gap-1 shrink-0 self-start">
              <button
                v-if="toast.action"
                type="button"
                class="rounded-lg px-3 py-1.5 text-xs font-semibold bg-hover hover:bg-btn-secondary-hover transition-colors text-foreground"
                @click="toast.action.onClick"
              >
                {{ toast.action.label }}
              </button>
              <button
                type="button"
                class="p-1.5 rounded-full text-secondary hover:text-foreground hover:bg-hover transition-colors"
                @click="dismiss(toast.id, 'top')"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      <TransitionGroup name="slide">
        <div
          v-for="toast in bottomToasts"
          :key="toast.id"
          class="pointer-events-auto bg-surface-elevated shadow-2xl ring-1 ring-black/5 dark:ring-white/10 transition-all duration-300 overflow-hidden rounded-xl border-l-4"
          :style="{ borderLeftColor: `var(${typeConfig[toast.type].cssVar})` }"
        >
          <template v-if="toast.download">
            <div class="flex gap-3 p-4 items-start">
              <div
                class="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
                :class="[iconBg[toast.type], iconColor[toast.type]]"
                aria-hidden="true"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-xs text-secondary font-medium uppercase tracking-wide">
                  {{ toast.download.title }}
                </p>
                <p class="text-sm font-semibold text-foreground mt-0.5 truncate">
                  {{ toast.download.fileLabel }}
                </p>
                <p class="text-xs text-secondary font-mono mt-1 break-all leading-snug">
                  {{ pathTail(toast.download.path) }}
                </p>
              </div>
              <button
                v-if="toast.action"
                type="button"
                class="shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold bg-hover hover:bg-btn-secondary-hover transition-colors text-foreground"
                @click="toast.action.onClick"
              >
                {{ toast.action.label }}
              </button>
              <button
                type="button"
                class="shrink-0 self-start -mr-1 -mt-1 p-1.5 rounded-full text-secondary hover:text-foreground hover:bg-hover transition-colors"
                @click="dismiss(toast.id, 'bottom')"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </template>
          <div v-else class="flex gap-3 p-4 items-start">
            <div
              class="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
              :class="[iconBg[toast.type], iconColor[toast.type]]"
              aria-hidden="true"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" :d="typeConfig[toast.type].icon" />
              </svg>
            </div>
            <div class="min-w-0 flex-1 pt-0.5">
              <p class="text-xs font-semibold uppercase tracking-wider text-secondary">
                {{ typeConfig[toast.type].label }}
              </p>
              <p class="text-sm text-foreground mt-0.5 leading-snug">
                {{ toast.message }}
              </p>
            </div>
            <div class="flex items-center gap-1 shrink-0 self-start">
              <button
                v-if="toast.action"
                type="button"
                class="rounded-lg px-3 py-1.5 text-xs font-semibold bg-hover hover:bg-btn-secondary-hover transition-colors text-foreground"
                @click="toast.action.onClick"
              >
                {{ toast.action.label }}
              </button>
              <button
                type="button"
                class="p-1.5 rounded-full text-secondary hover:text-foreground hover:bg-hover transition-colors"
                @click="dismiss(toast.id, 'bottom')"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.32s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-enter-from {
  opacity: 0;
  transform: translateX(24px) scale(0.95);
}
.slide-leave-to {
  opacity: 0;
  transform: translateX(24px) scale(0.95);
}
.slide-move {
  transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1);
}
</style>
