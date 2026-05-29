import type { DawType } from '@pjasaver/shared-types'

const dawNames: Record<DawType, string> = {
  logic_pro: 'Logic Pro',
  ableton: 'Ableton Live',
  fl_studio: 'FL Studio',
  cubase: 'Cubase',
  reaper: 'REAPER',
  studio_one: 'Studio One',
  bitwig: 'Bitwig',
  other: 'DAW',
}

export function useDawIcon() {
  function getDawName(daw: DawType): string {
    return dawNames[daw] || 'DAW'
  }

  function getDawColor(daw: DawType): string {
    const colors: Record<DawType, string> = {
      logic_pro: '#000000',
      ableton: '#0000FF',
      fl_studio: '#FF6600',
      cubase: '#00BFFF',
      reaper: '#6B3FA0',
      studio_one: '#00A86B',
      bitwig: '#FF4400',
      other: '#86868B',
    }
    return colors[daw] || '#86868B'
  }

  return { getDawName, getDawColor }
}
