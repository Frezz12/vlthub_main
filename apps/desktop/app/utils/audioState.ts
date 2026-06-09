import { reactive } from 'vue'

export interface AudioPreviewState {
  src: string
  title: string
  playing: boolean
  currentTime: number
  duration: number
  speed: number
  volume: number
}

export const audioState = reactive<AudioPreviewState>({
  src: '',
  title: '',
  playing: false,
  currentTime: 0,
  duration: 0,
  speed: 1,
  volume: 1,
})
