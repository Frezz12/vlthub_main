export default defineNuxtRouteMiddleware(async () => {
  if (import.meta.server) {
    return
  }

  const auth = useAuthStore()
  auth.initFromStorage()

  if (!auth.accessToken) {
    return navigateTo('/login')
  }

  try {
    await auth.fetchMe()
  } catch {
    const refreshed = await auth.refresh()
    if (!refreshed) {
      auth._clearSession()
      return navigateTo('/login')
    }
    try {
      await auth.fetchMe()
    } catch {
      auth._clearSession()
      return navigateTo('/login')
    }
  }
})
