import { defineStore } from 'pinia'

export interface ChatMessageData {
  id: string
  room_id: string
  user_id: string
  user_name: string
  user_avatar: string | null
  content: string
  file_name: string | null
  file_path: string | null
  file_size: number | null
  file_type: string | null
  version_id: string | null
  version_number: number | null
  version_title: string | null
  reply_to_id: string | null
  reply_to_user_name: string | null
  reply_to_content: string | null
  reply_to_file_name: string | null
  reply_to_version_title: string | null
  reply_to_version_number: number | null
  edited_at: string | null
  deleted_by: string[] | null
  reactions: Record<string, string[]> | null
  created_at: string
  user_badge_icon_svg: string | null
  user_badge_ring_gradient: string | null
  user_badge_ring_effect: string | null
  user_badge_name: string | null
}

interface ChatState {
  messages: ChatMessageData[]
  total: number
  loading: boolean
  connected: boolean
  unreadCount: number
  uploading: boolean
  uploadProgress: number
  replyTo: { messageId: string; userName: string; content: string; versionTitle?: string | null; versionNumber?: number | null } | null
  editingMessage: ChatMessageData | null
}

let ws: WebSocket | null = null
let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null

const BASE = typeof __API_BASE_URL__ !== 'undefined' && __API_BASE_URL__
  ? __API_BASE_URL__
  : 'https://vlthub.ru'

export const useChatStore = defineStore('chat', {
  state: (): ChatState => ({
    messages: [],
    total: 0,
    loading: false,
    connected: false,
    unreadCount: 0,
    uploading: false,
    uploadProgress: 0,
    replyTo: null,
    editingMessage: null,
  }),

  getters: {
    sortedMessages: (state) => [...state.messages].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    ),
  },

  actions: {
    _authHeaders(): Record<string, string> {
      const auth = useAuthStore()
      if (!auth.accessToken) return {}
      return { Authorization: `Bearer ${auth.accessToken}` }
    },

    _token() {
      const auth = useAuthStore()
      return auth.accessToken || ''
    },

    _addMessage(msg: ChatMessageData) {
      const exists = this.messages.some(m => m.id === msg.id)
      if (!exists) {
        this.messages.push(msg)
        this.total++
      }
    },

    _removeMessage(id: string) {
      const idx = this.messages.findIndex(m => m.id === id)
      if (idx !== -1) {
        this.messages.splice(idx, 1)
        this.total--
      }
    },

    _updateMessage(id: string, updates: Partial<ChatMessageData>) {
      const idx = this.messages.findIndex(m => m.id === id)
      if (idx !== -1) {
        this.messages[idx] = { ...this.messages[idx], ...updates }
      }
    },

    async fetchMessages(projectId: string) {
      this.loading = true
      try {
        const res = await useApiFetch<{ messages: ChatMessageData[]; total: number }>(
          `/api/v1/projects/${projectId}/chat`,
          { headers: this._authHeaders() }
        )
        this.messages = res.messages
        this.total = res.total
      } finally {
        this.loading = false
      }
    },

    async sendMessage(projectId: string, content: string, signal?: AbortSignal) {
      const body: Record<string, any> = { content }
      if (this.replyTo) body.reply_to_id = this.replyTo.messageId
      const msg = await useApiFetch<ChatMessageData>(
        `/api/v1/projects/${projectId}/chat`,
        { method: 'POST', body, headers: this._authHeaders(), signal }
      )
      this._addMessage(msg)
      this.replyTo = null
      return msg
    },

    async sendVersionMessage(projectId: string, versionId: string, content = '', signal?: AbortSignal) {
      const body: Record<string, any> = { content, version_id: versionId }
      if (this.replyTo) body.reply_to_id = this.replyTo.messageId
      const msg = await useApiFetch<ChatMessageData>(
        `/api/v1/projects/${projectId}/chat/with-version`,
        { method: 'POST', body, headers: this._authHeaders(), signal }
      )
      this._addMessage(msg)
      this.replyTo = null
      return msg
    },

    async updateMessage(projectId: string, messageId: string, content: string, signal?: AbortSignal) {
      const msg = await useApiFetch<ChatMessageData>(
        `/api/v1/projects/${projectId}/chat/${messageId}`,
        { method: 'PATCH', body: { content }, headers: this._authHeaders(), signal }
      )
      this._updateMessage(messageId, msg)
      this.editingMessage = null
      return msg
    },

    async sendFileMessage(projectId: string, file: File, content = '') {
      this.uploading = true
      this.uploadProgress = 0
      try {
        const form = new FormData()
        form.append('file', file)
        form.append('content', content)
        if (this.replyTo) form.append('reply_to_id', this.replyTo.messageId)

        const xhr = new XMLHttpRequest()
        xhr.open('POST', `${BASE}/api/v1/projects/${projectId}/chat/with-file`)
        xhr.setRequestHeader('Authorization', `Bearer ${this._token()}`)
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            this.uploadProgress = Math.round((e.loaded / e.total) * 100)
          }
        }

        const msg = await new Promise<ChatMessageData>((resolve, reject) => {
          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(JSON.parse(xhr.responseText))
            } else {
              try {
                const err = JSON.parse(xhr.responseText)
                reject(new Error(err.detail || 'Upload failed'))
              } catch {
                reject(new Error('Upload failed'))
              }
            }
          }
          xhr.onerror = () => reject(new Error('Upload failed'))
          xhr.send(form)
        })

        this._addMessage(msg)
        this.replyTo = null
        return msg
      } finally {
        this.uploading = false
        this.uploadProgress = 0
      }
    },

    async sendVersionMessage(projectId: string, versionId: string, content = '') {
      const body: Record<string, any> = { content, version_id: versionId }
      if (this.replyTo) body.reply_to_id = this.replyTo.messageId
      const msg = await useApiFetch<ChatMessageData>(
        `/api/v1/projects/${projectId}/chat/with-version`,
        { method: 'POST', body, headers: this._authHeaders() }
      )
      this._addMessage(msg)
      this.replyTo = null
      return msg
    },

    async updateMessage(projectId: string, messageId: string, content: string) {
      const msg = await useApiFetch<ChatMessageData>(
        `/api/v1/projects/${projectId}/chat/${messageId}`,
        { method: 'PATCH', body: { content }, headers: this._authHeaders() }
      )
      this._updateMessage(messageId, msg)
      this.editingMessage = null
      return msg
    },

    async toggleReaction(projectId: string, messageId: string, emoji: string) {
      try {
        const msg = await useApiFetch<ChatMessageData>(
          `/api/v1/projects/${projectId}/chat/${messageId}/reactions`,
          { method: 'POST', body: { emoji }, headers: this._authHeaders() }
        )
        this._updateMessage(messageId, { reactions: msg.reactions })
        return msg
      } catch (e) {
        console.error('Failed to toggle reaction', e)
        throw e
      }
    },

    async deleteMessage(projectId: string, messageId: string, scope: 'all' | 'self' = 'all') {
      await useApiFetch(
        `/api/v1/projects/${projectId}/chat/${messageId}?scope=${scope}`,
        { method: 'DELETE', headers: this._authHeaders() }
      )
      if (scope === 'all') {
        this._removeMessage(messageId)
      } else {
        this._updateMessage(messageId, { deleted_by: [this._currentUserId(), ...(this.messages.find(m => m.id === messageId)?.deleted_by || [])] })
      }
    },

    _currentUserId(): string {
      const auth = useAuthStore()
      return auth.user?.id || ''
    },

    setReplyTo(messageId: string, userName: string, content: string, versionTitle?: string | null, versionNumber?: number | null) {
      this.replyTo = { messageId, userName, content, versionTitle, versionNumber }
    },

    clearReplyTo() {
      this.replyTo = null
    },

    setEditingMessage(msg: ChatMessageData | null) {
      this.editingMessage = msg
    },

    connectWebSocket(projectId: string) {
      const auth = useAuthStore()
      if (!auth.accessToken || ws) return

      const wsUrl = BASE.replace(/^http/, 'ws') +
        `/api/v1/projects/${projectId}/chat/ws?token=${auth.accessToken}`

      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        this.connected = true
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data) as ChatMessageData & { _type?: string; scope?: string; deleted_by?: string }
        if (data._type === 'edit') {
          this._updateMessage(data.id, data)
        } else if (data._type === 'delete') {
          if (data.scope === 'self') {
            const currentUserId = this._currentUserId()
            if (data.deleted_by === currentUserId) {
              this._removeMessage(data.id)
            } else {
              this._updateMessage(data.id, { deleted_by: [...(this.messages.find(m => m.id === data.id)?.deleted_by || []), data.deleted_by!] })
            }
          } else {
            this._removeMessage(data.id)
          }
        } else if (data._type === 'reaction') {
          this._updateMessage(data.id, { reactions: data.reactions })
        } else {
          this._addMessage(data)
          this.incrementUnread()
        }
      }

      ws.onclose = () => {
        this.connected = false
        ws = null
        wsReconnectTimer = setTimeout(() => this.connectWebSocket(projectId), 5000)
      }

      ws.onerror = () => {
        ws?.close()
      }
    },

    disconnectWebSocket() {
      if (wsReconnectTimer) {
        clearTimeout(wsReconnectTimer)
        wsReconnectTimer = null
      }
      if (ws) {
        ws.onclose = null
        ws.close()
        ws = null
      }
      this.connected = false
    },

    incrementUnread() {
      this.unreadCount++
    },

    clearUnread() {
      this.unreadCount = 0
    },

    clearMessages() {
      this.messages = []
      this.total = 0
    },
  },
})
