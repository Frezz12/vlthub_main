<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()
const dm = useDMStore()

const selectedUserId = ref<string | null>(null)
const showRoomList = ref(true)

watch(() => route.query.user, (user) => {
  if (user && typeof user === 'string') {
    selectedUserId.value = user
    showRoomList.value = false
  }
}, { immediate: true })

watch(() => dm.currentRoomId, (roomId) => {
  if (!roomId && selectedUserId.value) {
    selectedUserId.value = null
    showRoomList.value = true
    router.replace({ query: {} })
  }
})

function selectUser(userId: string) {
  selectedUserId.value = userId
  showRoomList.value = false
  router.replace({ query: { user: userId } })
}

function backToList() {
  showRoomList.value = true
  selectedUserId.value = null
  dm.clearMessages()
  dm.disconnectWebSocket()
  router.replace({ query: {} })
}
</script>

<template>
  <div class="flex h-[calc(100vh-3.5rem)] bg-surface/30">
    <!-- Room list sidebar -->
    <div
      class="w-[340px] shrink-0 border-r border-border/20"
      :class="showRoomList || !selectedUserId ? 'block' : 'hidden md:block'"
    >
      <DmRoomList :active-user-id="selectedUserId" @select="selectUser" />
    </div>

    <!-- Chat area -->
    <div
      class="flex-1 min-w-0 relative"
      :class="!showRoomList && selectedUserId ? 'block' : 'hidden md:block'"
    >
      <template v-if="selectedUserId">
        <DmChat :key="selectedUserId" :other-user-id="selectedUserId" />
      </template>

      <!-- Placeholder when no chat selected -->
      <div v-else class="flex flex-col items-center justify-center h-full text-center px-8">
        <div class="w-20 h-20 rounded-[24px] bg-gradient-to-br from-primary/8 to-primary/3 text-primary/25 flex items-center justify-center mb-6 shadow-sm ring-1 ring-black/[0.02]">
          <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="0.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
        </div>
        <h2 class="text-[17px] font-semibold text-foreground/50 mb-1.5">Добро пожаловать в чаты</h2>
        <p class="text-[13px] text-secondary/40 max-w-[280px] leading-relaxed">Выберите пользователя из списка слева или начните новый диалог, нажав «+» в верхнем углу</p>
      </div>
    </div>
  </div>
</template>
