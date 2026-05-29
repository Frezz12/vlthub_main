<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const auth = useAuthStore()
const projects = useProjectsStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

type TabId = 'my' | 'favorite' | 'accessible' | 'archived'

const searchQuery = ref('')
const showCreateModal = ref(false)
const activeTab = ref<TabId>('my')

const tabs: { id: TabId; label: string }[] = [
  { id: 'favorite', label: 'Избранные' },
  { id: 'my', label: 'Мои проекты' },
  { id: 'accessible', label: 'Доступные' },
  { id: 'archived', label: 'Архив' },
]

const ownedProjects = computed(() =>
  projects.items.filter(p => p.owner_id === auth.user?.id && !p.is_archived)
)

const accessibleProjects = computed(() =>
  projects.items.filter(p => p.owner_id !== auth.user?.id && !p.is_archived)
)

const favoriteProjects = computed(() =>
  projects.items.filter(p => p.is_favorite && !p.is_archived)
)

const archivedProjects = computed(() =>
  projects.items.filter(p => p.is_archived)
)

const currentList = computed(() => {
  let list: typeof projects.items
  if (activeTab.value === 'favorite') list = favoriteProjects.value
  else if (activeTab.value === 'my') list = ownedProjects.value
  else if (activeTab.value === 'accessible') list = accessibleProjects.value
  else list = archivedProjects.value
  return [...list].sort((a, b) => (b.is_favorite ? 1 : 0) - (a.is_favorite ? 1 : 0))
})

const isAccessibleTab = computed(() => activeTab.value === 'accessible')

function getTabFilters(tab: TabId) {
  return {
    archived: tab === 'archived' ? null : false,
    favorite: tab === 'favorite' ? true : null,
  }
}

onMounted(() => {
  projects.setFilters(getTabFilters(activeTab.value))
  projects.fetchProjects()
})

watch(searchQuery, (val) => {
  projects.setFilters({ search: val })
  projects.fetchProjects()
})

watch(activeTab, () => {
  projects.setFilters(getTabFilters(activeTab.value))
  projects.fetchProjects()
})

function handleDelete(id: string) {
  if (confirm('Удалить проект?')) {
    projects.deleteProject(id)
  }
}

async function handleArchive(projectId: string) {
  const project = projects.items.find(p => p.id === projectId)
  if (!project) return
  await projects.updateProject(projectId, { is_archived: !project.is_archived })
  projects.fetchProjects()
}

async function handleFavorite(projectId: string) {
  const project = projects.items.find(p => p.id === projectId)
  if (!project) return
  const newVal = !project.is_favorite
  if (newVal && projects.items.filter(p => p.is_favorite).length >= 5) {
    toast.show('Максимум 5 избранных проектов', 'error')
    return
  }
  await projects.updateProject(projectId, { is_favorite: newVal })
  projects.fetchProjects()
}
</script>

<template>
  <div class="page-shell">
    <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
      <div>
        <h1 class="page-title">Проекты</h1>
        <p class="page-subtitle">
          Добро пожаловать, {{ auth.user?.nickname }}
        </p>
      </div>
      <UiButton @click="showCreateModal = true">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Новый проект
      </UiButton>
    </div>

    <div class="mb-6 flex flex-col sm:flex-row gap-3">
      <UiInput
        v-model="searchQuery"
        placeholder="Поиск проектов..."
        class="flex-1"
      />
      <div class="tabs-bar shrink-0 overflow-x-auto max-w-full">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="tab-btn whitespace-nowrap"
          :class="activeTab === tab.id ? 'tab-btn-active' : 'tab-btn-inactive'"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div v-if="projects.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="card p-4 animate-pulse">
        <div class="h-4 bg-btn-secondary rounded w-3/4 mb-3" />
        <div class="h-3 bg-btn-secondary rounded w-1/2 mb-2" />
        <div class="h-3 bg-btn-secondary rounded w-1/3" />
      </div>
    </div>

    <div v-else-if="currentList.length === 0" class="empty-state">
      <p class="text-secondary text-lg mb-2">
        {{ activeTab === 'favorite' ? 'Нет избранных проектов' : activeTab === 'my' ? 'У вас пока нет проектов' : activeTab === 'accessible' ? 'Нет доступных проектов' : 'Нет архивных проектов' }}
      </p>
      <p class="text-secondary text-sm mb-6">
        {{ activeTab === 'my' ? 'Создайте первый проект, чтобы начать работу' : '' }}
      </p>
      <UiButton v-if="activeTab === 'my'" @click="showCreateModal = true">Создать проект</UiButton>
    </div>

    <TransitionGroup
      v-else
      name="stagger"
      tag="div"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <NuxtLink
        v-for="(project, index) in currentList"
        :key="project.id"
        :to="`/projects/${project.id}`"
        class="card card-interactive p-4 no-underline block relative overflow-hidden"
        :style="{ '--delay': index * 0.05 + 's' }"
      >
        <ProjectCardContent
          :project="project"
          :is-accessible="isAccessibleTab"
          :can-archive="project.owner_id === auth.user?.id"
          @archive="handleArchive"
          @favorite="handleFavorite"
        />
      </NuxtLink>
    </TransitionGroup>

    <UiModal v-model="showCreateModal" title="Новый проект">
      <ProjectForm @created="showCreateModal = false" />
    </UiModal>
  </div>
</template>

