<script setup lang="ts">
interface MediaItem {
  url: string
  fileName: string
  filePath: string
  fileType?: string
}

interface Props {
  modelValue: boolean
  media: MediaItem[]
  initialIndex?: number
}

const props = withDefaults(defineProps<Props>(), { initialIndex: 0 })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'save-as': [filePath: string, fileName: string]
}>()

const currentIndex = ref(props.initialIndex)
const imgLoading = ref(true)
const vidEl = ref<HTMLVideoElement | null>(null)
const isVideo = computed(() => {
  const name = currentMedia.value?.fileName ?? ''
  const ext = name.split('.').pop()?.toLowerCase()
  return ['mp4', 'webm', 'mov', 'avi', 'mkv', 'm4v', '3gp'].includes(ext || '')
})
const currentMedia = computed(() => props.media[currentIndex.value] ?? null)

watch(() => props.modelValue, (val) => {
  if (val) {
    currentIndex.value = props.initialIndex
    imgLoading.value = true
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

watch(() => props.initialIndex, (idx) => {
  currentIndex.value = idx
  imgLoading.value = true
})

function close() {
  emit('update:modelValue', false)
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    imgLoading.value = true
  }
}

function next() {
  if (currentIndex.value < props.media.length - 1) {
    currentIndex.value++
    imgLoading.value = true
  }
}

function onBackdropClick(e: MouseEvent) {
  if ((e.target as HTMLElement)?.classList.contains('lightbox-backdrop')) close()
}

function onKeydown(e: KeyboardEvent) {
  if (!props.modelValue) return
  if (e.key === 'Escape') close()
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
  if (e.key === ' ') { e.preventDefault(); return }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

function formatFileName(name: string): string {
  return name.length > 40 ? name.slice(0, 37) + '...' : name
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue && currentMedia"
        class="lightbox-backdrop fixed inset-0 z-[100] flex flex-col bg-black/85 backdrop-blur-sm"
        @click="onBackdropClick"
      >
        <!-- Top bar -->
        <div class="flex items-center justify-between px-4 py-3 shrink-0">
          <p class="text-sm text-white/70 truncate">{{ formatFileName(currentMedia.fileName) }}</p>
          <div class="flex items-center gap-2">
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-white/50 hover:text-white hover:bg-white/10 transition-all"
              @click.stop="emit('save-as', currentMedia.filePath, currentMedia.fileName)"
              title="Сохранить как"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </button>
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-white/50 hover:text-white hover:bg-white/10 transition-all"
              @click="close"
              title="Закрыть"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Media area -->
        <div class="flex-1 flex items-center justify-center relative min-h-0 px-4">
          <!-- Prev arrow -->
          <button
            v-if="media.length > 1 && currentIndex > 0"
            class="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center bg-black/40 text-white/70 hover:bg-black/60 hover:text-white transition-all z-10"
            @click.stop="prev"
            title="Предыдущее"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <!-- Image -->
          <img
            v-if="!isVideo"
            :src="currentMedia.url"
            :alt="currentMedia.fileName"
            class="max-w-full max-h-full object-contain rounded-lg select-none"
            :class="imgLoading ? 'opacity-0' : 'opacity-100'"
            style="transition: opacity 0.2s"
            @load="imgLoading = false"
            @error="imgLoading = false"
            draggable="false"
          />

          <!-- Video -->
          <video
            v-else
            ref="vidEl"
            :src="currentMedia.url"
            class="max-w-full max-h-full rounded-lg"
            controls
            autoplay
            playsinline
            preload="auto"
          ></video>

          <!-- Loading spinner -->
          <div
            v-if="imgLoading && !isVideo"
            class="absolute inset-0 flex items-center justify-center"
          >
            <div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>

          <!-- Next arrow -->
          <button
            v-if="media.length > 1 && currentIndex < media.length - 1"
            class="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center bg-black/40 text-white/70 hover:bg-black/60 hover:text-white transition-all z-10"
            @click.stop="next"
            title="Следующее"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <!-- Bottom counter -->
        <div v-if="media.length > 1" class="flex items-center justify-center gap-1.5 px-4 py-3 shrink-0">
          <button
            v-for="(_, i) in media"
            :key="i"
            class="w-1.5 h-1.5 rounded-full transition-all"
            :class="i === currentIndex ? 'bg-white w-3' : 'bg-white/30 hover:bg-white/50'"
            @click="currentIndex = i; imgLoading = true"
          />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
