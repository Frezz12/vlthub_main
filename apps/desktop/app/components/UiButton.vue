<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  block?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  block: false,
})

const emit = defineEmits<{
  click: [e: MouseEvent]
}>()
</script>

<template>
  <button
    :class="[
      'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]',
      {
        'bg-primary text-white hover:bg-primary/90 active:bg-primary/80': variant === 'primary',
        'bg-btn-secondary text-foreground hover:bg-btn-secondary-hover': variant === 'secondary',
        'text-foreground hover:bg-hover': variant === 'ghost',
        'bg-danger text-white hover:bg-danger/90': variant === 'danger',
        'px-2 py-1 text-[10px]': size === 'xs',
        'px-3 py-1.5 text-xs': size === 'sm',
        'px-4 py-3 text-sm': size === 'md',
        'px-6 py-3 text-base': size === 'lg',
        'w-full': block,
      },
    ]"
    :disabled="disabled || loading"
    @click="emit('click', $event)"
  >
    <svg
      v-if="loading"
      class="animate-spin h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <slot />
  </button>
</template>
