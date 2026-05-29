import { defineStore } from 'pinia'
import type { UserOut, LoginRequest, RegisterRequest, TokenResponse } from '@pjasaver/shared-types'

function getStorage(name: string): string | null {
  if (import.meta.client) {
    try {
      return localStorage.getItem(name)
    } catch { return null }
  }
  return null
}

function setStorage(name: string, value: string | null) {
  if (import.meta.client) {
    try {
      if (value) localStorage.setItem(name, value)
      else localStorage.removeItem(name)
    } catch { /* ignore */ }
  }
}

interface AuthState {
  user: UserOut | null
  accessToken: string | null
  refreshToken: string | null
  loading: boolean
  hasPin: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    loading: false,
    hasPin: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    currentUser: (state) => state.user,
  },

  actions: {
    _authHeaders(): Record<string, string> {
      if (!this.accessToken) return {}
      return { Authorization: `Bearer ${this.accessToken}` }
    },

    /** Restore session from storage on app start */
    initFromStorage() {
      if (!this.accessToken) {
        this.accessToken = getStorage('accessToken')
        this.refreshToken = getStorage('refreshToken')
      }
    },

    async register(data: RegisterRequest) {
      this.loading = true
      try {
        const res = await useApiFetch<TokenResponse>('/api/v1/auth/register', {
          method: 'POST',
          body: data,
        })
        this._setSession(res)
        return res
      } finally {
        this.loading = false
      }
    },

    async login(data: LoginRequest) {
      this.loading = true
      try {
        const res = await useApiFetch<TokenResponse>('/api/v1/auth/login', {
          method: 'POST',
          body: data,
        })
        this._setSession(res)
        return res
      } finally {
        this.loading = false
      }
    },

    async refresh() {
      if (!this.refreshToken) return null
      try {
        const res = await useApiFetch<TokenResponse>('/api/v1/auth/refresh', {
          method: 'POST',
          body: { refresh_token: this.refreshToken },
        })
        this._setSession(res)
        return res
      } catch {
        this._clearSession()
        return null
      }
    },

    async logout() {
      try {
        await useApiFetch('/api/v1/auth/logout', {
          method: 'POST',
          body: { refresh_token: this.refreshToken },
        })
      } catch {
        // ignore
      }
      this._clearSession()
      navigateTo('/login')
    },

    async fetchMe() {
      this.user = await useApiFetch<UserOut>('/api/v1/users/me', {
        headers: this._authHeaders(),
      })
      await this.fetchPinStatus()
    },

    async fetchPinStatus() {
      try {
        const res = await useApiFetch<{ has_pin: boolean }>('/api/v1/auth/check-pin', {
          method: 'POST',
          body: { email: this.user?.email },
        })
        this.hasPin = res.has_pin
      } catch {
        this.hasPin = false
      }
    },

    _setSession(res: TokenResponse) {
      this.accessToken = res.access_token
      this.refreshToken = res.refresh_token
      this.user = res.user
      this.hasPin = res.has_pin
      setStorage('accessToken', res.access_token)
      setStorage('refreshToken', res.refresh_token)
    },

    _clearSession() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      setStorage('accessToken', null)
      setStorage('refreshToken', null)
    },
  },
})
