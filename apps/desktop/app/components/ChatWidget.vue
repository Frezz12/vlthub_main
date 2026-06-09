<script setup lang="ts">
import type { ChatMessageData } from '~/stores/chat'
import type { UserBadgeBrief } from '@pjasaver/shared-types'
import { resolveApiUrl } from '~/composables/useApiFetch'
import { invoke } from '@tauri-apps/api/core'
import UiAvatarRing from '~/components/UiAvatarRing.vue'
import UiLightbox from '~/components/UiLightbox.vue'
import { audioState } from '~/utils/audioState'
import { playAudio as globalPlayAudio, toggleAudio as globalToggleAudio, seekAudio as globalSeek, setSpeed, stopAudio as globalStopAudio, setVolume } from '~/utils/audioService'

const CHAT_FILE_MAX_SIZE = 100 * 1024 * 1024

const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void } | null

interface Props {
  projectId: string
}

const props = defineProps<Props>()
const chat = useChatStore()
const auth = useAuthStore()
const versions = useVersionsStore()

const isOpen = ref(false)
const text = ref('')
const sending = ref(false)
const listRef = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const selectedVersion = ref<{ id: string; title: string; num: number; isCurrent: boolean } | null>(null)
const showVersionPicker = ref(false)
const showEmojiPicker = ref(false)
const reactionPicker = ref<{ msg: ChatMessageData; x: number; y: number } | null>(null)
const contextMenu = ref<{ msg: ChatMessageData; x: number; y: number } | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const panelRef = ref<HTMLElement | null>(null)
const deleteDialog = ref<ChatMessageData | null>(null)
const sendingAbort = ref<AbortController | null>(null)
const downloadingId = ref<string | null>(null)
const downloadAbort = ref<AbortController | null>(null)

const playingAudioId = ref<string | null>(null)
const audioProgress = ref<Record<string, number>>({})
const audioDuration = ref<Record<string, number>>({})
const audioSpeed = ref(1)

function calcProgress(msgId: string): number {
  if (!audioDuration.value[msgId]) return 0
  return (audioProgress.value[msgId] || 0) / audioDuration.value[msgId]
}

function toggleAudio(msgId: string, filePath: string) {
  const url = mediaUrl(filePath)
  const msg = chat.sortedMessages.find(m => m.id === msgId)
  const title = msg?.file_name || filePath.split('/').pop() || filePath

  if (audioState.src === url) {
    globalToggleAudio()
    return
  }

  playingAudioId.value = msgId
  globalPlayAudio(url, title)
  audioProgress.value[msgId] = 0
}

function seekAudio(msgId: string, e: Event) {
  const input = e.target as HTMLInputElement
  globalSeek(parseFloat(input.value))
}

function cycleAudioSpeed() {
  const speeds = [1, 1.5, 2, 0.5]
  const idx = speeds.indexOf(audioSpeed.value)
  audioSpeed.value = speeds[(idx + 1) % speeds.length]
  setSpeed(audioSpeed.value)
}

watch(() => audioState.src, () => {
  if (!audioState.src) {
    playingAudioId.value = null
  }
})

watch(() => audioState.currentTime, (t) => {
  if (playingAudioId.value) {
    audioProgress.value[playingAudioId.value] = t
  }
})

watch(() => audioState.duration, (d) => {
  if (playingAudioId.value) {
    audioDuration.value[playingAudioId.value] = d
  }
})

const dragging = ref(false)
let tauriDragUnlisten: (() => void) | null = null

const lightboxOpen = ref(false)
const lightboxMedia = ref<{ url: string; fileName: string }[]>([])
const lightboxIndex = ref(0)

const storedWidth = typeof localStorage !== 'undefined' ? localStorage.getItem('chat_width') : null
const storedHeight = typeof localStorage !== 'undefined' ? localStorage.getItem('chat_height') : null
const maxPanelW = typeof window !== 'undefined' ? window.innerWidth - 28 : 600
const maxPanelH = typeof window !== 'undefined' ? window.innerHeight - 88 : 800
const chatWidth = ref(Math.min(parseInt(storedWidth || '380', 10), maxPanelW))
const chatHeight = ref(Math.min(parseInt(storedHeight || '520', 10), maxPanelH))
const resizing = ref(false)

function startResize(e: MouseEvent) {
  resizing.value = true
  const startX = e.clientX
  const startY = e.clientY
  const startW = chatWidth.value
  const startH = chatHeight.value
  const maxW = window.innerWidth - 28
  const maxH = window.innerHeight - 88

  function onMouseMove(ev: MouseEvent) {
    const w = Math.max(280, Math.min(maxW, startW - (ev.clientX - startX)))
    const h = Math.max(360, Math.min(maxH, startH - (ev.clientY - startY)))
    chatWidth.value = w
    chatHeight.value = h
  }

  function onMouseUp() {
    resizing.value = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.style.userSelect = ''
    document.body.style.cursor = ''
    try {
      localStorage.setItem('chat_width', String(chatWidth.value))
      localStorage.setItem('chat_height', String(chatHeight.value))
    } catch {}
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'nwse-resize'
}

watch(isOpen, (open) => {
  if (open) {
    chat.clearUnread()
    chat.fetchMessages(props.projectId)
    versions.fetchVersions(props.projectId)
    nextTick(() => scrollToBottom())
  }
})

watch(() => props.projectId, (newId, oldId) => {
  if (newId !== oldId) {
    chat.clearMessages()
    chat.disconnectWebSocket()
    chat.connectWebSocket(newId)
    if (isOpen.value) {
      chat.fetchMessages(newId)
      versions.fetchVersions(newId)
      nextTick(() => scrollToBottom())
    }
  }
})

onMounted(async () => {
  document.addEventListener('mousedown', closeContextMenu)
  document.addEventListener('keydown', onKeyGlobal)
  document.addEventListener('dragover', preventDocDrag)
  document.addEventListener('drop', preventDocDrag)
  chat.connectWebSocket(props.projectId)
  if (panelRef.value) {
    panelRef.value.addEventListener('dragenter', onDragEnterNative)
    panelRef.value.addEventListener('dragover', onDragOverNative)
    panelRef.value.addEventListener('dragleave', onDragLeaveNative)
    panelRef.value.addEventListener('drop', onDropNative)
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
})

onUnmounted(() => {
  chat.disconnectWebSocket()
  document.removeEventListener('mousedown', closeContextMenu)
  document.removeEventListener('keydown', onKeyGlobal)
  document.removeEventListener('dragover', preventDocDrag)
  document.removeEventListener('drop', preventDocDrag)
  if (panelRef.value) {
    panelRef.value.removeEventListener('dragenter', onDragEnterNative)
    panelRef.value.removeEventListener('dragover', onDragOverNative)
    panelRef.value.removeEventListener('dragleave', onDragLeaveNative)
    panelRef.value.removeEventListener('drop', onDropNative)
  }
  if (tauriDragUnlisten) {
    tauriDragUnlisten()
    tauriDragUnlisten = null
  }
})

const currentUserId = computed(() => auth.user?.id)

const filteredVersions = computed(() =>
  versions.sortedVersions.slice(0, 10)
)

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

function selectVersion(versionId: string) {
  const v = versions.items.find(v => v.id === versionId)
  if (v) {
    selectedVersion.value = { id: v.id, title: v.title || '', num: v.version_number, isCurrent: v.is_current }
  }
  showVersionPicker.value = false
}

function cancelVersion() {
  selectedVersion.value = null
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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

function mediaUrl(filePath: string): string {
  return resolveApiUrl(filePath) || filePath
}

function openLightbox(msg: ChatMessageData, msgs: ChatMessageData[]) {
  const media = msgs.filter(m =>
    m.file_name && m.file_path && (isImageFile(m.file_name) || isVideoFile(m.file_name))
  )
  if (media.length === 0) return
  lightboxMedia.value = media.map(m => ({
    url: mediaUrl(m.file_path!),
    fileName: m.file_name!,
  }))
  lightboxIndex.value = media.findIndex(m => m.id === msg.id)
  if (lightboxIndex.value === -1) lightboxIndex.value = 0
  lightboxOpen.value = true
}

const EMOTIONAL_PREFIXES = ['yes', 'yeah', 'yep', 'yess', 'awesome', 'fantastic', 'amazing', 'great', 'perfect', 'wonderful', 'love', 'sure', 'absolutely', 'definitely', 'totally', 'nice', 'cool', 'да', 'конечно', 'отлично', 'прекрасно', 'супер', 'класс', 'ага', 'ладно', 'ок', 'ok']
const EMOTIONAL_CHARS = ['!', '🥰', '🎉', '❤️', '🔥', '😍', '💯', '✨', '🙌', '👏', '💪', '🤩']

function isEmotionalResponse(content: string): boolean {
  const t = content.trim()
  if (t.length > 60) return false
  if (EMOTIONAL_CHARS.some(c => t.includes(c))) return true
  if (EMOTIONAL_PREFIXES.some(p => t.toLowerCase().startsWith(p))) return true
  return false
}

async function send() {
  if (sending.value || chat.uploading) return

  sendingAbort.value = new AbortController()
  sending.value = true

  if (chat.editingMessage) {
    const content = text.value.trim()
    if (!content) { sending.value = false; return }
    try {
      await chat.updateMessage(props.projectId, chat.editingMessage.id, content, sendingAbort.value.signal)
      text.value = ''
    } finally {
      sending.value = false
      sendingAbort.value = null
    }
    return
  }

  const content = text.value.trim()

  if (selectedVersion.value) {
    try {
      await chat.sendVersionMessage(props.projectId, selectedVersion.value.id, content, sendingAbort.value.signal)
      text.value = ''
      selectedVersion.value = null
      nextTick(() => scrollToBottom())
    } finally {
      sending.value = false
      sendingAbort.value = null
    }
    return
  }

  if (selectedFile.value) {
    if (selectedFile.value.size > CHAT_FILE_MAX_SIZE) {
      toast?.show('Файл превышает 100 МБ', 'error')
      selectedFile.value = null
      sending.value = false
      sendingAbort.value = null
      return
    }
    try {
      await chat.sendFileMessage(props.projectId, selectedFile.value, content)
      text.value = ''
      selectedFile.value = null
      nextTick(() => scrollToBottom())
    } finally {
      sending.value = false
      sendingAbort.value = null
    }
    return
  }

  if (!content) { sending.value = false; sendingAbort.value = null; return }
  try {
    await chat.sendMessage(props.projectId, content, sendingAbort.value.signal)
    text.value = ''
    nextTick(() => scrollToBottom())
  } finally {
    sending.value = false
    sendingAbort.value = null
  }
}

function cancelSend() {
  sendingAbort.value?.abort()
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
  if (chat.editingMessage) chat.setEditingMessage(null)
  if (chat.replyTo) chat.clearReplyTo()
  selectedFile.value = null
  selectedVersion.value = null
  showVersionPicker.value = false
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

function onDragLeaveNative(e: DragEvent) {
  const target = e.currentTarget as HTMLElement
  const related = e.relatedTarget as HTMLElement
  if (!target.contains(related)) {
    dragging.value = false
  }
}

function onDropNative(e: DragEvent) {
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

function scrollToBottom() {
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight
  }
}

watch(() => chat.messages.length, () => {
  nextTick(() => scrollToBottom())
})

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

function shouldShowDate(msg: ChatMessageData, idx: number): boolean {
  if (idx === 0) return true
  const prev = chat.messages[idx - 1]
  return new Date(msg.created_at).toDateString() !== new Date(prev.created_at).toDateString()
}

function isSameSender(msg: ChatMessageData, idx: number): boolean {
  if (idx === 0) return false
  const prev = chat.messages[idx - 1]
  const diff = new Date(msg.created_at).getTime() - new Date(prev.created_at).getTime()
  return msg.user_id === prev.user_id && diff < 300000
}

function startReply(msg: ChatMessageData) {
  chat.setReplyTo(msg.id, msg.user_name, msg.content, msg.version_title, msg.version_number)
}

function replyLabel(msg: ChatMessageData): string {
  if (msg.reply_to_version_title) return msg.reply_to_version_title
  if (msg.reply_to_version_number) return `Версия ${msg.reply_to_version_number}`
  if (msg.reply_to_file_name) return msg.reply_to_file_name
  return msg.reply_to_user_name || 'Ответ'
}

const REACTION_EMOJIS = [
  '👍', '❤️', '😂', '😮', '😢', '😡', '🎉', '🔥',
  '👏', '💯', '✅', '❌', '🤔', '👀', '💪', '🙏',
  '✨', '⭐', '🎊', '🥳',
]

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

function startEdit(msg: ChatMessageData) {
  text.value = msg.content
  chat.setEditingMessage(msg)
  contextMenu.value = null
  nextTick(() => onTextareaInput())
}

async function toggleReaction(msg: ChatMessageData, emoji: string) {
  await chat.toggleReaction(props.projectId, msg.id, emoji)
  reactionPicker.value = null
}

async function deleteMsg(msg: ChatMessageData) {
  contextMenu.value = null
  deleteDialog.value = msg
}

async function confirmDelete(scope: 'all' | 'self') {
  const msg = deleteDialog.value
  if (!msg) return
  deleteDialog.value = null
  await chat.deleteMessage(props.projectId, msg.id, scope)
}

function onContextMenu(e: MouseEvent, msg: ChatMessageData) {
  contextMenu.value = { msg, x: e.clientX, y: e.clientY }
}

function isOwnMessage(msg: ChatMessageData) {
  return msg.user_id === currentUserId.value
}

const visibleMessages = computed(() =>
  chat.sortedMessages.filter(msg => !msg.deleted_by?.includes(currentUserId.value ?? ''))
)

function closeContextMenu() {
  contextMenu.value = null
  reactionPicker.value = null
}

function onKeyGlobal(e: KeyboardEvent) {
  if (e.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}

function onTextareaInput() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

function messageBadge(msg: ChatMessageData): UserBadgeBrief | null {
  if (!msg.user_badge_ring_gradient) return null
  return {
    id: '',
    name: msg.user_badge_name || '',
    icon_svg: msg.user_badge_icon_svg || '',
    avatar_ring_gradient: msg.user_badge_ring_gradient,
    avatar_ring_effect: msg.user_badge_ring_effect || null,
    is_active: true,
    description: null,
  }
}

const ownBadge = computed<UserBadgeBrief | null>(() => {
  const b = auth.user?.active_badge
  if (!b?.avatar_ring_gradient) return null
  return b
})

function downloadFile(msg: ChatMessageData) {
  if (downloadingId.value) return
  if (!msg.file_path || !msg.file_name) return

  downloadingId.value = msg.id
  downloadAbort.value = new AbortController()

  const dlStore = useDownloadProgress()
  dlStore.registerDownload(msg.id, msg.file_name, () => { cancelDownload(msg) })

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
      dlStore.removeDownload(msg.id)
    })
    .catch((e) => {
      if (e.name === 'AbortError') return
      toast?.show('Ошибка при скачивании', 'error')
    })
    .finally(() => {
      if (downloadingId.value === msg.id) downloadingId.value = null
    })
}

function cancelDownload(msg: ChatMessageData) {
  if (downloadingId.value === msg.id) {
    downloadAbort.value?.abort()
    downloadAbort.value = null
    downloadingId.value = null
  }
}

async function saveFileAs(msg: ChatMessageData) {
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

function getReplyMessage(msg: ChatMessageData): ChatMessageData | undefined {
  if (!msg.reply_to_id) return undefined
  return chat.messages.find(m => m.id === msg.reply_to_id)
}

function scrollToMessage(messageId: string) {
  const el = document.getElementById('msg-' + messageId)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  el.classList.add('highlight-message')
  setTimeout(() => el.classList.remove('highlight-message'), 1500)
}
</script>

<template>
  <div class="chat-widget">
    <div class="relative flex items-start gap-1.5">
      <button
        v-show="!isOpen"
        class="chat-toggle-modern"
        :class="{ 'has-unread': chat.unreadCount > 0 }"
        @click="isOpen = !isOpen"
      >
        <svg v-if="!isOpen" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
        <span v-if="!isOpen && chat.unreadCount > 0" class="chat-badge">{{ chat.unreadCount }}</span>
      </button>
      <span v-if="!isOpen" class="text-[8px] font-bold uppercase tracking-wider text-primary px-1 py-0.5 rounded-md bg-primary/10 self-start mt-1.5 leading-none">Beta</span>
    </div>

    <Transition name="panel">
      <div
        v-if="isOpen"
        ref="panelRef"
        class="chat-panel-modern"
        :style="{ width: chatWidth + 'px', height: chatHeight + 'px' }"
        @click.stop
      >
        <!-- Header -->
        <div class="chat-header-modern">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                </svg>
              </div>
              <div>
                <p class="text-base font-semibold text-foreground">Чат проекта <span class="text-[9px] font-bold uppercase tracking-wider text-primary align-middle ml-1 px-1 py-0.5 rounded-md bg-primary/10">Beta</span></p>
                <p class="text-xs" :class="chat.connected ? 'text-success' : 'text-secondary/60'">
                  {{ chat.connected ? 'В сети' : 'Нет соединения' }}
                </p>
              </div>
            </div>
            <button
              class="w-8 h-8 rounded-xl flex items-center justify-center text-secondary/40 hover:text-primary hover:bg-primary/5 transition-all shrink-0 -mr-1"
              @click="isOpen = false"
              title="Закрыть"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Resize handle -->
        <div
          class="chat-resize-handle"
          @mousedown.prevent="startResize"
        >
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
          </svg>
        </div>

        <!-- Messages -->
        <div ref="listRef" class="chat-messages-modern chat-messages-scrollbar">
          <div v-if="chat.loading" class="flex items-center justify-center py-8">
            <div class="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>

          <div v-else-if="chat.messages.length === 0" class="flex flex-col items-center justify-center py-12 text-center px-6">
            <div class="w-12 h-12 rounded-2xl bg-primary/5 text-primary/40 flex items-center justify-center mb-3">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
              </svg>
            </div>
            <p class="text-sm text-foreground/40">Сообщений пока нет</p>
          </div>

          <div v-for="(msg, idx) in visibleMessages" :key="msg.id" :id="'msg-' + msg.id" class="px-4 py-0.5">
            <!-- Date separator -->
                <div v-if="shouldShowDate(msg, idx)" class="chat-date-separator">
                  <span>{{ formatDate(msg.created_at) }}</span>
                </div>

            <div
              class="chat-message-container"
              :class="{ own: msg.user_id === currentUserId }"
              @contextmenu.prevent="msg.content !== undefined && onContextMenu($event, msg)"
            >
              <!-- Avatar -->
              <div class="chat-avatar">
                <UiAvatarRing
                  v-if="messageBadge(msg)"
                  :src="msg.user_avatar"
                  :name="msg.user_name"
                  :badge="messageBadge(msg)!"
                  size="sm"
                />
                <div v-else class="chat-avatar-circle">
                  {{ msg.user_name?.charAt(0)?.toUpperCase() || '?' }}
                </div>
              </div>

              <div class="chat-bubble">
                <!-- User name + badge -->
                <div
                  class="flex items-center gap-1.5 mb-0.5 px-1"
                  :class="msg.user_id === currentUserId ? 'justify-end' : ''"
                >
                  <UserBadgeIcon v-if="messageBadge(msg)" :badge="messageBadge(msg)" size="sm" />
                  <span class="text-[11px] font-semibold text-secondary/60">{{ msg.user_name }}</span>
                </div>

                <!-- Reply quote (independent of text content) -->
                <div
                  v-if="msg.reply_to_id && !msg.content"
                  class="chat-reply-quote-modern"
                  @click="scrollToMessage(msg.reply_to_id)"
                >
                  <p class="chat-reply-author">
                    {{ replyLabel(msg) }}
                  </p>
                  <p class="chat-reply-content">
                    {{ msg.reply_to_content }}
                  </p>
                </div>

                <!-- Text bubble (with inline reply quote) -->
                <div
                  v-if="msg.content"
                  class="chat-message-text chat-message-bubble"
                  :class="msg.user_id === currentUserId
                    ? 'chat-bubble-out'
                    : (isEmotionalResponse(msg.content)
                      ? 'message-bubble-emotional chat-bubble-in'
                      : 'chat-bubble-in')"
                >
                  <div
                    v-if="msg.reply_to_id"
                    class="chat-reply-quote-modern"
                    @click="scrollToMessage(msg.reply_to_id)"
                  >
                    <p class="chat-reply-author">
                      {{ replyLabel(msg) }}
                    </p>
                    <p class="chat-reply-content">
                      {{ msg.reply_to_content }}
                    </p>
                  </div>
                  <span class="whitespace-pre-wrap">{{ msg.content }}</span>
                  <span v-if="msg.edited_at" class="text-[10px] opacity-50 ml-1.5">(ред.)</span>
                </div>

                <!-- File attachment (image/video preview, audio player, or download) -->
                <div v-if="msg.file_name && msg.file_path" class="chat-file-attachment">
                  <!-- Image preview -->
                  <div
                    v-if="isImageFile(msg.file_name)"
                    class="chat-file-image"
                    @click="openLightbox(msg, visibleMessages)"
                  >
                    <img
                      :src="mediaUrl(msg.file_path)"
                      :alt="msg.file_name"
                      class="w-full max-h-64 object-cover"
                      loading="lazy"
                    />
                  </div>
                  <!-- Video preview -->
                  <div
                    v-if="isVideoFile(msg.file_name)"
                    class="chat-file-image"
                    @click="openLightbox(msg, visibleMessages)"
                  >
                    <video
                      :src="mediaUrl(msg.file_path)"
                      class="w-full max-h-64 object-cover"
                      preload="metadata"
                    >
                      <p class="text-sm text-secondary/50 p-4">{{ msg.file_name }}</p>
                    </video>
                    <div class="absolute inset-0 flex items-center justify-center bg-black/20">
                      <div class="w-12 h-12 rounded-full bg-black/50 flex items-center justify-center">
                        <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                      </div>
                    </div>
                  </div>
                  <!-- Audio player (Telegram-style) -->
                  <div
                    v-if="isAudioFile(msg.file_name)"
                    class="chat-audio-player"
                  >
                    <div class="flex items-center gap-2.5 px-3.5 py-2.5">
                      <!-- Play button with progress ring -->
                      <div class="relative shrink-0">
                        <button
                          class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 active:scale-95"
                          :class="msg.user_id === currentUserId ? 'bg-white/15 text-white hover:bg-white/25' : 'bg-primary/10 text-primary hover:bg-primary/20'"
                          @click.stop="toggleAudio(msg.id, msg.file_path!)"
                        >
                          <svg v-if="playingAudioId !== msg.id" class="w-4.5 h-4.5 ml-[1px]" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M8 5v14l11-7z"/>
                          </svg>
                          <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                          </svg>
                        </button>
                        <!-- Circular progress ring -->
                        <svg
                          v-if="playingAudioId === msg.id && audioDuration[msg.id]"
                          class="absolute inset-0 w-10 h-10 -rotate-90 pointer-events-none"
                          viewBox="0 0 40 40"
                        >
                          <circle
                            cx="20" cy="20" r="17"
                            fill="none"
                            :class="msg.user_id !== currentUserId ? 'chat-audio-progress-bg' : ''"
                            :stroke="msg.user_id === currentUserId ? 'rgba(255,255,255,0.25)' : ''"
                            stroke-width="2.5"
                          />
                          <circle
                            cx="20" cy="20" r="17"
                            fill="none"
                            :stroke="msg.user_id === currentUserId ? '#fff' : 'var(--color-primary)'"
                            stroke-width="2.5"
                            stroke-linecap="round"
                            :stroke-dasharray="2 * Math.PI * 17"
                            :stroke-dashoffset="2 * Math.PI * 17 * (1 - calcProgress(msg.id))"
                            class="transition-all duration-300"
                          />
                        </svg>
                      </div>
                      <!-- Info column -->
                      <div class="min-w-0 flex-1">
                        <p class="text-sm font-semibold truncate leading-tight" :class="msg.user_id === currentUserId ? 'text-white' : 'text-foreground'">{{ msg.file_name }}</p>
                        <p v-if="msg.file_size" class="text-[10px] leading-relaxed mt-1" :class="msg.user_id === currentUserId ? 'text-white/70' : 'text-secondary'">{{ formatFileSize(msg.file_size) }}</p>
                        <div class="flex items-center gap-2 mt-1.5">
                          <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums" :class="msg.user_id === currentUserId ? 'text-white/75' : 'text-secondary'">
                            {{ formatAudioTime(audioProgress[msg.id] || 0) }}
                          </span>
                          <div class="flex-1 relative h-2 rounded-full" :class="msg.user_id === currentUserId ? 'bg-white/20' : 'bg-primary/10'">
                            <div
                              class="absolute inset-y-0 left-0 rounded-full transition-all duration-300"
                              :class="msg.user_id === currentUserId ? 'bg-white/90' : 'bg-primary'"
                              :style="{ width: (calcProgress(msg.id) * 100) + '%' }"
                            />
                            <input
                              type="range"
                              min="0"
                              :max="audioDuration[msg.id] || 0"
                              :value="audioProgress[msg.id] || 0"
                              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                              @input="seekAudio(msg.id, $event)"
                              @click.stop
                            />
                          </div>
                          <span class="text-[10px] leading-none shrink-0 font-medium tabular-nums" :class="msg.user_id === currentUserId ? 'text-white/75' : 'text-secondary'">
                            {{ formatAudioTime(audioDuration[msg.id] || 0) }}
                          </span>
                        </div>
                      </div>
                      <!-- Speed + Download -->
                      <div class="flex flex-col items-center gap-1 shrink-0">
                        <button
                          class="text-[10px] font-bold leading-none px-2 py-1.5 rounded-md transition-all duration-200 hover:scale-105 active:scale-95 tabular-nums"
                          :class="msg.user_id === currentUserId ? 'text-white/70 hover:bg-white/15' : 'text-secondary hover:text-primary hover:bg-primary/10'"
                          title="Скорость воспроизведения"
                          @click.stop="cycleAudioSpeed()"
                        >
                          {{ audioSpeed }}x
                        </button>
                        <button
                          class="w-7 h-7 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95"
                          :class="[
                            'text-white/60 hover:text-white hover:bg-white/15',
                            msg.user_id !== currentUserId ? 'text-secondary/60 hover:text-primary hover:bg-primary/10' : ''
                          ]"
                          title="Сохранить как"
                          @click.stop="!downloadingId && msg.file_path && downloadFile(msg)"
                        >
                          <svg v-if="downloadingId !== msg.id" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"></path></svg>
                          <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                  <!-- Other file (download) -->
                  <div
                    v-if="!isImageFile(msg.file_name) && !isVideoFile(msg.file_name) && !isAudioFile(msg.file_name)"
                    class="chat-file-generic cursor-pointer rounded-2xl"
                    :class="{ 'opacity-70': downloadingId === msg.id }"
                    @click="!downloadingId && msg.file_path && downloadFile(msg)"
                  >
                    <div class="chat-file-icon" :class="msg.user_id === currentUserId ? 'bg-white/20 text-white' : 'bg-primary/10 text-primary'">
                      <svg v-if="downloadingId !== msg.id" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                      </svg>
                      <svg v-else class="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                      </svg>
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium truncate" :class="msg.user_id === currentUserId ? 'text-white' : 'text-foreground'">{{ msg.file_name }}</p>
                      <p v-if="msg.file_size" class="text-[11px]" :class="msg.user_id === currentUserId ? 'text-white/70' : 'text-secondary/50'">{{ formatFileSize(msg.file_size) }}</p>
                    </div>
                    <div v-if="downloadingId === msg.id" class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer transition-colors" 
                         :class="msg.user_id === currentUserId ? 'hover:bg-white/10' : 'hover:bg-surface'"
                         @click.stop="cancelDownload(msg)">
                      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- Version attachment link -->
                  <NuxtLink
                    v-if="msg.version_id"
                    :to="`/projects/${props.projectId}/versions/${msg.version_id}`"
                    class="chat-version-attachment rounded-2xl"
                  >
                  <div class="chat-file-icon" :class="msg.user_id === currentUserId ? 'bg-white/20 text-white' : 'bg-primary/10 text-primary'">
                    <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-medium truncate" :class="msg.user_id === currentUserId ? 'text-white' : 'text-foreground'">{{ msg.version_title || `Версия ${msg.version_number}` }}</p>
                    <p class="text-[11px]" :class="msg.user_id === currentUserId ? 'text-white/70' : 'text-secondary/50'">Версия {{ msg.version_number }}</p>
                  </div>
                  <svg class="w-5 h-5 shrink-0" :class="msg.user_id === currentUserId ? 'text-white/70' : 'text-secondary/40'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                  </svg>
                </NuxtLink>

                <!-- Reactions -->
                <div
                  v-if="msg.reactions && Object.keys(msg.reactions).length > 0"
                  class="chat-reactions-container"
                  :class="msg.user_id === currentUserId ? 'justify-end' : ''"
                >
                  <button
                    v-for="(users, emoji) in msg.reactions"
                    :key="emoji"
                    class="chat-reaction-pill"
                    :class="{
                      active: users.includes(currentUserId ?? ''),
                      inactive: !users.includes(currentUserId ?? '') && msg.user_id !== currentUserId
                    }"
                    @click="toggleReaction(msg, emoji)"
                  >
                    <span class="text-lg leading-none">{{ emoji }}</span>
                    <span class="tabular-nums">{{ users.length }}</span>
                  </button>
                </div>

                <!-- Timestamp -->
                <div class="chat-message-meta" :class="{ own: msg.user_id === currentUserId }">
                  <span class="chat-message-time">{{ formatTime(msg.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Reply bar -->
        <div
          v-if="chat.replyTo"
          class="flex items-center gap-2.5 mx-4 mb-1.5 px-3 py-2 rounded-xl bg-primary/5 border border-primary/20"
        >
          <div class="w-6 h-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-primary/80">{{ chat.replyTo.versionTitle || chat.replyTo.versionNumber ? `Версия ${chat.replyTo.versionTitle || chat.replyTo.versionNumber}` : `Ответ ${chat.replyTo.userName}` }}</p>
            <p class="text-[11px] text-secondary/50 truncate">{{ chat.replyTo.content }}</p>
          </div>
          <button
            class="w-6 h-6 rounded-lg flex items-center justify-center text-secondary/40 hover:text-danger hover:bg-danger/5 transition-colors shrink-0"
            @click="chat.clearReplyTo()"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Edit bar -->
        <div
          v-if="chat.editingMessage"
          class="flex items-center gap-2.5 mx-4 mb-1.5 px-3 py-2 rounded-xl bg-primary/5 border border-primary/20"
        >
          <div class="w-6 h-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-primary/80">Редактирование</p>
            <p class="text-[11px] text-secondary/50 truncate">{{ chat.editingMessage.content }}</p>
          </div>
          <button
            class="w-6 h-6 rounded-lg flex items-center justify-center text-secondary/40 hover:text-danger hover:bg-danger/5 transition-colors shrink-0"
            @click="chat.setEditingMessage(null)"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Selected file preview -->
        <div
          v-if="selectedFile && !selectedVersion"
          class="flex items-center gap-2.5 mx-4 mb-1.5 px-3 py-2 rounded-xl bg-surface-elevated border border-border/50"
        >
          <div class="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-foreground truncate">{{ selectedFile.name }}</p>
            <p class="text-[10px] text-secondary/50">{{ formatFileSize(selectedFile.size) }}</p>
          </div>
          <button
            class="w-6 h-6 rounded-lg flex items-center justify-center text-secondary/40 hover:text-danger hover:bg-danger/5 transition-colors shrink-0"
            @click="cancelFile"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Selected version preview -->
        <div
          v-if="selectedVersion"
          class="flex items-center gap-2.5 mx-4 mb-1.5 px-3 py-2 rounded-xl bg-surface-elevated border border-border/50"
        >
          <div class="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-foreground truncate">
              {{ selectedVersion.title || `Версия ${selectedVersion.num}` }}
              <span v-if="selectedVersion.isCurrent" class="text-[10px] text-primary/60">Текущая</span>
            </p>
            <p class="text-[10px] text-secondary/50">Версия {{ selectedVersion.num }}</p>
          </div>
          <button
            class="w-6 h-6 rounded-lg flex items-center justify-center text-secondary/40 hover:text-danger hover:bg-danger/5 transition-colors shrink-0"
            @click="cancelVersion"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Input -->
        <div class="chat-input-wrapper relative">
          <!-- Version picker dropdown -->
          <Transition name="dropdown">
            <div
              v-if="showVersionPicker"
              class="absolute bottom-full left-4 right-4 mb-2 rounded-2xl bg-surface-elevated border border-border shadow-xl overflow-hidden"
            >
              <div class="px-4 py-2.5 border-b border-border/50">
                <p class="text-xs font-medium text-secondary/60">Прикрепить версию</p>
              </div>
              <div class="max-h-44 overflow-y-auto">
                <button
                  v-for="v in filteredVersions"
                  :key="v.id"
                  class="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-surface transition-colors"
                  @click="selectVersion(v.id)"
                >
                  <div class="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-medium text-foreground truncate">{{ v.title || `Версия ${v.version_number}` }}</p>
                    <p class="text-[11px] text-secondary/50">Версия {{ v.version_number }}{{ v.is_current ? ' · Текущая' : '' }}</p>
                  </div>
                </button>
                <div v-if="filteredVersions.length === 0" class="px-4 py-6 text-center">
                  <p class="text-xs text-secondary/40">Нет версий</p>
                </div>
              </div>
            </div>
          </Transition>

          <!-- Emoji picker dropdown -->
          <Transition name="dropdown">
            <div
              v-if="showEmojiPicker"
              class="absolute bottom-full left-4 right-4 mb-2 rounded-2xl bg-surface-elevated border border-border shadow-xl overflow-hidden"
            >
              <div class="max-h-52 overflow-y-auto p-2.5 grid grid-cols-9 gap-0.5">
                <button
                  v-for="emoji in EMOJIS"
                  :key="emoji"
                  class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-primary/10 text-lg transition-colors"
                  @click="insertEmoji(emoji)"
                >
                  {{ emoji }}
                </button>
              </div>
            </div>
          </Transition>

          <div class="chat-input-container">
            <button
              class="chat-input-btn"
              title="Прикрепить файл"
              :class="{ 'text-primary bg-primary/5': selectedFile }"
              @click="openFilePicker"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
              </svg>
            </button>
            <button
              class="chat-input-btn"
              title="Прикрепить версию"
              :class="{ 'text-primary bg-primary/5': selectedVersion }"
              @click="showVersionPicker = !showVersionPicker"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </button>
            <button
              class="chat-input-btn"
              title="Эмодзи"
              :class="{ 'text-primary bg-primary/5': showEmojiPicker }"
              @click="showEmojiPicker = !showEmojiPicker"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
              </svg>
            </button>
            <textarea
              ref="textareaRef"
              v-model="text"
              placeholder="Написать сообщение..."
              rows="1"
              class="flex-1 bg-transparent text-sm text-foreground placeholder-secondary/40 resize-none outline-none px-2 py-2 max-h-40"
              @keydown="onKeydown"
              @input="onTextareaInput"
            />
            <button
              :disabled="(!text.trim() && !selectedFile && !selectedVersion) || sending || chat.uploading"
              class="chat-send-btn"
              @click="sending || chat.uploading ? cancelSend() : send()"
            >
              <svg v-if="!sending && !chat.uploading" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <input
          ref="fileInput"
          type="file"
          class="hidden"
          @change="onFileSelected"
        />

        <!-- Drag-drop overlay -->
        <div
          v-show="dragging"
          class="absolute inset-0 z-50 flex items-center justify-center bg-surface/80 backdrop-blur-sm rounded-xl border-2 border-dashed border-primary/40 m-2 pointer-events-none"
          @dragenter="onDragEnterNative"
          @dragover="onDragOverNative"
          @dragleave="onDragLeaveNative"
          @drop="onDropNative"
        >
          <div class="flex flex-col items-center gap-3 text-primary/60">
            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            <span class="text-sm font-medium">Отпустите файл для отправки</span>
          </div>
        </div>

      </div>
    </Transition>
  </div>

  <!-- Context menu -->
  <Teleport to="body">
    <div
      v-if="contextMenu"
      class="fixed inset-0 z-[200]"
      @mousedown.stop="closeContextMenu"
    >
      <div
        class="absolute bg-surface-elevated border border-border rounded-2xl shadow-xl py-1.5 min-w-[180px] overflow-hidden"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @mousedown.stop
      >
        <button
          class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-foreground hover:bg-surface transition-colors text-left"
          @click="startReply(contextMenu.msg); contextMenu = null"
        >
          <svg class="w-4 h-4 text-secondary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
          </svg>
          Ответить
        </button>
        <button
          v-if="contextMenu.msg.user_id === currentUserId"
          class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-foreground hover:bg-surface transition-colors text-left"
          @click="startEdit(contextMenu.msg); contextMenu = null"
        >
          <svg class="w-4 h-4 text-secondary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
          </svg>
          Редактировать
        </button>
        <button
          class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-foreground hover:bg-surface transition-colors text-left"
          @click="reactionPicker = { msg: contextMenu.msg, x: contextMenu.x, y: contextMenu.y }; contextMenu = null"
        >
          <svg class="w-4 h-4 text-secondary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
          </svg>
          Реакция
        </button>
        <button
          v-if="contextMenu.msg.file_path && contextMenu.msg.file_name"
          class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-foreground hover:bg-surface transition-colors text-left"
          @click="saveFileAs(contextMenu.msg); contextMenu = null"
        >
          <svg class="w-4 h-4 text-secondary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Сохранить как
        </button>
        <div class="h-px bg-border/50 mx-3 my-1" />
        <button
          v-if="contextMenu.msg.user_id === currentUserId"
          class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-danger hover:bg-danger/5 transition-colors text-left"
          @click="deleteMsg(contextMenu.msg); contextMenu = null"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
          Удалить
        </button>
      </div>
    </div>
  </Teleport>

  <!-- Reaction picker -->
  <Teleport to="body">
    <div
      v-if="reactionPicker"
      class="fixed inset-0 z-[200]"
      @mousedown.stop="reactionPicker = null"
    >
      <div
        class="absolute bg-surface-elevated border border-border rounded-2xl shadow-xl p-2"
        :style="{ left: reactionPicker.x + 'px', top: reactionPicker.y + 'px' }"
        @mousedown.stop
      >
        <div class="flex items-center gap-0.5 flex-wrap max-w-[280px]">
          <button
            v-for="emoji in REACTION_EMOJIS"
            :key="emoji"
            class="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-primary/10 text-xl transition-all hover:scale-110"
            :class="reactionPicker.msg.reactions?.[emoji]?.includes(currentUserId ?? '') ? 'bg-primary/10 ring-1 ring-primary/30' : ''"
            @click="toggleReaction(reactionPicker.msg, emoji)"
          >
            {{ emoji }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Lightbox -->
  <UiLightbox
    v-model="lightboxOpen"
    :media="lightboxMedia"
    :initial-index="lightboxIndex"
  />

  <!-- Delete confirmation -->
  <Teleport to="body">
    <div
      v-if="deleteDialog"
      class="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click="deleteDialog = null"
    >
      <div
        class="bg-surface-elevated border border-border rounded-2xl shadow-2xl p-6 max-w-sm w-full mx-4"
        @click.stop
      >
        <div class="w-10 h-10 rounded-2xl bg-danger/10 text-danger flex items-center justify-center mb-4">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-foreground mb-2">Удалить сообщение?</h3>
        <p class="text-sm text-secondary/60 mb-6">Вы можете удалить сообщение у всех или только у себя.</p>
        <div class="flex flex-col gap-2">
          <button
            class="w-full px-4 py-2.5 rounded-xl bg-danger text-white text-sm font-medium hover:bg-danger/90 transition-colors"
            @click="confirmDelete('all')"
          >
            Удалить у всех
          </button>
          <button
            class="w-full px-4 py-2.5 rounded-xl bg-surface text-foreground text-sm font-medium border border-border/50 hover:bg-surface-elevated transition-colors"
            @click="confirmDelete('self')"
          >
            Удалить у себя
          </button>
          <button
            class="w-full px-4 py-2 rounded-xl text-secondary/50 text-sm hover:text-foreground transition-colors"
            @click="deleteDialog = null"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.chat-widget {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
}

.chat-toggle {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: none;
  outline: none;
  color: white;
  background: var(--color-primary);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), 0 1px 4px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.chat-toggle:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.chat-toggle.is-open {
  background: var(--color-surface-elevated);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.chat-toggle.is-open:hover {
  transform: scale(1.05);
}

.chat-toggle.has-unread {
  animation: chat-glow 2s ease-in-out infinite;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), 0 1px 4px rgba(0, 0, 0, 0.08), 0 0 20px color-mix(in srgb, var(--color-primary) 50%, transparent);
}

@keyframes chat-glow {
  0%, 100% { box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), 0 1px 4px rgba(0, 0, 0, 0.08), 0 0 20px color-mix(in srgb, var(--color-primary) 50%, transparent); }
  50% { box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), 0 1px 4px rgba(0, 0, 0, 0.08), 0 0 30px color-mix(in srgb, var(--color-primary) 70%, transparent); }
}

.chat-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  background: var(--color-danger);
  color: white;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  box-shadow: 0 2px 6px color-mix(in srgb, var(--color-danger) 40%, transparent);
}

.chat-panel {
  position: absolute;
  bottom: 64px;
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15), 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.chat-panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0 12px;
  scroll-behavior: smooth;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 2px;
}

.chat-input {
  padding: 8px 16px 16px;
  flex-shrink: 0;
}

.chat-resize-handle {
  position: absolute;
  top: 0;
  left: 0;
  width: 20px;
  height: 20px;
  cursor: nwse-resize;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 3px;
  color: var(--color-secondary);
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 5;
}

.chat-panel:hover .chat-resize-handle {
  opacity: 0.4;
}

.chat-resize-handle:hover {
  opacity: 1 !important;
  color: var(--color-primary);
}

.panel-enter-active,
.panel-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.96);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.highlight-message {
  animation: msg-highlight 1.5s ease-out;
}

@keyframes msg-highlight {
  0% { background-color: color-mix(in srgb, var(--color-primary) 12%, transparent); border-radius: 12px; }
  100% { background-color: transparent; }
}

.message-bubble-emotional {
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 6%, transparent) 0%, color-mix(in srgb, var(--color-warning) 5%, transparent) 100%);
}

html.dark .message-bubble-emotional {
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 10%, transparent) 0%, color-mix(in srgb, var(--color-warning) 8%, transparent) 100%);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}
</style>
