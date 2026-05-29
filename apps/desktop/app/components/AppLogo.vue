<script setup lang="ts">
withDefaults(
  defineProps<{
    size?: 'sm' | 'lg'
    showIcon?: boolean
  }>(),
  {
    size: 'sm',
    showIcon: true,
  },
)
</script>

<template>
  <div
    class="flex items-center"
    :class="size === 'lg' ? 'justify-center flex-col gap-3' : 'gap-2.5'"
  >
    <div
      v-if="showIcon"
      class="rounded-xl bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center shrink-0 shadow-lg shadow-primary/25"
      :class="size === 'lg' ? 'w-14 h-14' : 'w-7 h-7'"
    >
      <span
        class="font-bold text-white leading-none tracking-tight"
        :class="size === 'lg' ? 'text-2xl' : 'text-xs'"
      >V</span>
    </div>
    <div :class="size === 'lg' ? 'text-center' : ''">
      <span
        class="font-semibold tracking-tight"
        :class="
          size === 'lg'
            ? 'text-4xl font-extrabold bg-gradient-to-r from-primary to-primary-dark bg-clip-text text-transparent'
            : 'text-sm text-foreground'
        "
      >VLTHub</span>
      <p v-if="size === 'lg'" class="text-[11px] text-secondary/60 tracking-widest uppercase mt-0.5">Project Studio</p>
    </div>
  </div>
</template>
