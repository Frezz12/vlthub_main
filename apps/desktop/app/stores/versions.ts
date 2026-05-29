import { defineStore } from 'pinia'
import type {
  VersionOut,
  VersionCreate,
  VersionUpdate,
  VersionListOut,
  VersionFileOut,
  CommentOut,
  CommentCreate,
  AudioPreviewOut,
} from '@pjasaver/shared-types'

interface VersionsState {
  items: VersionOut[]
  total: number
  current: VersionOut | null
  files: VersionFileOut[]
  comments: CommentOut[]
  previews: AudioPreviewOut[]
  loading: boolean
}

export const useVersionsStore = defineStore('versions', {
  state: (): VersionsState => ({
    items: [],
    total: 0,
    current: null,
    files: [],
    comments: [],
    previews: [],
    loading: false,
  }),

  getters: {
    versionList: (state) => state.items,
    currentVersion: (state) => state.current,
    sortedVersions: (state) => [...state.items].sort((a, b) => {
      if (a.is_current) return -1
      if (b.is_current) return 1
      return b.version_number - a.version_number
    }),
  },

  actions: {
    _authHeaders(): Record<string, string> {
      const auth = useAuthStore()
      if (!auth.accessToken) return {}
      return { Authorization: `Bearer ${auth.accessToken}` }
    },

    async fetchVersions(projectId: string) {
      this.loading = true
      try {
        const res = await useApiFetch<VersionListOut>(`/api/v1/projects/${projectId}/versions`, { headers: this._authHeaders() })
        this.items = res.items
        this.total = res.total
      } finally {
        this.loading = false
      }
    },

    async fetchVersion(projectId: string, verId: string) {
      this.loading = true
      try {
        this.current = await useApiFetch<VersionOut>(`/api/v1/projects/${projectId}/versions/${verId}`, { headers: this._authHeaders() })
        return this.current
      } finally {
        this.loading = false
      }
    },

    async createVersion(projectId: string, data: VersionCreate) {
      const version = await useApiFetch<VersionOut>(`/api/v1/projects/${projectId}/versions`, {
        method: 'POST',
        body: data,
        headers: this._authHeaders(),
      })
      this.items.push(version)
      this.total++
      return version
    },

    async deleteVersion(projectId: string, verId: string) {
      await useApiFetch(`/api/v1/projects/${projectId}/versions/${verId}`, { method: 'DELETE', headers: this._authHeaders() })
      this.items = this.items.filter((v) => v.id !== verId)
      this.total--
      if (this.current?.id === verId) this.current = null
    },

    async setCurrentVersion(projectId: string, verId: string) {
      const version = await useApiFetch<VersionOut>(
        `/api/v1/projects/${projectId}/versions/${verId}/current`,
        { method: 'PATCH', headers: this._authHeaders() },
      )
      this.items = this.items.map((v) => ({ ...v, is_current: v.id === verId }))
      if (this.current?.id === verId) this.current = version
      return version
    },

    async updateVersion(projectId: string, verId: string, data: VersionUpdate) {
      const version = await useApiFetch<VersionOut>(
        `/api/v1/projects/${projectId}/versions/${verId}`,
        { method: 'PATCH', body: data, headers: this._authHeaders() },
      )
      this.items = this.items.map((v) => (v.id === verId ? version : v))
      if (this.current?.id === verId) this.current = version
      return version
    },

    async fetchFiles(projectId: string, verId: string) {
      this.files = await useApiFetch<VersionFileOut[]>(
        `/api/v1/projects/${projectId}/versions/${verId}/files`,
        { headers: this._authHeaders() },
      )
    },

    async fetchComments(projectId: string, verId: string) {
      this.comments = await useApiFetch<CommentOut[]>(
        `/api/v1/projects/${projectId}/versions/${verId}/comments`,
        { headers: this._authHeaders() },
      )
    },

    async addComment(projectId: string, verId: string, data: CommentCreate) {
      const comment = await useApiFetch<CommentOut>(
        `/api/v1/projects/${projectId}/versions/${verId}/comments`,
        { method: 'POST', body: data, headers: this._authHeaders() },
      )
      this.comments.push(comment)
      return comment
    },

    async deleteComment(projectId: string, verId: string, commentId: string) {
      await useApiFetch(
        `/api/v1/projects/${projectId}/versions/${verId}/comments/${commentId}`,
        { method: 'DELETE', headers: this._authHeaders() },
      )
      this.comments = this.comments.filter((c) => c.id !== commentId)
    },

    async deletePreview(projectId: string, verId: string, previewId: string) {
      await useApiFetch(
        `/api/v1/projects/${projectId}/versions/${verId}/previews/${previewId}`,
        { method: 'DELETE', headers: this._authHeaders() },
      )
      if (this.current) {
        this.current.audio_previews = this.current.audio_previews?.filter((p) => p.id !== previewId)
      }
    },
  },
})
