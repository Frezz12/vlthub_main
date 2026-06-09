<script setup lang="ts">
import type { DirectMessageData } from '~/stores/dm'
import type { UserBadgeBrief } from '@pjasaver/shared-types'
import { resolveApiUrl } from '~/composables/useApiFetch'
import { invoke } from '@tauri-apps/api/core'
import UiAvatarRing from '~/components/UiAvatarRing.vue'
import UiLightbox from '~/components/UiLightbox.vue'

const CHAT_FILE_MAX_SIZE = 100 * 1024 * 1024

const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void } | null
const router = useRouter()

function goToProfile() {
  if (dm.currentRoom?.other_user_username) {
    router.push(`/profile/${dm.currentRoom.other_user_username}`)
  }
}

interface Props {
  otherUserId: string
}

const props = defineProps<Props>()
const dm = useDMStore()
const auth = useAuthStore()

const text = ref('')
const sending = ref(false)
const listRef = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const showEmojiPicker = ref(false)
const reactionPicker = ref<{ msg: DirectMessageData; x: number; y: number } | null>(null)
const contextMenu = ref<{ msg: DirectMessageData; x: number; y: number } | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const chatRoot = ref<HTMLElement | null>(null)
const deleteDialog = ref<DirectMessageData | null>(null)
const downloadingId = ref<string | null>(null)
const downloadAbort = ref<AbortController | null>(null)
const chatReady = ref(false)
const newMessageIds = ref<Set<string>>(new Set())
let initialMessageIds = new Set<string>()

const dragging = ref(false)
let tauriDragUnlisten: (() => void) | null = null

const lightboxOpen = ref(false)
const lightboxMedia = ref<{ url: string; fileName: string }[]>([])
const lightboxIndex = ref(0)

function mediaUrl(filePath: string): string {
  return resolveApiUrl(filePath) || filePath
}

function openLightbox(msg: DirectMessageData, msgs: DirectMessageData[]) {
  const media = msgs.filter(m =>
    m.file_name && m.file_path && (isImageFile(m.file_name) || isVideoFile(m.file_name))
  )
  if (media.length === 0) return
  lightboxMedia.value = media.map(m => ({
    url: mediaUrl(m.file_path!),
    fileName: m.file_name!,
    filePath: m.file_path!,
  }))
  lightboxIndex.value = media.findIndex(m => m.id === msg.id)
  if (lightboxIndex.value === -1) lightboxIndex.value = 0
  lightboxOpen.value = true
}

function isAudioFile(fileName: string): boolean {
  const ext = fileName.split('.').pop()?.toLowerCase()
  return ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'wma', 'opus', 'aiff'].includes(ext || '')
}

function isImageFile(fileName: string): boolean {
  const ext = fileName.split('.').pop()?.toLowerCase()
  return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'avif'].includes(ext || '')
}

function isVideoFile(fileName: string): boolean {
  const ext = fileName.split('.').pop()?.toLowerCase()
  return ['mp4', 'webm', 'mov', 'avi', 'mkv', 'm4v', '3gp'].includes(ext || '')
}

function formatAudioTime(seconds: number): string {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onSeek(msgId: string, e: Event) {
  const input = e.target as HTMLInputElement
  dm.seekAudio(msgId, parseFloat(input.value))
}

function onDragEnterNative(e: DragEvent) {
  e.preventDefault()
  dragging.value = true
}

function onDragOverNative(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'copy'
  }
}

function onDragLeave(e: DragEvent) {
  const target = e.currentTarget as HTMLElement
  const related = e.relatedTarget as HTMLElement
  if (!target.contains(related)) {
    dragging.value = false
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  dragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    const file = files[0]
    if (file.size > CHAT_FILE_MAX_SIZE) {
      toast?.show('Файл превышает 100 МБ', 'error')
      return
    }
    selectedFile.value = file
  }
}

function preventDocDrag(e: DragEvent) {
  e.preventDefault()
}

function isTauri(): boolean {
  return typeof window !== 'undefined' &&
    ((window as any).__TAURI__ !== undefined ||
     (window as any).__TAURI_INTERNALS__ !== undefined)
}

async function loadDroppedFile(filePath: string) {
  try {
    const bytes = await invoke<number[]>('read_file_bytes', { path: filePath })
    const uint8 = new Uint8Array(bytes)
    const blob = new Blob([uint8])
    const fileName = filePath.split('\\').pop() || filePath.split('/').pop() || 'file'
    const file = new File([blob], fileName, { type: blob.type || '' })
    if (file.size > CHAT_FILE_MAX_SIZE) {
      toast?.show('Файл превышает 100 МБ', 'error')
      return
    }
    selectedFile.value = file
  } catch (e) {
    console.error('Failed to read dropped file', e)
    toast?.show('Не удалось прочитать файл', 'error')
  }
}

onMounted(async () => {
  document.addEventListener('mousedown', closeContextMenu)
  document.addEventListener('dragover', preventDocDrag)
  document.addEventListener('drop', preventDocDrag)
  if (chatRoot.value) {
    chatRoot.value.addEventListener('dragenter', onDragEnterNative)
    chatRoot.value.addEventListener('dragover', onDragOverNative)
    chatRoot.value.addEventListener('dragleave', onDragLeave)
    chatRoot.value.addEventListener('drop', onDrop)
  }
  if (isTauri()) {
    try {
      const { getCurrentWindow } = await import('@tauri-apps/api/window')
      tauriDragUnlisten = await getCurrentWindow().onDragDropEvent((event) => {
        if (event.payload.type === 'over') {
          dragging.value = true
        } else if (event.payload.type === 'leave') {
          dragging.value = false
        } else if (event.payload.type === 'drop') {
          dragging.value = false
          const filePath = event.payload.paths[0]
          if (filePath) {
            loadDroppedFile(filePath)
          }
        }
      })
    } catch (e) {
      console.warn('Failed to setup Tauri drag-drop listener', e)
    }
  }
  await loadChat(props.otherUserId)
  if (listRef.value) {
    listRef.value.addEventListener('scroll', onScroll)
  }
  lastSeenTimer = setInterval(() => { lastSeenTick.value++ }, 30000)
  roomRefreshTimer = setInterval(() => {
    if (dm.currentRoomId) dm.fetchRooms()
  }, 120000)
})

onUnmounted(() => {
  if (lastSeenTimer) clearInterval(lastSeenTimer)
  if (roomRefreshTimer) clearInterval(roomRefreshTimer)
  if (listRef.value) {
    listRef.value.removeEventListener('scroll', onScroll)
  }
  if (dm.currentRoomId) markAsRead()
  dm.disconnectWebSocket()
  document.removeEventListener('mousedown', closeContextMenu)
  document.removeEventListener('dragover', preventDocDrag)
  document.removeEventListener('drop', preventDocDrag)
  if (chatRoot.value) {
    chatRoot.value.removeEventListener('dragenter', onDragEnterNative)
    chatRoot.value.removeEventListener('dragover', onDragOverNative)
    chatRoot.value.removeEventListener('dragleave', onDragLeave)
    chatRoot.value.removeEventListener('drop', onDrop)
  }
  if (tauriDragUnlisten) {
    tauriDragUnlisten()
    tauriDragUnlisten = null
  }
})

watch(() => props.otherUserId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    dm.disconnectWebSocket()
    dm.clearMessages()
    await loadChat(newId)
  }
})

async function loadChat(userId: string) {
  chatReady.value = false
  newMessageIds.value = new Set()
  try {
    const room = await dm.getOrCreateRoom(userId)
    await dm.fetchMessages(room.id)
    initialMessageIds = new Set(dm.messages.map(m => m.id))

    const unreadCount = room.unread_count
    if (unreadCount > 0) {
      const otherMsgs = dm.messages
        .filter(m => m.sender_id !== currentUserId.value)
        .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      const startIdx = Math.max(0, otherMsgs.length - unreadCount)
      for (let i = startIdx; i < otherMsgs.length; i++) {
        newMessageIds.value.add(otherMsgs[i].id)
      }
    }

    dm.connectWebSocket(room.id)
    dm.clearUnread()
    nextTick(() => scrollToBottom(false))
  } catch {
    toast?.show('Не удалось открыть чат', 'error')
  } finally {
    chatReady.value = true
  }
}

watch(() => dm.messages.length, () => {
  const wasNearBottom = listRef.value &&
    listRef.value.scrollTop + listRef.value.clientHeight >= listRef.value.scrollHeight - 100

  if (!wasNearBottom) {
    for (const msg of dm.messages) {
      if (!initialMessageIds.has(msg.id) && msg.sender_id !== currentUserId.value) {
        newMessageIds.value.add(msg.id)
      }
    }
  }

  nextTick(() => {
    if (wasNearBottom && dm.currentRoomId) {
      dm.markRoomRead(dm.currentRoomId)
    }
    scrollToBottom(false)
  })
})

const currentUserId = computed(() => auth.user?.id)

const visibleMessages = computed(() =>
  dm.sortedMessages.filter(msg => !msg.deleted_by?.includes(currentUserId.value ?? ''))
)

let lastSeenTimer: ReturnType<typeof setInterval> | null = null
let roomRefreshTimer: ReturnType<typeof setInterval> | null = null
const ONLINE_WINDOW = 5 * 60 * 1000
const lastSeenTick = ref(0)

const lastSeenText = computed(() => {
  const _ = lastSeenTick.value
  const room = dm.currentRoom
  if (!room) return ''
  const lastSeen = room.other_user_last_seen_at
  if (!lastSeen) return 'Нет соединения'
  const now = Date.now()
  const diff = now - new Date(lastSeen).getTime()
  if (diff < ONLINE_WINDOW) return 'В сети'
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `Был(а) ${minutes} мин. назад`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `Был(а) ${hours} ч. назад`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'Был(а) вчера'
  return `Был(а) ${days} дн. назад`
})

const lastSeenDot = computed(() => {
  const room = dm.currentRoom
  if (!room) return false
  return !!room.other_user_last_seen_at || !!room.unread_count
})

const isOnline = computed(() => {
  const _ = lastSeenTick.value
  const room = dm.currentRoom
  if (!room?.other_user_last_seen_at) return false
  return Date.now() - new Date(room.other_user_last_seen_at).getTime() < ONLINE_WINDOW
})

function onScroll() {
  if (listRef.value && dm.currentRoomId) {
    if (listRef.value.scrollTop + listRef.value.clientHeight >= listRef.value.scrollHeight - 50) {
      dm.markRoomRead(dm.currentRoomId)
      newMessageIds.value = new Set()
    }
  }
}

function scrollToBottom(markRead = true) {
  if (listRef.value) {
    const isNearBottom = listRef.value.scrollTop + listRef.value.clientHeight >= listRef.value.scrollHeight - 100
    listRef.value.scrollTop = listRef.value.scrollHeight
    if (markRead && isNearBottom && dm.currentRoomId) {
      dm.markRoomRead(dm.currentRoomId)
      newMessageIds.value = new Set()
    }
  }
}

function markAsRead() {
  if (dm.currentRoomId) {
    dm.markRoomRead(dm.currentRoomId)
    newMessageIds.value = new Set()
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  if (d.toDateString() === today.toDateString()) return 'Сегодня'
  if (d.toDateString() === yesterday.toDateString()) return 'Вчера'
  return d.toLocaleDateString([], { day: 'numeric', month: 'short' })
}

function shouldShowDate(msg: DirectMessageData, idx: number): boolean {
  if (idx === 0) return true
  const prev = dm.messages[idx - 1]
  return new Date(msg.created_at).toDateString() !== new Date(prev.created_at).toDateString()
}

function isFirstInGroup(idx: number): boolean {
  if (idx === 0) return true
  const prev = visibleMessages.value[idx - 1]
  const curr = visibleMessages.value[idx]
  if (!prev || !curr) return true
  if (prev.sender_id !== curr.sender_id) return true
  const prevTime = new Date(prev.created_at).getTime()
  const currTime = new Date(curr.created_at).getTime()
  return currTime - prevTime > 60_000
}

function isLastInGroup(idx: number): boolean {
  if (idx === visibleMessages.value.length - 1) return true
  const curr = visibleMessages.value[idx]
  const next = visibleMessages.value[idx + 1]
  if (!curr || !next) return true
  if (curr.sender_id !== next.sender_id) return true
  return false
}

function isOwnMessage(msg: DirectMessageData) {
  return msg.sender_id === currentUserId.value
}

const EMOTIONAL_PREFIXES = ['yes', 'yeah', 'yep', 'yess', 'awesome', 'fantastic', 'amazing', 'great', 'perfect', 'wonderful', 'love', 'sure', 'absolutely', 'definitely', 'totally', 'nice', 'cool', 'да', 'конечно', 'отлично', 'прекрасно', 'супер', 'класс', 'ага', 'ладно', 'ок', 'ok']
const EMOTIONAL_CHARS = ['!', '🥰', '🎉', '❤️', '🔥', '😍', '💯', '✨', '🙌', '👏', '💪', '🤩']

function isEmotionalResponse(content: string): boolean {
  if (!content) return false
  const t = content.trim()
  if (EMOTIONAL_CHARS.some(c => t.includes(c))) return true
  if (t.endsWith('!')) return true
  if (EMOTIONAL_PREFIXES.some(p => t.toLowerCase().startsWith(p))) return true
  return false
}

function openFilePicker() {
  fileInput.value?.click()
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
  }
  input.value = ''
}

function cancelFile() {
  selectedFile.value = null
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const MAX_IMAGE_DIMENSION = 1920
const IMAGE_QUALITY = 0.82

async function compressImage(file: File): Promise<File> {
  if (!isImageFile(file.name)) return file

  const ext = file.name.split('.').pop()?.toLowerCase()
  // Never compress GIF, SVG, AVIF (too lossy or already efficient)
  if (ext === 'gif' || ext === 'svg' || ext === 'avif') return file

  const originalType = file.type || 'image/jpeg'

  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)

    img.onload = () => {
      URL.revokeObjectURL(url)
      let { width, height } = img

      // Resize only if exceeds max dimension
      if (Math.max(width, height) <= MAX_IMAGE_DIMENSION && ext !== 'png') {
        // For JPEG/WEBP already small enough, try compressing anyway
        if (ext === 'jpg' || ext === 'jpeg' || ext === 'webp') {
          if (file.size < 500 * 1024) {
            resolve(file)
            return
          }
        } else {
          resolve(file)
          return
        }
      }

      if (width > MAX_IMAGE_DIMENSION || height > MAX_IMAGE_DIMENSION) {
        const ratio = Math.min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
        width = Math.round(width * ratio)
        height = Math.round(height * ratio)
      }

      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      if (!ctx) { resolve(file); return }

      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
      ctx.drawImage(img, 0, 0, width, height)

      const mimeType = ext === 'png' ? 'image/png' : 'image/jpeg'
      const quality = ext === 'png' ? 0.9 : IMAGE_QUALITY

      canvas.toBlob(async (blob) => {
        if (!blob || blob.size >= file.size) {
          resolve(file)
          return
        }
        const newName = file.name.replace(/\.[^.]+$/, ext === 'png' ? '.png' : '.jpg')
        const compressed = new File([blob], newName, { type: blob.type })
        resolve(compressed)
      }, mimeType, quality)
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      resolve(file)
    }

    img.src = url
  })
}

async function send() {
  if (sending.value || dm.uploading || !dm.currentRoomId) return

  sending.value = true

  if (dm.editingMessage) {
    const content = text.value.trim()
    if (!content) { sending.value = false; return }
    try {
      await dm.updateMessage(dm.currentRoomId, dm.editingMessage.id, content)
      text.value = ''
      markAsRead()
    } finally {
      sending.value = false
    }
    return
  }

  const content = text.value.trim()

  if (selectedFile.value) {
    if (selectedFile.value.size > CHAT_FILE_MAX_SIZE) {
      toast?.show('Файл превышает 100 МБ', 'error')
      selectedFile.value = null
      sending.value = false
      return
    }

    const fileToUpload = isImageFile(selectedFile.value.name)
      ? await compressImage(selectedFile.value)
      : selectedFile.value

    try {
      await dm.sendFileMessage(dm.currentRoomId, fileToUpload, content)
      text.value = ''
      selectedFile.value = null
      markAsRead()
      nextTick(() => scrollToBottom())
    } finally {
      sending.value = false
    }
    return
  }

  if (!content) { sending.value = false; return }
  try {
    await dm.sendMessage(dm.currentRoomId, content)
    text.value = ''
    markAsRead()
    nextTick(() => scrollToBottom())
  } finally {
    sending.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
  if (e.key === 'Escape') {
    cancelAll()
  }
}

function cancelAll() {
  if (dm.editingMessage) dm.setEditingMessage(null)
  if (dm.replyTo) dm.clearReplyTo()
  selectedFile.value = null
  showEmojiPicker.value = false
}

function startReply(msg: DirectMessageData) {
  dm.setReplyTo(msg.id, msg.sender_name, msg.content)
  contextMenu.value = null
}

function startEdit(msg: DirectMessageData) {
  text.value = msg.content
  dm.setEditingMessage(msg)
  contextMenu.value = null
  nextTick(() => onTextareaInput())
}

async function toggleReaction(msg: DirectMessageData, emoji: string) {
  if (!dm.currentRoomId) return
  await dm.toggleReaction(dm.currentRoomId, msg.id, emoji)
  reactionPicker.value = null
}

async function deleteMsg(msg: DirectMessageData) {
  contextMenu.value = null
  deleteDialog.value = msg
}

async function confirmDelete(scope: 'all' | 'self') {
  const msg = deleteDialog.value
  if (!msg || !dm.currentRoomId) return
  deleteDialog.value = null
  await dm.deleteMessage(dm.currentRoomId, msg.id, scope)
}

function onContextMenu(e: MouseEvent, msg: DirectMessageData) {
  const menuWidth = 180
  const menuHeight = 260
  const x = Math.min(e.clientX, window.innerWidth - menuWidth - 12)
  const y = Math.min(e.clientY, window.innerHeight - menuHeight - 12)
  contextMenu.value = { msg, x: Math.max(12, x), y: Math.max(12, y) }
}

function closeContextMenu() {
  contextMenu.value = null
  reactionPicker.value = null
}

function onTextareaInput() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

function messageBadge(msg: DirectMessageData): UserBadgeBrief | null {
  if (!msg.sender_badge_ring_gradient) return null
  return {
    id: '',
    name: msg.sender_badge_name || '',
    icon_svg: msg.sender_badge_icon_svg || '',
    avatar_ring_gradient: msg.sender_badge_ring_gradient,
    avatar_ring_effect: msg.sender_badge_ring_effect || null,
    is_active: true,
    description: null,
  }
}

function downloadFile(msg: DirectMessageData) {
  if (downloadingId.value) return
  if (!msg.file_path || !msg.file_name) return

  if (dm.playingAudioId === msg.id) dm.stopAudio()

  downloadingId.value = msg.id
  downloadAbort.value = new AbortController()

  const url = resolveApiUrl(msg.file_path) || msg.file_path
  fetch(url, {
    signal: downloadAbort.value.signal,
    headers: auth.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {},
  })
    .then(res => res.blob())
    .then(blob => {
      if (downloadAbort.value?.signal.aborted) return
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = msg.file_name!
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(a.href), 10000)
    })
    .catch((e) => {
      if (e.name === 'AbortError') return
      toast?.show('Ошибка при скачивании', 'error')
    })
    .finally(() => {
      if (downloadingId.value === msg.id) downloadingId.value = null
    })
}

function cancelDownload(msg: DirectMessageData) {
  if (downloadingId.value === msg.id) {
    downloadAbort.value?.abort()
    downloadAbort.value = null
    downloadingId.value = null
  }
}

async function saveFileAs(msg: DirectMessageData) {
  try {
    const path = await invoke<string | null>('save_file_dialog', { defaultName: msg.file_name })
    if (!path) return

    const url = resolveApiUrl(msg.file_path) || msg.file_path!
    await invoke('download_file', {
      url,
      dest: path,
      label: msg.file_name || 'file',
      token: auth.accessToken || null,
    })
    toast?.show('Файл сохранён', 'success')
  } catch (e: any) {
    if (e?.toString?.()?.includes?.('cancelled')) {
      toast?.show('Скачивание отменено', 'info')
    } else {
      toast?.show(e?.toString() || 'Ошибка при сохранении', 'error')
    }
  }
}

async function onLightboxSaveAs(filePath: string, fileName: string) {
  try {
    const path = await invoke<string | null>('save_file_dialog', { defaultName: fileName })
    if (!path) return
    const url = resolveApiUrl(filePath) || filePath
    await invoke('download_file', { url, dest: path, label: fileName, token: auth.accessToken || null })
    toast?.show('Файл сохранён', 'success')
  } catch (e: any) {
    if (e?.toString?.()?.includes?.('cancelled')) {
      toast?.show('Скачивание отменено', 'info')
    } else {
      toast?.show(e?.toString() || 'Ошибка при сохранении', 'error')
    }
  }
}

function scrollToMessage(messageId: string) {
  const el = document.getElementById('msg-' + messageId)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  el.classList.add('highlight-message')
  setTimeout(() => el.classList.remove('highlight-message'), 1500)
}

const EMOJIS = [
  '😀','😃','😄','😁','😅','😂','🤣','😊','😇','🙂','😉','😌','😍','🥰','😘',
  '😗','😋','😛','😜','🤪','😝','🤑','🤗','🤩','🤔','🤨','😐','😑','😶','😏',
  '😒','🙄','😬','🤥','😌','😔','😪','🤤','😴','😷','🤒','🤕','🤢','🤮','🤧',
  '🥵','🥶','🥴','😵','🤯','🤠','🥳','😎','🤓','🧐','😕','😟','🙁','😮','😯',
  '😲','😳','🥺','😢','😭','😤','😡','🤬','👍','👎','👌','✌','🤞','🤟','🤘',
  '🤙','👋','🤚','✋','👏','🙌','👐','🤲','🙏','💪','🤝','❤️','🧡','💛','💚',
  '💙','💜','🖤','🤍','🤎','💕','💗','💖','💘','💝','🎉','🎊','✨','🔥','⭐',
  '🌟','💯','✅','❌','🎯','🎨','🎵','🎶','💡','📌','📍','🔔','🔕','💬','🗨','💭',
]

const REACTION_EMOJIS = [
  '👍', '❤️', '😂', '😮', '😢', '😡', '🎉', '🔥',
  '👏', '💯', '✅', '❌', '🤔', '👀', '💪', '🙏',
  '✨', '⭐', '🎊', '🥳',
]

function declOfNum(n: number, titles: [string, string, string]): string {
  return titles[n % 10 === 1 && n % 100 !== 11 ? 0 : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? 1 : 2]
}

function insertEmoji(emoji: string) {
  const el = textareaRef.value
  if (!el) {
    text.value += emoji
    return
  }
  const start = el.selectionStart
  const end = el.selectionEnd
  const newText = text.value.substring(0, start) + emoji + text.value.substring(end)
  text.value = newText
  showEmojiPicker.value = false
  nextTick(() => {
    const pos = start + emoji.length
    el.setSelectionRange(pos, pos)
    el.focus()
    onTextareaInput()
  })
}
</script>

<template>
  <div
    ref="chatRoot"
    class="flex flex-col h-full relative bg-surface"
  >
    <!-- Drag overlay (full component) -->
    <div
      v-show="dragging"
      class="absolute inset-0 z-50 flex items-center justify-center bg-surface/70 backdrop-blur-sm rounded-2xl border-2 border-dashed border-primary/30 m-3 pointer-events-none"
    >
      <div class="flex flex-col items-center gap-3 text-primary/50">
        <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        <span class="text-sm font-medium">Отпустите файл для отправки</span>
      </div>
    </div>

    <!-- Header -->
    <div class="flex items-center gap-3 px-4 py-3 shrink-0 bg-surface/60 backdrop-blur-2xl border-b border-border/20">
      <div class="flex items-center gap-3 min-w-0 cursor-pointer" @click="goToProfile">
        <div class="relative shrink-0">
          <UiAvatarRing
            v-if="dm.currentRoom && messageBadge({ sender_badge_ring_gradient: dm.currentRoom.other_user_badge_ring_gradient, sender_badge_icon_svg: dm.currentRoom.other_user_badge_icon_svg, sender_badge_ring_effect: dm.currentRoom.other_user_badge_ring_effect, sender_badge_name: dm.currentRoom.other_user_badge_name } as any)"
            :src="dm.currentRoom?.other_user_avatar"
            :name="dm.currentRoom?.other_user_name"
            :badge="messageBadge({ sender_badge_ring_gradient: dm.currentRoom.other_user_badge_ring_gradient, sender_badge_icon_svg: dm.currentRoom.other_user_badge_icon_svg, sender_badge_ring_effect: dm.currentRoom.other_user_badge_ring_effect, sender_badge_name: dm.currentRoom.other_user_badge_name } as any)!"
            size="sm"
          />
          <div v-else class="w-10 h-10 rounded-full bg-gradient-to-br from-primary/8 to-primary/3 text-primary flex items-center justify-center text-sm font-medium overflow-hidden shadow-sm ring-1 ring-black/[0.03]">
            <img v-if="dm.currentRoom?.other_user_avatar" :src="dm.currentRoom.other_user_avatar" class="w-full h-full object-cover" />
            <span v-else>{{ dm.currentRoom?.other_user_name?.charAt(0)?.toUpperCase() || '?' }}</span>
          </div>
          <span
            v-if="isOnline"
            class="absolute -bottom-[1px] -right-[1px] w-[11px] h-[11px] rounded-full bg-success ring-[2.5px] ring-surface/80 online-dot-sm"
          />
        </div>
        <div class="min-w-0">
          <p class="text-[15px] font-semibold text-foreground truncate leading-tight flex items-center gap-1.5">
            {{ dm.currentRoom?.other_user_name || 'Загрузка...' }}
          </p>
          <p class="text-[12px] leading-relaxed mt-px flex items-center gap-1">
            <span :class="isOnline ? 'text-success font-medium' : 'text-secondary/40'">{{ lastSeenText }}</span>
            <span v-if="lastSeenDot && !isOnline" class="w-0.5 h-0.5 rounded-full bg-secondary/30" />
          </p>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div
      ref="listRef"
      class="flex-1 overflow-y-auto px-4 py-4 scroll-smooth dm-chat-bg relative"
    >
      <div v-if="dm.loading && dm.messages.length === 0" class="flex items-center justify-center py-16">
        <div class="w-6 h-6 border-[2.5px] border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>

      <div v-else-if="dm.messages.length === 0" class="flex flex-col items-center justify-center py-20 text-center px-8">
        <div class="w-20 h-20 rounded-[24px] bg-gradient-to-br from-primary/8 to-primary/3 text-primary/25 flex items-center justify-center mb-5 shadow-sm ring-1 ring-black/[0.02]">
          <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="0.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
        </div>
        <p class="text-[15px] font-semibold text-foreground/50 mb-1.5">Пока нет сообщений</p>
        <p class="text-xs text-secondary/40 leading-relaxed max-w-[260px]">Начните разговор — отправьте первое сообщение или поделитесь файлом</p>
      </div>

      <template v-for="(msg, idx) in visibleMessages" :key="msg.id">
        <div v-if="shouldShowDate(msg, idx)" class="flex items-center justify-center py-4 px-4">
          <span class="text-[11px] font-medium text-secondary/30 tracking-wider uppercase select-none">{{ formatDate(msg.created_at) }}</span>
        </div>
        <div
          v-if="newMessageIds.has(msg.id) && (idx === 0 || !newMessageIds.has(visibleMessages[idx - 1].id))"
          class="flex items-center gap-3 py-2 px-4"
        >
          <span class="h-px flex-1 bg-primary/15" />
          <span class="text-[9px] font-semibold text-primary/30 shrink-0 tracking-widest uppercase">Новые</span>
          <span class="h-px flex-1 bg-primary/15" />
        </div>

        <div
          :id="'msg-' + msg.id"
          class="flex gap-2 items-end px-4 transition-all duration-150"
          :class="[
            isFirstInGroup(idx) ? 'mt-1.5' : 'mt-[1px]',
            isLastInGroup(idx) ? 'mb-1.5' : 'mb-0',
            isOwnMessage(msg) ? 'justify-end' : '',
          ]"
          @contextmenu.prevent="msg.content !== undefined && onContextMenu($event, msg)"
        >
          <div v-if="!isOwnMessage(msg) && isFirstInGroup(idx)" class="shrink-0 mb-1">
            <UiAvatarRing
              v-if="messageBadge(msg)"
              :src="msg.sender_avatar"
              :name="msg.sender_name"
              :badge="messageBadge(msg)!"
              size="sm"
            />
            <div v-else class="w-7 h-7 rounded-full bg-gradient-to-br from-primary/8 to-primary/3 text-primary/60 flex items-center justify-center text-[9px] font-medium shadow-sm ring-1 ring-black/[0.02]">
              {{ msg.sender_name?.charAt(0)?.toUpperCase() || '?' }}
            </div>
          </div>
          <div v-if="isOwnMessage(msg) && isFirstInGroup(idx)" class="w-7 shrink-0" />

          <div class="max-w-[72%] min-w-0 group relative">
            <div
              v-if="isFirstInGroup(idx) && !isOwnMessage(msg)"
              class="flex items-center gap-1 mb-1 ml-1.5"
            >
              <span class="text-[11px] font-semibold text-foreground/60">{{ msg.sender_name }}</span>
              <UserBadgeIcon v-if="messageBadge(msg)" :badge="messageBadge(msg)!" size="sm" />
            </div>

            <!-- Reply-only message (no text content) -->
            <div
              v-if="msg.reply_to_id && !msg.content"
              class="mb-1 rounded-xl p-2 border-l-[3px] cursor-pointer hover:opacity-80 transition-all"
              :class="isOwnMessage(msg) ? 'reply-quote-own' : 'reply-quote-other'"
              @click="scrollToMessage(msg.reply_to_id)"
            >
              <p class="text-[9px] font-semibold" :class="isOwnMessage(msg) ? 'text-white/80' : 'text-primary'">{{ msg.reply_to_sender_name || 'Ответ' }}</p>
              <p class="text-[9px] leading-tight truncate mt-px" :class="isOwnMessage(msg) ? 'text-white/60' : 'text-secondary/50'">{{ msg.reply_to_content }}</p>
            </div>

            <!-- Text bubble -->
            <div
              v-if="msg.content && !(msg.file_name && (isImageFile(msg.file_name) || isVideoFile(msg.file_name)))"
              class="px-[16px] py-[11px] text-[15px] leading-relaxed break-words relative transition-all duration-200"
              :class="[
                isOwnMessage(msg)
                  ? 'bubble-own'
                  : 'bubble-other',
                isFirstInGroup(idx)
                  ? (isOwnMessage(msg) ? 'rounded-[18px] rounded-br-[6px]' : 'rounded-[18px] rounded-bl-[6px]')
                  : 'rounded-[18px]',
              ]"
            >
              <div
                v-if="msg.reply_to_id"
                class="mb-2 -mx-[10px] -mt-[7px] p-2.5 border-l-[3px] rounded-[12px] cursor-pointer hover:opacity-90 transition-all duration-200"
                :class="isOwnMessage(msg) ? 'reply-quote-own' : 'reply-quote-other'"
                @click="scrollToMessage(msg.reply_to_id)"
              >
                <p class="text-[10px] font-semibold" :class="isOwnMessage(msg) ? 'text-white/90' : 'text-primary'">{{ msg.reply_to_sender_name || 'Ответ' }}</p>
                <p class="text-[10px] leading-tight mt-0.5" :class="isOwnMessage(msg) ? 'text-white/70' : 'text-secondary/50'">{{ msg.reply_to_content }}</p>
              </div>
              <span class="leading-relaxed">{{ msg.content }}</span>
              <span v-if="msg.edited_at" class="text-[10px] opacity-25 ml-1 select-none">ред.</span>
            </div>

            <!-- Audio player (Apple-style) -->
            <div
              v-if="msg.file_name && isAudioFile(msg.file_name)"
              class="mt-1.5 overflow-hidden transition-all duration-200 relative"
              :class="[
                isOwnMessage(msg)
                  ? 'bubble-own'
                  : 'bubble-other',
                isFirstInGroup(idx)
                  ? (isOwnMessage(msg) ? 'rounded-[18px] rounded-br-[6px]' : 'rounded-[18px] rounded-bl-[6px]')
                  : 'rounded-[18px]',
              ]"
            >
              <div class="flex items-center gap-3 px-4 py-3">
                <!-- Play button with progress ring -->
                <div class="relative shrink-0">
                  <button
                    class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 active:scale-90"
                    :class="isOwnMessage(msg)
                      ? 'bg-white/15 text-white hover:bg-white/25'
                      : 'bg-primary/10 text-primary hover:bg-primary/18'"
                    @click.stop="msg.file_path && dm.toggleAudio(msg.id, msg.file_path)"
                  >
                    <svg v-if="dm.playingAudioId !== msg.id || !dm.audioPlaying" class="w-[18px] h-[18px] ml-px" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8.75 5.5a.75.75 0 0 0-1.125.65v11.7a.75.75 0 0 0 1.125.65l10.125-5.85a.75.75 0 0 0 0-1.3L8.75 5.5Z"/>
                    </svg>
                    <svg v-else class="w-[15px] h-[15px]" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                    </svg>
                  </button>
                  <!-- Circular progress ring -->
                  <svg
                    v-if="dm.playingAudioId === msg.id && dm.audioDuration[msg.id]"
                    class="absolute inset-0 w-10 h-10 -rotate-90 pointer-events-none"
                    viewBox="0 0 40 40"
                  >
                    <circle
                      cx="20" cy="20" r="17"
                      fill="none"
                      :stroke="isOwnMessage(msg) ? 'rgba(255,255,255,0.25)' : 'color-mix(in srgb, var(--color-primary) 15%, transparent)'"
                      stroke-width="2.5"
                    />
                    <circle
                      cx="20" cy="20" r="17"
                      fill="none"
                      :stroke="isOwnMessage(msg) ? '#fff' : 'var(--color-primary)'"
                      stroke-width="2.5"
                      stroke-linecap="round"
                      :stroke-dasharray="2 * Math.PI * 17"
                      :stroke-dashoffset="2 * Math.PI * 17 * (1 - dm.calcProgress(msg.id))"
                      class="transition-all duration-300"
                    />
                  </svg>
                </div>

                <!-- Info column -->
                <div class="min-w-0 flex-1">
                  <p class="text-[13px] font-semibold truncate leading-tight">{{ msg.file_name }}</p>
                  <p v-if="msg.file_size" class="text-[10px] leading-relaxed mt-0.5" :class="isOwnMessage(msg) ? 'text-white/70' : 'text-secondary/45'">{{ formatFileSize(msg.file_size) }}</p>
                  <div class="flex items-center gap-2 mt-1.5">
                    <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums" :class="isOwnMessage(msg) ? 'text-white/75' : 'text-secondary/45'">
                      {{ formatAudioTime(dm.audioProgress[msg.id] || 0) }}
                    </span>
                    <div class="flex-1 relative h-[5px] rounded-full" :class="isOwnMessage(msg) ? 'bg-white/20' : 'bg-primary/10'">
                      <div
                        class="absolute inset-y-0 left-0 rounded-full transition-all duration-300"
                        :class="isOwnMessage(msg) ? 'bg-white/90' : 'bg-primary'"
                        :style="{ width: (dm.calcProgress(msg.id) * 100) + '%' }"
                      />
                      <input
                        type="range"
                        min="0"
                        :max="dm.audioDuration[msg.id] || 0"
                        :value="dm.audioProgress[msg.id] || 0"
                        class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        @input="onSeek(msg.id, $event)"
                        @click.stop
                      />
                    </div>
                    <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums" :class="isOwnMessage(msg) ? 'text-white/75' : 'text-secondary/45'">
                      {{ formatAudioTime(dm.audioDuration[msg.id] || 0) }}
                    </span>
                  </div>
                </div>

                <!-- Speed + Download -->
                <div class="flex flex-col items-center gap-1 shrink-0">
                  <button
                    class="text-[10px] font-bold leading-none px-2 py-1.5 rounded-lg transition-all duration-200 hover:scale-105 active:scale-95 tabular-nums"
                    :class="isOwnMessage(msg)
                      ? 'text-white/70 hover:bg-white/15'
                      : 'text-secondary/45 hover:text-primary hover:bg-primary/10'"
                    @click.stop="dm.cycleSpeed()"
                    title="Скорость воспроизведения"
                  >{{ dm.playbackSpeed }}x</button>
                  <button
                    class="w-7 h-7 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95"
                    :class="isOwnMessage(msg)
                      ? 'text-white/60 hover:text-white hover:bg-white/15'
                      : 'text-secondary/45 hover:text-primary hover:bg-primary/10'"
                    @click.stop="msg.file_path && saveFileAs(msg)"
                    title="Сохранить как"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- Image attachment -->
            <div
              v-else-if="msg.file_name && isImageFile(msg.file_name)"
              class="mt-1.5 overflow-hidden transition-all duration-200 relative cursor-pointer group"
              :class="[
                isOwnMessage(msg)
                  ? 'bubble-own'
                  : 'bubble-other',
                isFirstInGroup(idx)
                  ? (isOwnMessage(msg) ? 'rounded-[18px] rounded-br-[6px]' : 'rounded-[18px] rounded-bl-[6px]')
                  : 'rounded-[18px]',
              ]"
              @click="openLightbox(msg, dm.messages)"
            >
              <div class="relative overflow-hidden" :class="isFirstInGroup(idx) ? (isOwnMessage(msg) ? 'rounded-[18px] rounded-br-[6px]' : 'rounded-[18px] rounded-bl-[6px]') : 'rounded-[18px]'">
                <img
                  :src="mediaUrl(msg.file_path!)"
                  :alt="msg.file_name"
                  class="w-full max-h-[300px] object-contain"
                  loading="lazy"
                  draggable="false"
                />
                <!-- Hover overlay -->
                <div class="absolute inset-0 bg-black/0 group-hover:bg-black/8 transition-all duration-200 flex items-center justify-center">
                  <div class="w-11 h-11 rounded-full bg-black/30 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200 scale-75 group-hover:scale-100 backdrop-blur-sm">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
                    </svg>
                  </div>
                </div>
              </div>
              <div v-if="msg.content || msg.file_size" class="flex items-center justify-between px-4 py-3">
                <p v-if="msg.content" class="text-sm font-medium truncate" :class="isOwnMessage(msg) ? 'text-white/90' : 'text-foreground'">{{ msg.content }}</p>
                <p v-if="msg.file_size" class="text-[10px] shrink-0 ml-2" :class="isOwnMessage(msg) ? 'text-white/70' : 'text-secondary/45'">{{ formatFileSize(msg.file_size) }}</p>
              </div>
            </div>

            <!-- Video attachment -->
            <div
              v-else-if="msg.file_name && isVideoFile(msg.file_name)"
              class="mt-1.5 overflow-hidden transition-all relative cursor-pointer group"
              :class="[
                isOwnMessage(msg)
                  ? 'bubble-own'
                  : 'bubble-other',
                isFirstInGroup(idx)
                  ? (isOwnMessage(msg) ? 'rounded-[18px] rounded-br-[6px]' : 'rounded-[18px] rounded-bl-[6px]')
                  : 'rounded-[18px]',
              ]"
              @click="openLightbox(msg, dm.messages)"
            >
              <div class="relative bg-black/20 flex items-center justify-center min-h-[100px]" :class="isFirstInGroup(idx) ? (isOwnMessage(msg) ? 'rounded-[14px] rounded-br-[4px]' : 'rounded-[14px] rounded-bl-[4px]') : 'rounded-[14px]'">
                  <div class="w-12 h-12 rounded-full bg-black/40 flex items-center justify-center backdrop-blur-sm">
                  <svg class="w-5 h-5 ml-px text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.75 5.5a.75.75 0 0 0-1.125.65v11.7a.75.75 0 0 0 1.125.65l10.125-5.85a.75.75 0 0 0 0-1.3L8.75 5.5Z" />
                  </svg>
                </div>
              </div>
              <div v-if="msg.content || msg.file_size" class="flex items-center justify-between px-3 py-2">
                <p v-if="msg.content" class="text-xs font-medium truncate" :class="isOwnMessage(msg) ? 'text-white/80' : 'text-foreground'">{{ msg.content }}</p>
                <p v-if="msg.file_size" class="text-[10px] shrink-0 ml-2" :class="isOwnMessage(msg) ? 'text-white/50' : 'text-secondary/45'">{{ formatFileSize(msg.file_size) }}</p>
              </div>
            </div>

            <!-- File attachment (non-media) -->
            <div
              v-else-if="msg.file_name"
              class="mt-1.5 overflow-hidden transition-all relative"
              :class="[
                isOwnMessage(msg)
                  ? 'bubble-own'
                  : 'bubble-other',
                isFirstInGroup(idx)
                  ? (isOwnMessage(msg) ? 'rounded-[18px] rounded-br-[6px]' : 'rounded-[18px] rounded-bl-[6px]')
                  : 'rounded-[18px]',
              ]"
              :style="!downloadingId && msg.file_path ? 'cursor: pointer' : ''"
              @click="!downloadingId && msg.file_path && downloadFile(msg)"
            >
              <div class="flex items-center gap-3 px-4 py-3">
                <div
                  class="w-10 h-10 rounded-[12px] flex items-center justify-center shrink-0"
                  :class="isOwnMessage(msg) ? 'bg-white/12 text-white' : 'bg-primary/10 text-primary'"
                >
                  <svg v-if="downloadingId !== msg.id" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                  <svg v-else class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-[13px] font-medium truncate leading-tight">{{ msg.file_name }}</p>
                  <p v-if="msg.file_size" class="text-[10px] leading-relaxed mt-px" :class="isOwnMessage(msg) ? 'text-white/60' : 'text-secondary/45'">{{ formatFileSize(msg.file_size) }}</p>
                </div>
                <div
                  v-if="downloadingId === msg.id"
                  class="w-10 h-10 rounded-[12px] flex items-center justify-center cursor-pointer transition-colors"
                  :class="isOwnMessage(msg) ? 'hover:bg-white/8' : 'hover:bg-primary/10'"
                  @click.stop="cancelDownload(msg)"
                >
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
              </div>
            </div>

            <!-- Reactions -->
            <div
              v-if="msg.reactions && Object.keys(msg.reactions).length > 0"
              class="flex flex-wrap gap-1 mt-0.5"
              :class="isOwnMessage(msg) ? 'justify-end' : ''"
            >
              <button
                v-for="(users, emoji) in msg.reactions"
                :key="emoji"
                class="inline-flex items-center gap-0.5 px-[7px] py-[2.5px] rounded-[10px] text-sm border transition-all duration-200 hover:scale-110 active:scale-95 select-none"
                :class="users.includes(currentUserId ?? '') ? 'bg-primary/8 border-primary/20 text-primary shadow-sm' : 'bg-surface-elevated/80 border-border/25 text-secondary/45 hover:bg-surface hover:border-secondary/20'"
                @click="toggleReaction(msg, emoji)"
              >
                <span class="text-xs leading-none">{{ emoji }}</span>
                <span class="text-[9px] font-semibold tabular-nums">{{ users.length }}</span>
              </button>
            </div>

            <!-- Time + edited -->
            <div
              class="flex items-center gap-1 mt-[3px] px-1 transition-opacity duration-200"
              :class="isOwnMessage(msg) ? 'justify-end opacity-40' : 'opacity-35'"
            >
              <span class="text-[9px] text-secondary/40 font-medium leading-none">{{ formatTime(msg.created_at) }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Bottom input area -->
    <div class="shrink-0 border-t border-border/15 bg-surface/60 backdrop-blur-2xl">
      <!-- Reply bar -->
      <div
        v-if="dm.replyTo"
        class="flex items-center gap-2 mx-3 mt-2 mb-1 px-3.5 py-2.5 rounded-2xl bg-primary/[0.04] border border-primary/[0.06]"
      >
        <div class="w-7 h-7 rounded-xl bg-primary/8 text-primary flex items-center justify-center shrink-0">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
          </svg>
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-[10px] font-semibold text-primary/70 leading-tight">{{ 'Ответ ' + dm.replyTo.userName }}</p>
          <p class="text-[10px] text-secondary/50 truncate mt-px leading-tight">{{ dm.replyTo.content }}</p>
        </div>
        <button
          class="w-7 h-7 rounded-xl flex items-center justify-center text-secondary/40 hover:text-danger hover:bg-danger/5 transition-all shrink-0"
          @click="dm.clearReplyTo()"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Edit bar -->
      <div
        v-if="dm.editingMessage"
        class="flex items-center gap-2 mx-3 mt-2 mb-1 px-3.5 py-2.5 rounded-2xl bg-primary/[0.04] border border-primary/[0.06]"
      >
        <div class="w-7 h-7 rounded-xl bg-primary/8 text-primary flex items-center justify-center shrink-0">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
          </svg>
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-[10px] font-semibold text-primary/70 leading-tight">Редактирование</p>
          <p class="text-[10px] text-secondary/50 truncate mt-px leading-tight">{{ dm.editingMessage.content }}</p>
        </div>
        <button
          class="w-7 h-7 rounded-xl flex items-center justify-center text-secondary/40 hover:text-danger hover:bg-danger/5 transition-all shrink-0"
          @click="dm.setEditingMessage(null)"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Selected file preview -->
      <div
        v-if="selectedFile"
        class="flex items-center gap-2 mx-3 mb-1 px-3.5 py-2.5 rounded-2xl bg-surface-elevated border border-border/20"
      >
        <div class="w-8 h-8 rounded-xl bg-primary/8 text-primary flex items-center justify-center shrink-0">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
          </svg>
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-xs font-medium text-foreground truncate leading-tight">{{ selectedFile.name }}</p>
          <p class="text-[9px] text-secondary/50 mt-px leading-tight">{{ formatFileSize(selectedFile.size) }}</p>
        </div>
        <button
          class="w-7 h-7 rounded-xl flex items-center justify-center text-secondary/40 hover:text-danger hover:bg-danger/5 transition-all shrink-0"
          @click="cancelFile"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Input -->
      <div class="relative px-3 pb-3 pt-1.5">
        <Transition name="dropdown">
          <div
            v-if="showEmojiPicker"
            class="absolute bottom-full left-3 right-3 mb-2 rounded-2xl bg-surface-elevated/95 border border-border/20 shadow-2xl overflow-hidden backdrop-blur-2xl"
          >
            <div class="max-h-44 overflow-y-auto p-2 grid grid-cols-9 gap-0.5">
              <button
                v-for="emoji in EMOJIS"
                :key="emoji"
                class="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-primary/10 text-base transition-colors"
                @click="insertEmoji(emoji)"
              >
                {{ emoji }}
              </button>
            </div>
          </div>
        </Transition>

        <div class="flex items-center gap-1 bg-surface-elevated/90 rounded-2xl border border-border/30 p-1 transition-all focus-within:border-primary/30 focus-within:shadow-[0_0_0_3px_color-mix(in_srgb,var(--color-primary)_8%,transparent)] backdrop-blur-sm">
          <button
            class="w-9 h-9 rounded-xl flex items-center justify-center text-secondary/35 hover:text-primary hover:bg-primary/8 transition-all shrink-0"
            title="Прикрепить файл"
            :class="{ 'text-primary bg-primary/10': selectedFile }"
            @click="openFilePicker"
          >
            <svg class="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
            </svg>
          </button>
          <button
            class="w-9 h-9 rounded-xl flex items-center justify-center text-secondary/35 hover:text-primary hover:bg-primary/8 transition-all shrink-0"
            title="Эмодзи"
            :class="{ 'text-primary bg-primary/10': showEmojiPicker }"
            @click="showEmojiPicker = !showEmojiPicker"
          >
            <svg class="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
            </svg>
          </button>
          <textarea
            ref="textareaRef"
            v-model="text"
            placeholder="Написать сообщение..."
            rows="1"
            class="flex-1 bg-transparent text-sm text-foreground placeholder:text-secondary/30 resize-none outline-none px-2 py-[10px] max-h-36 leading-relaxed"
            @keydown="onKeydown"
            @input="onTextareaInput"
          />
          <button
            :disabled="(!text.trim() && !selectedFile) || sending || dm.uploading"
            class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-all duration-200"
            :class="sending || dm.uploading ? 'bg-danger/10 text-danger' : (text.trim() || selectedFile) ? 'bg-primary text-white shadow-sm hover:shadow-md hover:opacity-90' : 'bg-surface border border-border/30 text-secondary/30'"
            @click="sending || dm.uploading ? () => {} : send()"
          >
            <svg v-if="!sending && !dm.uploading" class="w-[18px] h-[18px] ml-px" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
            <svg v-else class="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <input ref="fileInput" type="file" class="hidden" @change="onFileSelected" />
    </div>
  </div>

  <!-- Context menu -->
  <Teleport to="body">
    <div v-if="contextMenu" class="fixed inset-0 z-[200]" @mousedown.stop="closeContextMenu">
      <div
        class="absolute bg-surface-elevated/95 border border-border/20 rounded-2xl shadow-2xl py-1 min-w-[180px] overflow-hidden backdrop-blur-2xl"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @mousedown.stop
      >
        <button class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-primary/5 transition-colors text-left font-medium" @click="startReply(contextMenu.msg); contextMenu = null">
          <svg class="w-[18px] h-[18px] text-secondary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
          </svg>
          Ответить
        </button>
        <button v-if="contextMenu.msg.sender_id === currentUserId" class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-primary/5 transition-colors text-left font-medium" @click="startEdit(contextMenu.msg); contextMenu = null">
          <svg class="w-[18px] h-[18px] text-secondary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
          </svg>
          Редактировать
        </button>
        <button class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-primary/5 transition-colors text-left font-medium" @click="reactionPicker = { msg: contextMenu.msg, x: contextMenu.x, y: contextMenu.y }; contextMenu = null">
          <svg class="w-[18px] h-[18px] text-secondary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
          </svg>
          Реакция
        </button>
        <button v-if="contextMenu.msg.file_path && contextMenu.msg.file_name" class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-primary/5 transition-colors text-left font-medium" @click="saveFileAs(contextMenu.msg); contextMenu = null">
          <svg class="w-[18px] h-[18px] text-secondary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Сохранить как
        </button>
        <div class="h-px bg-border/20 mx-4 my-1" />
        <button v-if="contextMenu.msg.sender_id === currentUserId" class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-danger hover:bg-danger/5 transition-colors text-left font-medium" @click="deleteMsg(contextMenu.msg); contextMenu = null">
          <svg class="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
          Удалить
        </button>
      </div>
    </div>
  </Teleport>

  <!-- Reaction picker -->
  <Teleport to="body">
    <div v-if="reactionPicker" class="fixed inset-0 z-[200]" @mousedown.stop="reactionPicker = null">
      <div
        class="absolute bg-surface-elevated/95 border border-border/20 rounded-2xl shadow-2xl p-2 backdrop-blur-2xl"
        :style="{ left: reactionPicker.x + 'px', top: reactionPicker.y + 'px' }"
        @mousedown.stop
      >
        <div class="flex items-center gap-0.5 flex-wrap max-w-[280px]">
          <button
            v-for="emoji in REACTION_EMOJIS"
            :key="emoji"
            class="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-primary/10 text-lg transition-all hover:scale-110"
            :class="reactionPicker.msg.reactions?.[emoji]?.includes(currentUserId ?? '') ? 'bg-primary/8 ring-1 ring-primary/20' : ''"
            @click="toggleReaction(reactionPicker.msg, emoji)"
          >
            {{ emoji }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Delete confirmation -->
  <Teleport to="body">
    <div v-if="deleteDialog" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/15 backdrop-blur-sm" @click="deleteDialog = null">
      <div class="bg-surface-elevated/95 border border-border/20 rounded-3xl shadow-2xl p-7 max-w-sm w-full mx-4 backdrop-blur-2xl" @click.stop>
        <div class="w-11 h-11 rounded-2xl bg-danger/10 text-danger flex items-center justify-center mb-4">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-foreground mb-2">Удалить сообщение?</h3>
        <p class="text-[13px] text-secondary/60 mb-5 leading-relaxed">Вы можете удалить сообщение у всех или только у себя.</p>
        <div class="flex flex-col gap-2.5">
          <button class="w-full px-4 py-3 rounded-2xl bg-danger text-white text-[15px] font-medium hover:bg-danger/90 transition-colors shadow-sm" @click="confirmDelete('all')">Удалить у всех</button>
          <button class="w-full px-4 py-3 rounded-2xl bg-surface text-foreground text-[15px] font-medium border border-border/30 hover:bg-surface-elevated transition-colors" @click="confirmDelete('self')">Удалить у себя</button>
          <button class="w-full px-4 py-2.5 rounded-2xl text-secondary/50 text-[13px] hover:text-foreground transition-colors" @click="deleteDialog = null">Отмена</button>
        </div>
      </div>
    </div>
  </Teleport>

  <UiLightbox
    v-model="lightboxOpen"
    :media="lightboxMedia"
    :initial-index="lightboxIndex"
    @save-as="onLightboxSaveAs"
  />
</template>

<style scoped>
.dm-chat-bg {
  background-color: var(--color-surface);
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--color-text) 8%, transparent) transparent;
}
.dm-chat-bg::-webkit-scrollbar {
  width: 4px;
}
.dm-chat-bg::-webkit-scrollbar-track {
  background: transparent;
}
.dm-chat-bg::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--color-text) 8%, transparent);
  border-radius: 2px;
}
.dm-chat-bg::-webkit-scrollbar-thumb:hover {
  background: color-mix(in srgb, var(--color-text) 18%, transparent);
}

.online-dot-sm {
  animation: online-pulse-sm 2s ease-in-out infinite;
}
@keyframes online-pulse-sm {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-success) 50%, transparent); }
  50% { box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-success) 15%, transparent); }
}

.highlight-message {
  animation: highlight-fade 1.5s ease-out;
}
@keyframes highlight-fade {
  0% { background-color: color-mix(in srgb, var(--color-primary) 10%, transparent); border-radius: 12px; }
  100% { background-color: transparent; }
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* Apple-style message bubbles */
.bubble-own {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
  box-shadow: 0 1px 4px color-mix(in srgb, var(--color-primary) 20%, transparent);
}

.bubble-other {
  background: var(--color-surface-elevated);
  color: var(--color-text);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

/* Reply quote for own messages (on gradient bubble) */
.reply-quote-own {
  border-left-color: rgba(255, 255, 255, 0.35);
  background: linear-gradient(to right, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.03));
}

/* Reply quote for other user */
.reply-quote-other {
  border-left-color: color-mix(in srgb, var(--color-primary) 40%, transparent);
  background: linear-gradient(to right, color-mix(in srgb, var(--color-primary) 6%, transparent), transparent);
}

</style>
