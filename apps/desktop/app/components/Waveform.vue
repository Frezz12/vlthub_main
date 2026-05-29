<script setup lang="ts">
interface Props {
  peaks?: number[]
  duration?: number
  currentTime?: number
  height?: number
}

withDefaults(defineProps<Props>(), {
  peaks: () => Array.from({ length: 100 }, () => Math.random()),
  height: 48,
})
</script>

<template>
  <div class="w-full flex items-end gap-[1px]" :style="{ height: `${height}px` }">
    <div
      v-for="(peak, i) in peaks"
      :key="i"
      class="flex-1 rounded-t"
      :style="{
        height: `${Math.max(2, peak * height * 0.8)}px`,
        backgroundColor: currentTime && (i / peaks.length) <= (currentTime / (duration || 1))
          ? 'var(--color-primary)'
          : 'var(--color-secondary)',
        opacity: 0.6,
      }"
    />
  </div>
</template>
