<script setup lang="ts">
withDefaults(defineProps<{
  size?: 'sm' | 'md' | 'lg'
}>(), { size: 'sm' })

const sizeMap: Record<string, string> = {
  sm: 'text-[11px] px-1.5 py-0.5 rounded-md',
  md: 'text-xs px-2 py-0.5 rounded-lg',
  lg: 'text-sm px-2.5 py-1 rounded-lg',
}
</script>

<template>
  <span
    class="inline-flex items-center font-medium border border-border/50 bg-surface-elevated text-secondary"
    :class="sizeMap[size]"
  >
    <slot />
  </span>
</template>
