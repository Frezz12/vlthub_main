<script setup lang="ts">
const toastRef = ref<InstanceType<typeof UiToast> | null>(null)

provide('toast', {
  show: (
    message: string,
    type?: 'success' | 'error' | 'info',
    duration?: number,
    action?: { label: string; onClick: () => void },
    position?: 'top' | 'bottom',
    download?: { title: string; fileLabel: string; path: string },
  ) => {
    toastRef.value?.show(message, type, duration, action, position, download)
  },
})

function isTauri() {
  return typeof window !== 'undefined' && (window as any).__TAURI_INTERNALS__
}

async function tryOpenDevtools() {
  try {
    const { getCurrentWindow } = await import('@tauri-apps/api/window')
    await getCurrentWindow().openDevtools()
    return true
  } catch {
    try {
      const invoke = (window as any).__TAURI_INTERNALS__.invoke
      await invoke('open_devtools')
      return true
    } catch {
      return false
    }
  }
}

onMounted(() => {
  if (isTauri()) {
    window.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i'))) {
        e.preventDefault()
        tryOpenDevtools()
      }
    })
  }
  const up = useUploadProgress()
  up // ensure global listener is initialized
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage transition="page" />
    <UiToast ref="toastRef" />
  </NuxtLayout>
</template>
