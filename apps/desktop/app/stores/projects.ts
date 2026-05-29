import { defineStore } from 'pinia'
import type {
  ProjectOut,
  ProjectCreate,
  ProjectUpdate,
  ProjectListOut,
  CollaboratorInvite,
  CollaboratorUpdate,
  AccessUpdate,
  ShareLinkCreate,
  ShareLinkOut,
  ExternalArtistCreate,
  DawType,
  ProjectActivityListOut,
} from '@pjasaver/shared-types'

interface ProjectsState {
  items: ProjectOut[]
  total: number
  current: ProjectOut | null
  loading: boolean
  filters: {
    daw: DawType | null
    search: string
    archived: boolean | null
    favorite: boolean | null
    tags: string[]
  }
}

export const useProjectsStore = defineStore('projects', {
  state: (): ProjectsState => ({
    items: [],
    total: 0,
    current: null,
    loading: false,
    filters: {
      daw: null,
      search: '',
      archived: false,
      favorite: null,
      tags: [],
    },
  }),

  getters: {
    projectList: (state) => state.items,
    currentProject: (state) => state.current,
  },

  actions: {
    _authHeaders(): Record<string, string> {
      const auth = useAuthStore()
      if (!auth.accessToken) return {}
      return { Authorization: `Bearer ${auth.accessToken}` }
    },

    async fetchProjects(page = 1, limit = 20) {
      this.loading = true
      try {
        const params = new URLSearchParams({ page: String(page), limit: String(limit) })
        if (this.filters.daw) params.set('daw', this.filters.daw)
        if (this.filters.search) params.set('q', this.filters.search)
        if (this.filters.archived !== null) params.set('archived', String(this.filters.archived))
        if (this.filters.favorite !== null) params.set('favorite', String(this.filters.favorite))

        const res = await useApiFetch<ProjectListOut>(`/api/v1/projects?${params}`, { headers: this._authHeaders() })
        this.items = res.items
        this.total = res.total
      } finally {
        this.loading = false
      }
    },

    async fetchProject(id: string) {
      this.loading = true
      try {
        this.current = await useApiFetch<ProjectOut>(`/api/v1/projects/${id}`, { headers: this._authHeaders() })
        return this.current
      } finally {
        this.loading = false
      }
    },

    async createProject(data: ProjectCreate) {
      const project = await useApiFetch<ProjectOut>('/api/v1/projects', {
        method: 'POST',
        body: data,
        headers: this._authHeaders(),
      })
      this.items.unshift(project)
      this.total++
      return project
    },

    async updateProject(id: string, data: ProjectUpdate) {
      const project = await useApiFetch<ProjectOut>(`/api/v1/projects/${id}`, {
        method: 'PATCH',
        body: data,
        headers: this._authHeaders(),
      })
      if (this.current?.id === id) this.current = project
      const idx = this.items.findIndex((p) => p.id === id)
      if (idx !== -1) this.items[idx] = project
      return project
    },

    async deleteProject(id: string) {
      await useApiFetch(`/api/v1/projects/${id}`, { method: 'DELETE', headers: this._authHeaders() })
      this.items = this.items.filter((p) => p.id !== id)
      this.total--
      if (this.current?.id === id) this.current = null
    },

    async inviteCollaborator(projectId: string, data: CollaboratorInvite) {
      return useApiFetch(`/api/v1/projects/${projectId}/collaborators`, {
        method: 'POST',
        body: data,
        headers: this._authHeaders(),
      })
    },

    async updateCollaborator(projectId: string, userId: string, data: CollaboratorUpdate) {
      return useApiFetch(`/api/v1/projects/${projectId}/collaborators/${userId}`, {
        method: 'PATCH',
        body: data,
        headers: this._authHeaders(),
      })
    },

    async removeCollaborator(projectId: string, userId: string) {
      return useApiFetch(`/api/v1/projects/${projectId}/collaborators/${userId}`, {
        method: 'DELETE',
        headers: this._authHeaders(),
      })
    },

    async addAccess(projectId: string, data: AccessUpdate) {
      return useApiFetch(`/api/v1/projects/${projectId}/access`, {
        method: 'POST',
        body: data,
        headers: this._authHeaders(),
      })
    },

    async createShareLink(projectId: string, data: ShareLinkCreate) {
      return useApiFetch<ShareLinkOut>(`/api/v1/projects/${projectId}/share-links`, {
        method: 'POST',
        body: data,
        headers: this._authHeaders(),
      })
    },

    async requestAccess(projectId: string) {
      return useApiFetch(`/api/v1/projects/${projectId}/request-access`, {
        method: 'POST',
        headers: this._authHeaders(),
      })
    },

    async fetchAccessRequests(projectId: string) {
      return useApiFetch(`/api/v1/projects/${projectId}/access-requests`, {
        headers: this._authHeaders(),
      })
    },

    async resolveAccessRequest(projectId: string, requesterId: string, action: 'approve' | 'deny') {
      return useApiFetch(`/api/v1/projects/${projectId}/access-requests/by-user/${requesterId}`, {
        method: 'PATCH',
        body: { action },
        headers: this._authHeaders(),
      })
    },

    async fetchMyPath(projectId: string): Promise<string | null> {
      try {
        const res = await useApiFetch<{ project_path: string | null }>(
          `/api/v1/projects/${projectId}/my-path`,
          { headers: this._authHeaders() },
        )
        return res.project_path
      } catch {
        return null
      }
    },

    async updateMyPath(projectId: string, projectPath: string | null) {
      await useApiFetch(`/api/v1/projects/${projectId}/my-path`, {
        method: 'PUT',
        body: { project_path: projectPath },
        headers: this._authHeaders(),
      })
      if (this.current?.id === projectId) {
        this.current.my_project_path = projectPath
      }
    },

    async leaveProject(projectId: string) {
      await useApiFetch(`/api/v1/projects/${projectId}/leave`, {
        method: 'POST',
        headers: this._authHeaders(),
      })
      this.items = this.items.filter((p) => p.id !== projectId)
      this.total--
      if (this.current?.id === projectId) this.current = null
    },

    async addExternalArtist(projectId: string, data: ExternalArtistCreate) {
      return useApiFetch(`/api/v1/projects/${projectId}/external-artists`, {
        method: 'POST',
        body: data,
        headers: this._authHeaders(),
      })
    },

    async fetchProjectActivity(projectId: string, limit = 80, offset = 0) {
      const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
      return useApiFetch<ProjectActivityListOut>(`/api/v1/projects/${projectId}/activity?${params}`, {
        headers: this._authHeaders(),
      })
    },

    setFilters(filters: Partial<ProjectsState['filters']>) {
      Object.assign(this.filters, filters)
    },
  },
})
