<script setup lang="ts">
interface Props {
  src?: string | null
  alt?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'profile'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
})

const API_BASE = (typeof __API_BASE_URL__ !== 'undefined' && __API_BASE_URL__) ? __API_BASE_URL__ : 'http://localhost:8000'

const cacheKey = ref(0)

watch(() => props.src, () => {
  cacheKey.value++
})

const resolvedSrc = computed(() => {
  if (!props.src) return null
  return props.src.startsWith('/') ? `${API_BASE}${props.src}` : props.src
})

const avatarSrc = computed(() => {
  if (!resolvedSrc.value) return null
  const separator = resolvedSrc.value.includes('?') ? '&' : '?'
  return `${resolvedSrc.value}${separator}_ck=${cacheKey.value}`
})

const initials = computed(() => {
  if (!props.alt) return '?'
  return props.alt.split(' ').map((s) => s[0]).join('').toUpperCase().slice(0, 2)
})

const sizeClass = computed(() => ({
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-16 h-16 text-lg',
  xl: 'w-24 h-24 text-xl',
  '2xl': 'w-28 h-28 text-2xl',
  profile: 'w-28 h-28 sm:w-32 sm:h-32 text-2xl sm:text-3xl',
}[props.size]))
</script>

<template>
  <div
    v-if="avatarSrc"
    class="rounded-full overflow-hidden bg-btn-secondary shrink-0"
    :class="sizeClass"
  >
    <img :src="avatarSrc" :key="avatarSrc" :alt="alt" class="w-full h-full object-cover" />
  </div>
  <div
    v-else
    class="rounded-full text-primary flex items-center justify-center font-medium shrink-0"
    style="background-color: color-mix(in srgb, var(--color-primary) 10%, transparent)"
    :class="sizeClass"
  >
    {{ initials }}
  </div>
</template>
