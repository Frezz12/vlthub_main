import { ofetch } from 'ofetch'
import type {
  RegisterRequest,
  LoginRequest,
  TokenResponse,
  RefreshRequest,
  UserOut,
  UserUpdate,
  SocialLinkUpdate,
  ProjectCreate,
  ProjectUpdate,
  ProjectOut,
  ProjectListOut,
  CollaboratorInvite,
  CollaboratorUpdate,
  AccessUpdate,
  ShareLinkCreate,
  ShareLinkOut,
  ExternalArtistCreate,
  VersionCreate,
  VersionOut,
  VersionListOut,
  VersionFileOut,
  CommentOut,
  CommentCreate,
  AudioPreviewOut,
  NotificationOut,
  NotificationListOut,
  SearchParams,
  SearchResult,
} from '@pjasaver/shared-types'

export function createApiClient(baseURL: string) {
  const api = ofetch.create({
    baseURL,
    headers: { 'Content-Type': 'application/json' },
    onResponseError({ response }) {
      throw new Error(response._data?.detail || `Request failed: ${response.status}`)
    },
  })

  let accessToken: string | null = null
  let refreshToken: string | null = null
  let onAuthError: (() => void) | null = null

  function setTokens(access: string, refresh: string) {
    accessToken = access
    refreshToken = refresh
  }

  function clearTokens() {
    accessToken = null
    refreshToken = null
  }

  function setOnAuthError(cb: () => void) {
    onAuthError = cb
  }

  const authHeaders = () => (accessToken ? { Authorization: `Bearer ${accessToken}` } : {})

  async function request<T>(url: string, opts: Record<string, any> = {}): Promise<T> {
    try {
      return await api<T>(url, {
        ...opts,
        headers: { ...authHeaders(), ...opts.headers },
      })
    } catch (err: any) {
      if (err.status === 401 && refreshToken) {
        try {
          const res = await api<TokenResponse>('/api/v1/auth/refresh', {
            method: 'POST',
            body: { refresh_token: refreshToken },
          })
          setTokens(res.access_token, res.refresh_token)
          return await api<T>(url, {
            ...opts,
            headers: { Authorization: `Bearer ${res.access_token}`, ...opts.headers },
          })
        } catch {
          clearTokens()
          onAuthError?.()
        }
      }
      throw err
    }
  }

  return {
    setTokens,
    clearTokens,
    setOnAuthError,
    get accessToken() { return accessToken },
    get refreshToken() { return refreshToken },

    // Auth
    register: (data: RegisterRequest) =>
      request<TokenResponse>('/api/v1/auth/register', { method: 'POST', body: data }),
    login: (data: LoginRequest) =>
      request<TokenResponse>('/api/v1/auth/login', { method: 'POST', body: data }),
    refresh: (data: RefreshRequest) =>
      request<TokenResponse>('/api/v1/auth/refresh', { method: 'POST', body: data }),
    logout: () =>
      request<void>('/api/v1/auth/logout', { method: 'POST' }),

    // Users
    getMe: () => request<UserOut>('/api/v1/users/me'),
    updateMe: (data: UserUpdate) =>
      request<UserOut>('/api/v1/users/me', { method: 'PATCH', body: data }),
    uploadAvatar: (formData: FormData) =>
      request<UserOut>('/api/v1/users/me/avatar', { method: 'POST', body: formData }),
    updateSocialLinks: (data: SocialLinkUpdate) =>
      request<void>('/api/v1/users/me/social-links', { method: 'PATCH', body: data }),
    getUser: (username: string) => request<UserOut>(`/api/v1/users/${username}`),

    // Projects
    listProjects: (params?: Record<string, any>) =>
      request<ProjectListOut>('/api/v1/projects', { params }),
    getProject: (id: string) => request<ProjectOut>(`/api/v1/projects/${id}`),
    createProject: (data: ProjectCreate) =>
      request<ProjectOut>('/api/v1/projects', { method: 'POST', body: data }),
    updateProject: (id: string, data: ProjectUpdate) =>
      request<ProjectOut>(`/api/v1/projects/${id}`, { method: 'PATCH', body: data }),
    deleteProject: (id: string) =>
      request<void>(`/api/v1/projects/${id}`, { method: 'DELETE' }),

    // Collaborators
    inviteCollaborator: (id: string, data: CollaboratorInvite) =>
      request<void>(`/api/v1/projects/${id}/collaborators`, { method: 'POST', body: data }),
    updateCollaborator: (id: string, userId: string, data: CollaboratorUpdate) =>
      request<void>(`/api/v1/projects/${id}/collaborators/${userId}`, { method: 'PATCH', body: data }),
    removeCollaborator: (id: string, userId: string) =>
      request<void>(`/api/v1/projects/${id}/collaborators/${userId}`, { method: 'DELETE' }),
    addExternalArtist: (id: string, data: ExternalArtistCreate) =>
      request<void>(`/api/v1/projects/${id}/external-artists`, { method: 'POST', body: data }),

    // Access
    addAccess: (id: string, data: AccessUpdate) =>
      request<void>(`/api/v1/projects/${id}/access`, { method: 'POST', body: data }),
    updateAccess: (id: string, userId: string, data: AccessUpdate) =>
      request<void>(`/api/v1/projects/${id}/access/${userId}`, { method: 'PATCH', body: data }),
    removeAccess: (id: string, userId: string) =>
      request<void>(`/api/v1/projects/${id}/access/${userId}`, { method: 'DELETE' }),

    // Share Links
    createShareLink: (id: string, data: ShareLinkCreate) =>
      request<ShareLinkOut>(`/api/v1/projects/${id}/share-links`, { method: 'POST', body: data }),
    deleteShareLink: (id: string, linkId: string) =>
      request<void>(`/api/v1/projects/${id}/share-links/${linkId}`, { method: 'DELETE' }),

    // Versions
    listVersions: (projectId: string) =>
      request<VersionListOut>(`/api/v1/projects/${projectId}/versions`),
    getVersion: (projectId: string, verId: string) =>
      request<VersionOut>(`/api/v1/projects/${projectId}/versions/${verId}`),
    createVersion: (projectId: string, data: VersionCreate) =>
      request<VersionOut>(`/api/v1/projects/${projectId}/versions`, { method: 'POST', body: data }),
    deleteVersion: (projectId: string, verId: string) =>
      request<void>(`/api/v1/projects/${projectId}/versions/${verId}`, { method: 'DELETE' }),
    setCurrentVersion: (projectId: string, verId: string) =>
      request<VersionOut>(`/api/v1/projects/${projectId}/versions/${verId}/current`, { method: 'PATCH' }),
    getVersionFiles: (projectId: string, verId: string) =>
      request<VersionFileOut[]>(`/api/v1/projects/${projectId}/versions/${verId}/files`),

    // Audio Previews
    uploadPreview: (projectId: string, verId: string, formData: FormData) =>
      request<AudioPreviewOut>(`/api/v1/projects/${projectId}/versions/${verId}/previews`, { method: 'POST', body: formData }),
    deletePreview: (projectId: string, verId: string, previewId: string) =>
      request<void>(`/api/v1/projects/${projectId}/versions/${verId}/previews/${previewId}`, { method: 'DELETE' }),

    // Comments
    listComments: (projectId: string, verId: string) =>
      request<CommentOut[]>(`/api/v1/projects/${projectId}/versions/${verId}/comments`),
    createComment: (projectId: string, verId: string, data: CommentCreate) =>
      request<CommentOut>(`/api/v1/projects/${projectId}/versions/${verId}/comments`, { method: 'POST', body: data }),
    deleteComment: (projectId: string, verId: string, commentId: string) =>
      request<void>(`/api/v1/projects/${projectId}/versions/${verId}/comments/${commentId}`, { method: 'DELETE' }),

    // Notifications
    listNotifications: (params?: Record<string, any>) =>
      request<NotificationListOut>('/api/v1/notifications', { params }),
    markNotificationRead: (id: string) =>
      request<void>(`/api/v1/notifications/${id}/read`, { method: 'PATCH' }),
    markAllNotificationsRead: () =>
      request<void>('/api/v1/notifications/read-all', { method: 'PATCH' }),

    // Search
    search: (params: SearchParams) =>
      request<SearchResult>('/api/v1/search', { params }),
  }
}
