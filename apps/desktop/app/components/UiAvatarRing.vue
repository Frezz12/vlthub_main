<script setup lang="ts">
import type { UserBadgeBrief } from '@pjasaver/shared-types'

interface Props {
  src?: string | null
  alt?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'profile'
  badge?: UserBadgeBrief | null
  shadow?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  shadow: 'shadow-md',
})

const ringPadding = computed(() => props.size === 'sm' ? 'p-[2px]' : 'p-[3px]')

const ringGradientStyle = computed(() => {
  if (!props.badge?.avatar_ring_gradient) return {}
  return { background: props.badge.avatar_ring_gradient, '--ring-gradient': props.badge.avatar_ring_gradient }
})
</script>

<template>
  <template v-if="badge?.avatar_ring_gradient">
    <div
      class="inline-flex rounded-full avatar-ring-effect self-start"
      :class="[
        ringPadding,
        shadow,
        badge.avatar_ring_effect ? 'ring-effect-' + badge.avatar_ring_effect : '',
      ]"
      :style="ringGradientStyle"
    >
      <div class="rounded-full bg-surface-elevated">
        <UiAvatar :src="src" :alt="alt" :size="size" />
      </div>
    </div>
  </template>
  <UiAvatar v-else :src="src" :alt="alt" :size="size" />
</template>
