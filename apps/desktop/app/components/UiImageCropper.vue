<script setup lang="ts">
const props = withDefaults(defineProps<{
  image: string
  aspectRatio?: number
}>(), { aspectRatio: 3 })

const emit = defineEmits<{
  crop: [blob: Blob]
  cancel: []
}>()

const containerRef = ref<HTMLElement | null>(null)
const imgLoaded = ref(false)
const imgNaturalW = ref(0)
const imgNaturalH = ref(0)
const containerW = ref(0)
const containerH = ref(0)

// Image state
const imgScale = ref(1)
const imgOffX = ref(0)
const imgOffY = ref(0)

// Selection state (in container coords)
const selX = ref(0)
const selY = ref(0)
const selW = ref(0)
const selH = ref(0)

const dragging = ref<'image' | 'selection' | null>(null)
const resizing = ref<'tl' | 'tr' | 'bl' | 'br' | null>(null)
const dragStartX = ref(0)
const dragStartY = ref(0)
const dragInitVal = ref(0)

const minSelW = 80

function onImgLoad(e: Event) {
  const img = e.target as HTMLImageElement
  imgNaturalW.value = img.naturalWidth
  imgNaturalH.value = img.naturalHeight
  imgLoaded.value = true
  nextTick(() => {
    if (containerRef.value) {
      containerW.value = containerRef.value.offsetWidth
      containerH.value = containerRef.value.offsetHeight
    }
    autoFit()
  })
}

function autoFit() {
  if (!containerW.value || !imgNaturalW.value) return
  const cw = containerW.value
  const ch = containerH.value
  const iw = imgNaturalW.value
  const ih = imgNaturalH.value
  const fitScale = Math.min(cw / iw, ch / ih, 1)
  imgScale.value = fitScale
  const dispW = iw * fitScale
  const dispH = ih * fitScale
  imgOffX.value = (cw - dispW) / 2
  imgOffY.value = (ch - dispH) / 2

  const selRatio = props.aspectRatio
  const maxW = dispW * 0.9
  const maxH = dispH * 0.9
  let w = Math.min(maxW, cw * 0.85)
  let h = w / selRatio
  if (h > maxH) {
    h = maxH
    w = h * selRatio
  }
  selW.value = w
  selH.value = h
  selX.value = (cw - w) / 2
  selY.value = (ch - h) / 2
}

function containerMouse(e: PointerEvent) {
  const el = containerRef.value!
  const rect = el.getBoundingClientRect()
  return { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

function onPointerDown(e: PointerEvent) {
  const pos = containerMouse(e)
  const corner = hitCorner(pos.x, pos.y)
  if (corner) {
    resizing.value = corner
    dragStartX.value = pos.x
    dragStartY.value = pos.y
    dragInitVal.value = selW.value
    if (containerRef.value) containerRef.value.setPointerCapture(e.pointerId)
    return
  }
  if (hitSelection(pos.x, pos.y)) {
    dragging.value = 'selection'
    dragStartX.value = pos.x - selX.value
    dragStartY.value = pos.y - selY.value
    if (containerRef.value) containerRef.value.setPointerCapture(e.pointerId)
    return
  }
  dragging.value = 'image'
  dragStartX.value = pos.x - imgOffX.value
  dragStartY.value = pos.y - imgOffY.value
  if (containerRef.value) containerRef.value.setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  const pos = containerMouse(e)
  const cw = containerW.value
  const ch = containerH.value
  if (resizing.value) {
    const dx = pos.x - dragStartX.value
    const dy = pos.y - dragStartY.value
    const d = (dx + dy) / 2
    let newW = dragInitVal.value
    if (resizing.value === 'br' || resizing.value === 'tr') newW = dragInitVal.value + dx
    else if (resizing.value === 'bl' || resizing.value === 'tl') newW = dragInitVal.value - dx
    newW = Math.max(minSelW, Math.min(newW, cw))
    const newH = newW / props.aspectRatio
    if (newH > ch) {
      const clampedH = ch
      newW = clampedH * props.aspectRatio
    }
    const oldW = selW.value
    const oldH = selH.value
    if (resizing.value === 'tl') {
      selX.value += (oldW - newW)
      selY.value += (oldH - newH)
    } else if (resizing.value === 'tr') {
      selY.value += (oldH - newH)
    } else if (resizing.value === 'bl') {
      selX.value += (oldW - newW)
    }
    selW.value = newW
    selH.value = newH
    selX.value = Math.max(0, Math.min(selX.value, cw - selW.value))
    selY.value = Math.max(0, Math.min(selY.value, ch - selH.value))
    return
  }
  if (dragging.value === 'selection') {
    selX.value = Math.max(0, Math.min(pos.x - dragStartX.value, cw - selW.value))
    selY.value = Math.max(0, Math.min(pos.y - dragStartY.value, ch - selH.value))
    return
  }
  if (dragging.value === 'image') {
    imgOffX.value = pos.x - dragStartX.value
    imgOffY.value = pos.y - dragStartY.value
  }
}

function onPointerUp() {
  dragging.value = null
  resizing.value = null
}

function hitSelection(mx: number, my: number) {
  return mx >= selX.value && mx <= selX.value + selW.value &&
    my >= selY.value && my <= selY.value + selH.value
}

const cornerSize = 12

function hitCorner(mx: number, my: number) {
  const x = selX.value
  const y = selY.value
  const x2 = x + selW.value
  const y2 = y + selH.value
  const hs = cornerSize
  if (Math.abs(mx - x) <= hs && Math.abs(my - y) <= hs) return 'tl' as const
  if (Math.abs(mx - x2) <= hs && Math.abs(my - y) <= hs) return 'tr' as const
  if (Math.abs(mx - x) <= hs && Math.abs(my - y2) <= hs) return 'bl' as const
  if (Math.abs(mx - x2) <= hs && Math.abs(my - y2) <= hs) return 'br' as const
  return null
}

const cursorStyle = computed(() => {
  if (resizing.value) return 'cursor-nwse-resize'
  if (dragging.value === 'selection') return 'cursor-grabbing'
  if (dragging.value === 'image') return 'cursor-grabbing'
  return ''
})

const imgStyle = computed(() => {
  const s = imgScale.value
  return {
    transform: `translate(${imgOffX.value}px, ${imgOffY.value}px) scale(${s})`,
    transformOrigin: '0 0',
  }
})

const selStyle = computed(() => ({
  left: `${selX.value}px`,
  top: `${selY.value}px`,
  width: `${selW.value}px`,
  height: `${selH.value}px`,
}))

const overlayStyle = computed(() => ({
  clipPath: `polygon(
    0% 0%, 100% 0%, 100% 100%, 0% 100%,
    0% 0%,
    ${(selX.value / containerW.value) * 100}% ${(selY.value / containerH.value) * 100}%,
    ${((selX.value + selW.value) / containerW.value) * 100}% ${(selY.value / containerH.value) * 100}%,
    ${((selX.value + selW.value) / containerW.value) * 100}% ${((selY.value + selH.value) / containerH.value) * 100}%,
    ${(selX.value / containerW.value) * 100}% ${((selY.value + selH.value) / containerH.value) * 100}%,
    ${(selX.value / containerW.value) * 100}% ${(selY.value / containerH.value) * 100}%
  )`,
}))

function zoomIn() {
  imgScale.value = Math.min(imgScale.value * 1.3, 5)
}

function zoomOut() {
  imgScale.value = Math.max(imgScale.value / 1.3, 0.1)
}

async function confirmCrop() {
  if (!containerRef.value || !imgLoaded.value) return
  const canvas = document.createElement('canvas')
  const srcW = selW.value / imgScale.value
  const srcH = selH.value / imgScale.value
  canvas.width = Math.round(srcW)
  canvas.height = Math.round(srcH)
  const ctx = canvas.getContext('2d')!
  const img = new Image()
  img.src = props.image
  await new Promise((resolve) => { img.onload = resolve })
  const sx = (selX.value - imgOffX.value) / imgScale.value
  const sy = (selY.value - imgOffY.value) / imgScale.value
  ctx.drawImage(img, sx, sy, srcW, srcH, 0, 0, canvas.width, canvas.height)
  canvas.toBlob((b) => {
    if (b) emit('crop', b)
  }, 'image/jpeg', 0.95)
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div
      ref="containerRef"
      class="relative w-full overflow-hidden rounded-xl bg-black/10 select-none"
      :class="cursorStyle"
      :style="{ aspectRatio: `${aspectRatio}/1`, maxHeight: '55vh' }"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <img
        v-show="imgLoaded"
        :src="image"
        class="absolute top-0 left-0 max-w-none pointer-events-none"
        :style="imgStyle"
        draggable="false"
        @load="onImgLoad"
      />

      <div v-if="!imgLoaded" class="absolute inset-0 flex items-center justify-center text-secondary text-sm">
        Загрузка...
      </div>

      <div v-if="imgLoaded" class="absolute inset-0 pointer-events-none bg-black/55" :style="overlayStyle" />

      <div
        v-if="imgLoaded"
        class="absolute pointer-events-none border-2 border-white rounded-sm"
        :style="selStyle"
      >
        <div class="absolute inset-0 grid grid-cols-3 grid-rows-3">
          <div v-for="i in 2" :key="'v' + i" class="w-px bg-white/30 h-full justify-self-center row-span-3" />
          <div v-for="i in 2" :key="'h' + i" class="h-px bg-white/30 w-full self-center col-span-3" />
        </div>

        <div class="absolute w-3 h-3 border-2 border-white rounded-sm -top-1.5 -left-1.5 bg-black/40" />
        <div class="absolute w-3 h-3 border-2 border-white rounded-sm -top-1.5 -right-1.5 bg-black/40" />
        <div class="absolute w-3 h-3 border-2 border-white rounded-sm -bottom-1.5 -left-1.5 bg-black/40" />
        <div class="absolute w-3 h-3 border-2 border-white rounded-sm -bottom-1.5 -right-1.5 bg-black/40" />
      </div>
    </div>

    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button type="button" class="w-8 h-8 rounded-lg bg-btn-secondary flex items-center justify-center hover:bg-btn-secondary-hover transition-colors" @click="zoomOut" title="Уменьшить">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20 12H4" /></svg>
        </button>
        <span class="text-xs text-secondary w-8 text-center">{{ Math.round(imgScale * 100) }}%</span>
        <button type="button" class="w-8 h-8 rounded-lg bg-btn-secondary flex items-center justify-center hover:bg-btn-secondary-hover transition-colors" @click="zoomIn" title="Увеличить">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
        </button>
      </div>
      <div class="flex items-center gap-2">
        <UiButton variant="secondary" size="sm" @click="emit('cancel')">Отмена</UiButton>
        <UiButton size="sm" @click="confirmCrop">Применить</UiButton>
      </div>
    </div>
  </div>
</template>
