<script setup lang="ts">
import type { UserBadgeBrief } from '@pjasaver/shared-types'

withDefaults(defineProps<{
  badge: UserBadgeBrief | null | undefined
  size?: 'sm' | 'md' | 'lg'
}>(), { size: 'sm' })

const sizeMap: Record<string, string> = { sm: 'w-4 h-4', md: 'w-5 h-5', lg: 'w-6 h-6' }
</script>

<template>
  <span
    v-if="badge"
    :title="badge.description ? `${badge.name} — ${badge.description}` : badge.name"
    class="inline-flex items-center justify-center shrink-0"
    :class="sizeMap[size]"
    v-html="badge.icon_svg"
  />
</template>
