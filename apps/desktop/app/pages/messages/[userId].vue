<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()

const userId = computed(() => route.params.userId as string)

onMounted(() => {
  router.replace(`/messages?user=${userId.value}`)
})
</script>

<template>
  <div class="flex items-center justify-center h-[calc(100vh-5rem)]">
    <div class="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
  </div>
</template>
