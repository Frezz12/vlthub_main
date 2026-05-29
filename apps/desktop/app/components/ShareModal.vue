<script setup lang="ts">
interface Props {
  projectId: string
}

const props = defineProps<Props>()
import { formatError } from '~/utils/formatError'
const projects = useProjectsStore()
const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const query = ref('')
const results = ref<{ id: string; nickname: string; username: string; avatar_url: string | null }[]>([])
const searching = ref(false)
const inviting = ref<string | null>(null)
const collaborators = ref<{ user_id: string; nickname: string; username: string; avatar_url: string | null; role: string; status: string }[]>([])
const loadingCollabs = ref(true)
const role = ref<'editor'>('editor')
const shareLink = ref('')

async function loadCollaborators() {
  try {
    const res = await fetch(__API_BASE_URL__ + `/api/v1/projects/${props.projectId}/collaborators`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (res.ok) collaborators.value = await res.json()
  } catch {
    // ignore
  } finally {
    loadingCollabs.value = false
  }
}

onMounted(loadCollaborators)

let debounceTimer: ReturnType<typeof setTimeout>
function onSearchInput() {
  clearTimeout(debounceTimer)
  if (!query.value.trim()) { results.value = []; return }
  debounceTimer = setTimeout(doSearch, 300)
}

async function doSearch() {
  const q = query.value.trim()
  if (!q) return
  searching.value = true
  try {
    const res = await fetch(__API_BASE_URL__ + `/api/v1/users/search?q=${encodeURIComponent(q)}`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (res.ok) results.value = await res.json()
  } catch {
    results.value = []
  } finally {
    searching.value = false
  }
}

async function handleInvite(user: { id: string; username: string }) {
  inviting.value = user.id
  try {
    const res = await fetch(__API_BASE_URL__ + `/api/v1/projects/${props.projectId}/collaborators`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${auth.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email_or_username: user.username, role: 'editor' }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Ошибка' }))
      throw new Error(err.detail || 'Ошибка')
    }
    const collab = await res.json()
    collaborators.value.push(collab)
    results.value = results.value.filter(u => u.id !== user.id)
    query.value = ''
    toast.show(`${collab.nickname} добавлен в проект`, 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  } finally {
    inviting.value = null
  }
}

async function handleRemove(userId: string) {
  try {
    const res = await fetch(__API_BASE_URL__ + `/api/v1/projects/${props.projectId}/collaborators/${userId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error('Ошибка')
    collaborators.value = collaborators.value.filter(c => c.user_id !== userId)
    toast.show('Участник удалён', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}

async function handleGenerateLink() {
  try {
    const link = await projects.createShareLink(props.projectId, { role: role.value })
    shareLink.value = `https://vlthub.ru/shared/${link.token}`
    toast.show('Ссылка скопирована', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- Search users -->
    <div>
      <h3 class="text-sm font-medium mb-3">Добавить участника</h3>
      <UiInput
        v-model="query"
        placeholder="Поиск по username или имени..."
        @input="onSearchInput"
      />
      <div v-if="searching" class="text-xs text-secondary mt-2">Поиск...</div>
      <div v-else-if="results.length" class="mt-2 flex flex-col gap-1">
        <div
          v-for="u in results"
          :key="u.id"
          class="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-border/50 transition-colors"
        >
          <div class="flex items-center gap-2">
            <UiAvatar :src="u.avatar_url" :name="u.nickname" size="sm" />
            <div>
              <div class="text-sm font-medium">{{ u.nickname }}</div>
              <div class="text-xs text-secondary">@{{ u.username }}</div>
            </div>
          </div>
          <UiButton
            size="xs"
            variant="primary"
            :loading="inviting === u.id"
            @click="handleInvite(u)"
          >
            Добавить
          </UiButton>
        </div>
      </div>
      <div v-else-if="query && !searching" class="text-xs text-secondary mt-2">
        Пользователи не найдены
      </div>
    </div>

    <div class="border-t border-separator" />

    <!-- Current collaborators -->
    <div>
      <h3 class="text-sm font-medium mb-3">Участники проекта</h3>
      <div v-if="loadingCollabs" class="text-xs text-secondary">Загрузка...</div>
      <div v-else-if="!collaborators.length" class="text-xs text-secondary">
        Пока нет участников
      </div>
      <div v-else class="flex flex-col gap-1">
        <div
          v-for="c in collaborators"
          :key="c.user_id"
          class="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-border/50 transition-colors"
        >
          <div class="flex items-center gap-2">
            <UiAvatar :src="c.avatar_url" :name="c.nickname" size="sm" />
            <div>
              <div class="text-sm font-medium">{{ c.nickname }}</div>
              <div class="text-xs text-secondary">@{{ c.username }}</div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs text-secondary capitalize">{{ c.role }}</span>
            <button
              class="text-xs text-danger hover:underline"
              @click="handleRemove(c.user_id)"
            >
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="border-t border-separator" />

    <!-- Share link -->
    <div>
      <h3 class="text-sm font-medium mb-3">Создать ссылку для доступа</h3>
      <div class="flex gap-2 mb-3">
        <select
          v-model="role"
          class="rounded-lg input-control px-3 py-2 text-sm"
        >
          <option value="editor">Редактор</option>
        </select>
        <UiButton @click="handleGenerateLink">Создать ссылку</UiButton>
      </div>
      <div v-if="shareLink" class="text-xs text-primary break-all bg-border/50 p-2 rounded">
        {{ shareLink }}
      </div>
    </div>
  </div>
</template>
