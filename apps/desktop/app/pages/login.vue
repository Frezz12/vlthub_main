<script setup lang="ts">
import AnimatedBackground from '~/components/AnimatedBackground.vue'

const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const email = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await auth.login({ email: email.value, password: password.value })
    toast.show('Успешный вход', 'success')
    navigateTo('/')
  } catch (e: any) {
    toast.show(e.message || 'Ошибка входа', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="relative flex min-h-screen flex-col items-center justify-center p-4">
    <AnimatedBackground />

    <div class="mb-10 animate-fade-in-up">
      <AppLogo size="lg" />
    </div>

    <div class="w-full max-w-sm animate-fade-in-up delay-1">
      <div class="card p-8 shadow-xl shadow-black/[0.04]">
        <h2 class="text-2xl font-semibold mb-1 text-center">Вход</h2>
        <p class="text-sm text-secondary text-center mb-6">Войдите в свой аккаунт</p>

        <form class="flex flex-col gap-4" @submit.prevent="handleLogin">
          <UiInput v-model="email" label="Email" type="email" placeholder="you@example.com" />
          <UiInput v-model="password" label="Пароль" type="password" placeholder="••••••••" />

          <div class="flex justify-end">
            <NuxtLink to="/reset-password" class="text-sm text-primary font-medium hover:underline transition-colors">
              Забыли пароль?
            </NuxtLink>
          </div>

          <UiButton :loading="loading" block class="mt-2">
            Войти
          </UiButton>
        </form>

        <p class="text-sm text-secondary text-center mt-8">
          Нет аккаунта?
          <NuxtLink to="/register" class="text-primary font-medium hover:underline">Зарегистрироваться</NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>
