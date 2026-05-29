<script setup lang="ts">
interface SharedProject {
  id: string
  owner: { id: string; nickname: string; username: string; avatar_url: string | null } | null
  title: string
  bpm: number | null
  key: string | null
  beatmaker: string | null
  status: string
  description: string | null
  cover_url: string | null
  daw_type: string | null
  created_at: string
  updated_at: string
  tags: string[]
  role: string
}

import { formatError } from '~/utils/formatError'
const route = useRoute()
const loading = ref(true)
const project = ref<SharedProject | null>(null)
const error = ref('')
const requesting = ref(false)
const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

onMounted(async () => {
  try {
    const res = await fetch(__API_BASE_URL__ + `/api/v1/projects/shared/${route.params.token}`, {
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: 'Not found' }))
      throw new Error(body.detail || 'Not found')
    }
    project.value = await res.json()
  } catch (e: any) {
    error.value = formatError(e)
  } finally {
    loading.value = false
  }
})

async function requestAccess() {
  if (!project.value || requesting.value) return
  requesting.value = true
  try {
    const res = await fetch(__API_BASE_URL__ + `/api/v1/projects/${project.value.id}/access-requests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.accessToken}`,
      },
      body: JSON.stringify({ message: 'Хочу получить доступ по ссылке' }),
    })
    if (!res.ok) throw new Error('Failed to request access')
    toast.show('Запрос на доступ отправлен', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    requesting.value = false
  }
}

const statusLabels: Record<string, string> = {
  in_progress: 'In progress',
  completed: 'Completed',
  on_hold: 'On hold',
  dropped: 'Dropped',
}
</script>

<template>
  <div class="min-h-screen bg-surface-elevated">
    <header class="border-b border-separator px-6 py-4 flex items-center gap-3">
      <a href="/" class="text-xl font-bold text-primary no-underline">VLTHub</a>
      <span class="text-xs text-secondary">Shared project</span>
    </header>

    <main class="max-w-3xl mx-auto px-4 py-8">
      <div v-if="loading" class="text-center py-12 text-secondary">Loading...</div>

      <div v-else-if="error" class="text-center py-12">
        <p class="text-lg font-medium text-[#FF3B30] mb-2">Project not available</p>
        <p class="text-sm text-secondary">{{ error }}</p>
        <a href="/" class="inline-block mt-4 text-sm text-primary hover:underline">Go to home page</a>
      </div>

      <template v-else-if="project">
        <div class="flex items-start gap-4 mb-8">
          <div class="flex-1">
            <h1 class="text-2xl font-bold mb-1">{{ project.title }}</h1>
            <p v-if="project.owner" class="text-sm text-secondary">
              <span class="flex items-center gap-1">by {{ project.owner.nickname }}<UserBadgeIcon :badge="(project.owner as any).active_badge" size="sm" /></span>
              <span class="text-xs text-[#C7C7CC]">@{{ project.owner.username }}</span>
            </p>
          </div>
          <span
            class="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
            :class="{
              'bg-[#34C759]/10 text-[#34C759]': project.status === 'completed',
              'bg-[#007AFF]/10 text-[#007AFF]': project.status === 'in_progress',
              'bg-[#FF9500]/10 text-[#FF9500]': project.status === 'on_hold',
              'bg-[#C7C7CC]/10 text-[#8E8E93]': project.status === 'dropped',
            }"
          >
            {{ statusLabels[project.status] || project.status }}
          </span>
        </div>

        <div v-if="project.tags.length" class="flex flex-wrap gap-2 mb-6">
          <span
            v-for="tag in project.tags"
            :key="tag"
            class="inline-flex items-center rounded-full bg-[#F2F2F7] px-3 py-1 text-xs text-[#3A3A3C]"
          >
            #{{ tag }}
          </span>
        </div>

        <div v-if="project.description" class="text-sm text-[#3A3A3C] mb-6 leading-relaxed whitespace-pre-wrap">
          {{ project.description }}
        </div>

        <div class="grid grid-cols-2 gap-4 mb-8">
          <div v-if="project.bpm" class="rounded-xl bg-[#F2F2F7] px-4 py-3">
            <div class="text-xs text-secondary mb-1">BPM</div>
            <div class="text-sm font-medium">{{ project.bpm }}</div>
          </div>
          <div v-if="project.key" class="rounded-xl bg-[#F2F2F7] px-4 py-3">
            <div class="text-xs text-secondary mb-1">Key</div>
            <div class="text-sm font-medium">{{ project.key }}</div>
          </div>
          <div v-if="project.beatmaker" class="rounded-xl bg-[#F2F2F7] px-4 py-3">
            <div class="text-xs text-secondary mb-1">Beatmaker</div>
            <div class="text-sm font-medium">{{ project.beatmaker }}</div>
          </div>
          <div v-if="project.daw_type" class="rounded-xl bg-[#F2F2F7] px-4 py-3">
            <div class="text-xs text-secondary mb-1">DAW</div>
            <div class="text-sm font-medium">{{ project.daw_type }}</div>
          </div>
        </div>

        <div class="border-t border-separator pt-4 flex items-center justify-between gap-4">
          <span class="text-xs text-secondary">You have <strong class="text-[#3A3A3C]">{{ project.role }}</strong> access</span>
          <div v-if="auth.isAuthenticated" class="flex gap-2">
            <UiButton size="sm" :loading="requesting" @click="requestAccess">
              Запросить доступ
            </UiButton>
            <UiButton size="sm" variant="primary" @click="$router.push('/login')">
              <template v-if="!auth.isAuthenticated">Войти</template>
            </UiButton>
          </div>
          <UiButton v-else size="sm" variant="primary" @click="$router.push('/login')">
            Войти для доступа
          </UiButton>
        </div>
      </template>
    </main>
  </div>
</template>
