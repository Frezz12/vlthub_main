<script setup lang="ts">
interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  rows?: number
}

const props = withDefaults(defineProps<Props>(), {
  rows: 4,
})

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const editorRef = ref<HTMLDivElement | null>(null)

onMounted(() => {
  if (editorRef.value && props.modelValue) {
    editorRef.value.innerHTML = props.modelValue
  }
})

watch(() => props.modelValue, (val) => {
  const el = editorRef.value
  if (!el || document.activeElement === el) return
  if (el.innerHTML !== val) el.innerHTML = val
})

function exec(cmd: string, val?: string) {
  document.execCommand(cmd, false, val)
  el().focus()
}

function el() {
  return editorRef.value!
}

function onInput() {
  emit('update:modelValue', el().innerHTML)
}

function onPaste(e: ClipboardEvent) {
  e.preventDefault()
  const text = e.clipboardData?.getData('text/plain') || ''
  document.execCommand('insertText', false, text)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    document.execCommand('insertLineBreak')
  }
}

const fonts = [
  { label: 'Sans-serif', value: 'sans-serif' },
  { label: 'Serif', value: 'serif' },
  { label: 'Monospace', value: 'monospace' },
  { label: 'Arial', value: 'Arial' },
  { label: 'Helvetica', value: 'Helvetica' },
  { label: 'Georgia', value: 'Georgia' },
  { label: 'Times New Roman', value: 'Times New Roman' },
  { label: 'Courier New', value: 'Courier New' },
]

const fontSizes = ['12px', '14px', '16px', '18px', '20px', '24px', '28px', '36px']
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" class="text-sm font-medium text-foreground">{{ label }}</label>
    <div class="border border-input-border rounded-xl overflow-hidden bg-surface-elevated focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all">
      <div class="flex items-center gap-0.5 px-2 py-1.5 border-b border-separator bg-muted-surface/50 flex-wrap">
        <button
          type="button"
          class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-btn-secondary text-sm font-bold transition-colors"
          title="Жирный"
          @click="exec('bold')"
        >B</button>
        <button
          type="button"
          class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-btn-secondary text-sm italic transition-colors"
          title="Курсив"
          @click="exec('italic')"
        >I</button>
        <button
          type="button"
          class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-btn-secondary text-sm line-through transition-colors"
          title="Зачёркнутый"
          @click="exec('strikeThrough')"
        >S</button>
        <span class="w-px h-5 bg-separator mx-1" />
        <select
          class="text-xs input-control border border-input-border rounded-md px-1.5 py-1 outline-none cursor-pointer hover:border-primary/50"
          title="Шрифт"
          @change="exec('fontName', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">Шрифт</option>
          <option v-for="f in fonts" :key="f.value" :value="f.value">{{ f.label }}</option>
        </select>
        <select
          class="text-xs input-control border border-input-border rounded-md px-1.5 py-1 outline-none cursor-pointer hover:border-primary/50"
          title="Размер"
          @change="exec('fontSize', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">Размер</option>
          <option v-for="s in fontSizes" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div
        ref="editorRef"
        class="px-4 py-3 text-sm overflow-y-auto outline-none"
        :style="{ minHeight: rows * 24 + 24 + 'px' }"
        contenteditable="true"
        :data-placeholder="placeholder"
        @input="onInput"
        @paste="onPaste"
        @keydown="onKeydown"
      />
    </div>
  </div>
</template>

<style scoped>
[contenteditable]:empty::before {
  content: attr(data-placeholder);
  color: var(--color-secondary, #86868B);
  pointer-events: none;
}
</style>
