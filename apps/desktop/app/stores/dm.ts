import { defineStore } from 'pinia'

export interface DirectMessageData {
  id: string
  room_id: string
  sender_id: string
  sender_name: string
  sender_avatar: string | null
  content: string
  file_name: string | null
  file_path: string | null
  file_size: number | null
  file_type: string | null
  reply_to_id: string | null
  reply_to_sender_name: string | null
  reply_to_content: string | null
  edited_at: string | null
  deleted_by: string[] | null
  reactions: Record<string, string[]> | null
  read_at: string | null
  created_at: string
  sender_badge_icon_svg: string | null
  sender_badge_ring_gradient: string | null
  sender_badge_ring_effect: string | null
  sender_badge_name: string | null
}

export interface DirectMessageRoomData {
  id: string
  user1_id: string
  user2_id: string
  other_user_id: string
  other_user_name: string
  other_user_username: string
  other_user_avatar: string | null
  last_message_at: string | null
  last_message_content: string | null
  unread_count: number
  created_at: string
  other_user_last_seen_at: string | null
  other_user_badge_icon_svg: string | null
  other_user_badge_ring_gradient: string | null
  other_user_badge_ring_effect: string | null
  other_user_badge_name: string | null
}

interface DMState {
  rooms: DirectMessageRoomData[]
  messages: DirectMessageData[]
  total: number
  loading: boolean
  currentRoomId: string | null
  connected: boolean
  unreadCount: number
  uploading: boolean
  uploadProgress: number
  replyTo: { messageId: string; userName: string; content: string } | null
  editingMessage: DirectMessageData | null
  playingAudioId: string | null
  audioPlaying: boolean
  audioMsgSenderId: string | null
  audioMsgFileName: string | null
  audioMsgFilePath: string | null
  audioProgress: Record<string, number>
  audioDuration: Record<string, number>
  playbackSpeed: number
  volume: number
  audioTrackList: TrackInfo[]
}

let ws: WebSocket | null = null
let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null
let _pendingContents = new Set<string>()

const BASE = typeof __API_BASE_URL__ !== 'undefined' && __API_BASE_URL__
  ? __API_BASE_URL__
  : 'http://localhost:8000'

const AUDIO_PERSIST_KEY = 'dm_audio_state'

interface TrackInfo {
  id: string
  filePath: string
  fileName: string
}

interface AudioPersist {
  playingAudioId: string
  audioPlaying: boolean
  audioMsgSenderId: string | null
  audioMsgFileName: string | null
  audioMsgFilePath: string | null
  audioProgress: Record<string, number>
  audioDuration: Record<string, number>
  playbackSpeed: number
  volume: number
  audioTrackList: TrackInfo[]
}

function isImageFile(name: string): boolean {
  const ext = name.split('.').pop()?.toLowerCase()
  return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'avif'].includes(ext || '')
}

function isVideoFile(name: string): boolean {
  const ext = name.split('.').pop()?.toLowerCase()
  return ['mp4', 'webm', 'mov', 'avi', 'mkv', 'm4v', '3gp'].includes(ext || '')
}

function isAudioFile(name: string): boolean {
  const ext = name.split('.').pop()?.toLowerCase()
  return ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'wma', 'opus', 'aiff'].includes(ext || '')
}

function saveAudioPersist(state: DMState) {
  try {
    const data: AudioPersist = {
      playingAudioId: state.playingAudioId || '',
      audioPlaying: state.audioPlaying,
      audioMsgSenderId: state.audioMsgSenderId,
      audioMsgFileName: state.audioMsgFileName,
      audioMsgFilePath: state.audioMsgFilePath,
      audioProgress: state.audioProgress,
      audioDuration: state.audioDuration,
      playbackSpeed: state.playbackSpeed,
      volume: state.volume,
      audioTrackList: state.audioTrackList,
    }
    localStorage.setItem(AUDIO_PERSIST_KEY, JSON.stringify(data))
  } catch { /* ignore */ }
}

function loadAudioPersist(): Partial<DMState> {
  try {
    const raw = localStorage.getItem(AUDIO_PERSIST_KEY)
    if (!raw) return {}
    const data = JSON.parse(raw) as AudioPersist
    if (!data.playingAudioId) return {}
    return {
      playingAudioId: data.playingAudioId,
      audioPlaying: false,
      audioMsgSenderId: data.audioMsgSenderId,
      audioMsgFileName: data.audioMsgFileName,
      audioMsgFilePath: data.audioMsgFilePath,
      audioProgress: data.audioProgress,
      audioDuration: data.audioDuration,
      playbackSpeed: data.playbackSpeed,
      volume: data.volume,
      audioTrackList: data.audioTrackList || [],
    }
  } catch { return {} }
}


export const useDMStore = defineStore('dm', {
  state: (): DMState => {
    const saved = loadAudioPersist()
    return {
      rooms: [],
      messages: [],
      total: 0,
      loading: false,
      currentRoomId: null,
      connected: false,
      unreadCount: 0,
      uploading: false,
      uploadProgress: 0,
      replyTo: null,
      editingMessage: null,
      playingAudioId: saved.playingAudioId || null,
      audioPlaying: false,
      audioMsgSenderId: saved.audioMsgSenderId || null,
      audioMsgFileName: saved.audioMsgFileName || null,
      audioMsgFilePath: saved.audioMsgFilePath || null,
      audioProgress: saved.audioProgress || {},
      audioDuration: saved.audioDuration || {},
      playbackSpeed: saved.playbackSpeed || 1,
      volume: saved.volume ?? 1,
      audioTrackList: saved.audioTrackList || [],
    }
  },

  getters: {
    sortedMessages: (state) => [...state.messages].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    ),
    sortedRooms: (state) => [...state.rooms].sort((a, b) => {
      const aTime = a.last_message_at ? new Date(a.last_message_at).getTime() : 0
      const bTime = b.last_message_at ? new Date(b.last_message_at).getTime() : 0
      return bTime - aTime
    }),
    currentRoom: (state) => state.rooms.find(r => r.id === state.currentRoomId) || null,
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

    _currentUserId(): string {
      const auth = useAuthStore()
      return auth.user?.id || ''
    },

    _addMessage(msg: DirectMessageData) {
      // Server may create a separate text-only message from a file message's content field;
      // skip it since the file message already carries the text.
      if (!msg.file_path && !msg.file_name && msg.content && _pendingContents.has(msg.content)) {
        _pendingContents.delete(msg.content)
        return
      }
      const exists = this.messages.some(m =>
        m.id === msg.id ||
        (!!msg.file_name && !!msg.file_path && m.file_name === msg.file_name && m.file_path === msg.file_path)
      )
      if (!exists) {
        this.messages.push(msg)
        this.total++
      }
      // Update room last message for sorting
      const idx = this.rooms.findIndex(r => r.id === msg.room_id)
      if (idx !== -1) {
        const updated = [...this.rooms]
        updated[idx] = { ...updated[idx], last_message_at: msg.created_at, last_message_content: msg.content || msg.file_name || '' }
        this.rooms = updated
      }
    },

    _removeMessage(id: string) {
      const idx = this.messages.findIndex(m => m.id === id)
      if (idx !== -1) {
        this.messages.splice(idx, 1)
        this.total--
      }
    },

    _updateMessage(id: string, updates: Partial<DirectMessageData>) {
      const idx = this.messages.findIndex(m => m.id === id)
      if (idx !== -1) {
        this.messages[idx] = { ...this.messages[idx], ...updates }
      }
    },

    async fetchRooms() {
      this.loading = true
      try {
        const res = await useApiFetch<DirectMessageRoomData[]>(
          '/api/v1/direct/rooms',
          { headers: this._authHeaders() }
        )
        this.rooms = res
        this.unreadCount = res.reduce((sum, r) => sum + r.unread_count, 0)
      } finally {
        this.loading = false
      }
    },

    async getOrCreateRoom(otherUserId: string): Promise<DirectMessageRoomData> {
      const room = await useApiFetch<DirectMessageRoomData>(
        `/api/v1/direct/rooms/${otherUserId}`,
        { method: 'POST', headers: this._authHeaders() }
      )
      const idx = this.rooms.findIndex(r => r.id === room.id)
      if (idx !== -1) {
        this.rooms[idx] = room
      } else {
        this.rooms.unshift(room)
      }
      this.currentRoomId = room.id
      this.unreadCount = this.rooms.reduce((sum, r) => sum + r.unread_count, 0)
      return room
    },

    async fetchMessages(roomId: string) {
      this.loading = true
      this.currentRoomId = roomId
      try {
        const res = await useApiFetch<{ messages: DirectMessageData[]; total: number }>(
          `/api/v1/direct/rooms/${roomId}/messages`,
          { headers: this._authHeaders() }
        )
        this.messages = res.messages
        this.total = res.total
      } finally {
        this.loading = false
      }
    },

    async sendMessage(roomId: string, content: string) {
      _pendingContents.clear()
      const body: Record<string, any> = { content }
      if (this.replyTo) body.reply_to_id = this.replyTo.messageId
      const msg = await useApiFetch<DirectMessageData>(
        `/api/v1/direct/rooms/${roomId}/messages`,
        { method: 'POST', body, headers: this._authHeaders() }
      )
      this.replyTo = null
      // Update room last message for sorting
      const idx = this.rooms.findIndex(r => r.id === roomId)
      if (idx !== -1) {
        const updated = [...this.rooms]
        updated[idx] = { ...updated[idx], last_message_at: msg.created_at, last_message_content: msg.content || '' }
        this.rooms = updated
      }
      return msg
    },

    async sendFileMessage(roomId: string, file: File, content = '') {
      if (content) _pendingContents.add(content)
      this.uploading = true
      this.uploadProgress = 0
      try {
        const form = new FormData()
        form.append('file', file)
        form.append('content', content)
        if (this.replyTo) form.append('reply_to_id', this.replyTo.messageId)

        const xhr = new XMLHttpRequest()
        xhr.open('POST', `${BASE}/api/v1/direct/rooms/${roomId}/messages/with-file`)
        xhr.setRequestHeader('Authorization', `Bearer ${this._token()}`)
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            this.uploadProgress = Math.round((e.loaded / e.total) * 100)
          }
        }

        const msg = await new Promise<DirectMessageData>((resolve, reject) => {
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

        this.replyTo = null
        // Update room last message for sorting
        const idx = this.rooms.findIndex(r => r.id === roomId)
        if (idx !== -1) {
          const updated = [...this.rooms]
          updated[idx] = { ...updated[idx], last_message_at: msg.created_at, last_message_content: msg.content || msg.file_name || '' }
          this.rooms = updated
        }
        return msg
      } catch (e) {
        if (content) _pendingContents.delete(content)
        throw e
      } finally {
        this.uploading = false
        this.uploadProgress = 0
      }
    },

    async updateMessage(roomId: string, messageId: string, content: string) {
      const msg = await useApiFetch<DirectMessageData>(
        `/api/v1/direct/rooms/${roomId}/messages/${messageId}`,
        { method: 'PATCH', body: { content }, headers: this._authHeaders() }
      )
      this._updateMessage(messageId, msg)
      this.editingMessage = null
      return msg
    },

    async toggleReaction(roomId: string, messageId: string, emoji: string) {
      try {
        const msg = await useApiFetch<DirectMessageData>(
          `/api/v1/direct/rooms/${roomId}/messages/${messageId}/reactions`,
          { method: 'POST', body: { emoji }, headers: this._authHeaders() }
        )
        this._updateMessage(messageId, { reactions: msg.reactions })
        return msg
      } catch (e) {
        console.error('Failed to toggle reaction', e)
        throw e
      }
    },

    async markRoomRead(roomId: string) {
      try {
        await useApiFetch(
          `/api/v1/direct/rooms/${roomId}/read`,
          { method: 'POST', headers: this._authHeaders() }
        )
      } catch { return }
      const room = this.rooms.find(r => r.id === roomId)
      if (room) {
        room.unread_count = 0
      }
      this.unreadCount = this.rooms.reduce((sum, r) => sum + r.unread_count, 0)
    },

    async deleteRoom(roomId: string, scope: 'all' | 'self' = 'self') {
      await useApiFetch(
        `/api/v1/direct/rooms/${roomId}?scope=${scope}`,
        { method: 'DELETE', headers: this._authHeaders() }
      )
      this.rooms = this.rooms.filter(r => r.id !== roomId)
      this.unreadCount = this.rooms.reduce((sum, r) => sum + r.unread_count, 0)
      if (this.currentRoomId === roomId) {
        this.clearMessages()
      }
    },

    async deleteMessage(roomId: string, messageId: string, scope: 'all' | 'self' = 'all') {
      await useApiFetch(
        `/api/v1/direct/rooms/${roomId}/messages/${messageId}?scope=${scope}`,
        { method: 'DELETE', headers: this._authHeaders() }
      )
      if (scope === 'all') {
        this._removeMessage(messageId)
      } else {
        this._updateMessage(messageId, { deleted_by: [this._currentUserId(), ...(this.messages.find(m => m.id === messageId)?.deleted_by || [])] })
      }
    },

    setReplyTo(messageId: string, userName: string, content: string) {
      this.replyTo = { messageId, userName, content }
    },

    clearReplyTo() {
      this.replyTo = null
    },

    setEditingMessage(msg: DirectMessageData | null) {
      this.editingMessage = msg
    },

    connectWebSocket(roomId: string) {
      const auth = useAuthStore()
      if (!auth.accessToken || ws) return

      const wsUrl = BASE.replace(/^http/, 'ws') +
        `/api/v1/direct/ws?room_id=${roomId}&token=${auth.accessToken}`

      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        this.connected = true
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data) as DirectMessageData & { _type?: string; scope?: string; deleted_by?: string; room_id?: string }
        if (data._type === 'room_deleted') {
          const roomId = data.room_id
          if (roomId) {
            this.rooms = this.rooms.filter(r => r.id !== roomId)
            if (this.currentRoomId === roomId) {
              this.clearMessages()
            }
          }
          return
        }
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
          if (data.sender_id !== this._currentUserId()) {
            const room = this.rooms.find(r => r.id === data.room_id)
            if (room) {
              room.other_user_last_seen_at = new Date().toISOString()
              if (room.id !== this.currentRoomId) {
                room.unread_count++
              }
            }
            this.unreadCount = this.rooms.reduce((sum, r) => sum + r.unread_count, 0)
          }
        }
      }

      ws.onclose = () => {
        this.connected = false
        ws = null
        wsReconnectTimer = setTimeout(() => this.connectWebSocket(roomId), 5000)
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
      this.currentRoomId = null
      this.replyTo = null
      this.editingMessage = null
      this.audioTrackList = []
    },

    async heartbeat() {
      try {
        await useApiFetch('/api/v1/users/me/heartbeat', { method: 'POST', headers: this._authHeaders() })
      } catch { /* ignore */ }
    },

    // Audio player actions
    stopAudio() {
      if (audioEl) {
        audioEl.pause()
        audioEl = null
      }
      if (this.playingAudioId) {
        this.audioProgress[this.playingAudioId] = 0
      }
      this.playingAudioId = null
      this.audioPlaying = false
      this.audioMsgSenderId = null
      this.audioMsgFileName = null
      this.audioMsgFilePath = null
      saveAudioPersist(this.$state)
    },

    toggleAudio(msgId: string, filePath: string) {
      if (this.playingAudioId === msgId && audioEl) {
        if (audioEl.paused) {
          audioEl.play().catch(() => {})
          this.audioPlaying = true
        } else {
          audioEl.pause()
          this.audioPlaying = false
        }
        saveAudioPersist(this.$state)
        return
      }
      if (audioEl) {
        audioEl.pause()
      }
      const gen = ++audioGen
      const msg = this.messages.find(m => m.id === msgId)
      this.audioMsgSenderId = msg?.sender_id ?? this.audioMsgSenderId
      this.audioMsgFileName = msg?.file_name ?? this.audioMsgFileName
      this.audioMsgFilePath = filePath
      if (this.messages.length > 0) {
        this.audioTrackList = this.messages
          .filter(m => m.file_name && isAudioFile(m.file_name) && m.file_path)
          .map(m => ({ id: m.id, filePath: m.file_path!, fileName: m.file_name! }))
      }
      const url = BASE + filePath
      const audio = new Audio(url)
      audio.playbackRate = this.playbackSpeed
      audio.volume = this.volume
      const savedTime = this.audioProgress[msgId]
      audio.addEventListener('loadedmetadata', () => {
        this.audioDuration[msgId] = audio.duration
        if (savedTime && savedTime > 0 && savedTime < audio.duration) {
          audio.currentTime = savedTime
        }
      })
      let lastSave = 0
      audio.addEventListener('timeupdate', () => {
        this.audioProgress[msgId] = audio.currentTime
        const now = Date.now()
        if (now - lastSave > 3000) {
          lastSave = now
          saveAudioPersist(this.$state)
        }
      })
      audio.addEventListener('ended', () => {
        if (audioGen === gen) this.stopAudio()
      })
      audio.addEventListener('error', () => {
        if (audioGen === gen) this.stopAudio()
      })
      audio.play().catch(() => {
        if (audioGen === gen) this.stopAudio()
      })
      this.playingAudioId = msgId
      this.audioPlaying = true
      audioEl = audio
      saveAudioPersist(this.$state)
    },

    seekAudio(msgId: string, time: number) {
      if (audioEl && this.playingAudioId === msgId) {
        audioEl.currentTime = time
        saveAudioPersist(this.$state)
      }
    },

    cycleSpeed() {
      const options = [0.5, 1, 1.5, 2]
      const idx = options.indexOf(this.playbackSpeed)
      this.playbackSpeed = options[(idx + 1) % options.length]
      if (audioEl) {
        audioEl.playbackRate = this.playbackSpeed
      }
      saveAudioPersist(this.$state)
    },

    setSpeed(speed: number) {
      this.playbackSpeed = speed
      if (audioEl) {
        audioEl.playbackRate = speed
      }
      saveAudioPersist(this.$state)
    },

    setVolume(v: number) {
      this.volume = v
      if (audioEl) {
        audioEl.volume = v
      }
      saveAudioPersist(this.$state)
    },

    calcProgress(msgId: string): number {
      const dur = this.audioDuration[msgId]
      const cur = this.audioProgress[msgId]
      if (!dur || !cur) return 0
      return Math.min(cur / dur, 1)
    },
  },
})

let audioEl: HTMLAudioElement | null = null
let audioGen = 0
