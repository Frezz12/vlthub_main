<script setup lang="ts">
interface Props {
  modelValue: string
  type?: string
  placeholder?: string
  label?: string
  error?: string
  disabled?: boolean
  maxlength?: number
  hint?: string
}

defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function onInput(e: Event) {
  const target = e.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" class="text-sm font-medium text-foreground">
      {{ label }}
    </label>
    <div class="relative">
      <input
        :type="type || 'text'"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :maxlength="maxlength"
        class="input-control w-full rounded-xl px-4 py-3 text-sm placeholder-secondary disabled:opacity-50"
        :class="{ 'border-danger': error }"
        @input="onInput"
      />
    </div>
    <p v-if="error" class="text-xs text-danger">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-secondary">{{ hint }}</p>
  </div>
</template>
