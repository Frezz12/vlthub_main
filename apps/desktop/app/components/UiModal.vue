<script setup lang="ts">
interface Props {
  modelValue: boolean
  title?: string
  maxWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  maxWidth: '480px',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function close() {
  emit('update:modelValue', false)
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.modelValue) close()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-start justify-center pt-8 pb-8 bg-black/40 backdrop-blur-sm overflow-y-auto"
      >
        <Transition name="slide" appear>
          <div
            v-if="modelValue"
            class="card w-full mx-4 my-auto overflow-y-auto"
            :style="{ maxWidth, maxHeight: '90vh' }"
          >
            <div v-if="title" class="flex items-center justify-between px-6 py-4 border-b border-separator bg-muted-surface/80">
              <h2 class="text-base font-semibold text-foreground">{{ title }}</h2>
              <button class="text-secondary hover:text-foreground transition-colors" @click="close">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div class="px-6 py-4">
              <slot />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
