import { audioState } from './audioState'

let audioEl: HTMLAudioElement | null = null

function ensureAudio() {
  if (!audioEl) {
    audioEl = new Audio()
    audioEl.preload = 'auto'
    audioEl.addEventListener('timeupdate', () => {
      audioState.currentTime = audioEl!.currentTime
    })
    audioEl.addEventListener('loadedmetadata', () => {
      audioState.duration = audioEl!.duration
    })
    audioEl.addEventListener('play', () => { audioState.playing = true })
    audioEl.addEventListener('pause', () => { audioState.playing = false })
    audioEl.addEventListener('ended', () => {
      audioState.playing = false
      audioState.currentTime = 0
      audioState.src = ''
      audioState.title = ''
    })
  }
  return audioEl
}

export function playAudio(src: string, title: string) {
  const audio = ensureAudio()
  if (audio.src !== src) {
    audio.src = src
    audio.load()
  }
  audio.volume = audioState.volume
  audio.playbackRate = audioState.speed
  audio.play().catch(() => {})
  audioState.src = src
  audioState.title = title
  audioState.playing = true
  audioState.currentTime = 0
  audioState.duration = 0
}

export function toggleAudio() {
  const audio = ensureAudio()
  if (!audio.src) return
  if (audio.paused) {
    audio.play().catch(() => {})
  } else {
    audio.pause()
  }
}

export function seekAudio(time: number) {
  if (audioEl) audioEl.currentTime = time
}

export function setSpeed(speed: number) {
  audioState.speed = speed
  if (audioEl) audioEl.playbackRate = speed
}

export function cycleSpeed() {
  const speeds = [0.5, 1, 1.5, 2]
  const idx = speeds.indexOf(audioState.speed)
  const next = speeds[(idx + 1) % speeds.length]
  audioState.speed = next
  if (audioEl) audioEl.playbackRate = next
}

export function setVolume(v: number) {
  audioState.volume = v
  if (audioEl) audioEl.volume = v
}

export function stopAudio() {
  if (audioEl) {
    audioEl.pause()
    audioEl.currentTime = 0
  }
  audioState.playing = false
  audioState.currentTime = 0
  audioState.duration = 0
  audioState.src = ''
  audioState.title = ''
}

export function calcProgress() {
  return audioState.duration ? audioState.currentTime / audioState.duration : 0
}
