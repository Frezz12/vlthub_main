<script setup lang="ts">
const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const email = ref(auth.user?.email || '')
const code = ref('')
const loading = ref(false)
const done = ref(false)

async function handleSubmit() {
  loading.value = true
  try {
    await useApiFetch('/api/v1/auth/confirm-email', {
      method: 'POST',
      body: { email: email.value, code: code.value },
    })
    done.value = true
    if (auth.user) auth.user.is_email_confirmed = true
    toast.show('Email подтверждён', 'success')
  } catch (e: any) {
    toast.show(e.message || 'Неверный код', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-sm mx-4">
    <div class="mb-6 flex justify-center">
      <AppLogo size="lg" :show-icon="false" />
    </div>
    <div class="card p-8 shadow-xl shadow-black/[0.04]">
      <h1 class="text-2xl font-semibold mb-1">Подтверждение email</h1>
      <p class="text-sm text-secondary mb-6" v-if="!done">
        Введите код из письма
      </p>
      <p class="text-sm text-secondary mb-6" v-else>
        Email подтверждён
      </p>

      <form v-if="!done" class="flex flex-col gap-4" @submit.prevent="handleSubmit">
        <UiInput v-model="email" label="Email" type="email" placeholder="you@example.com" />
        <UiInput v-model="code" label="Код из письма" placeholder="000000" maxlength="6" />
        <UiButton :loading="loading" block>Подтвердить</UiButton>
      </form>

      <NuxtLink to="/" class="block text-sm text-primary hover:underline text-center mt-6">
        На главную
      </NuxtLink>
    </div>
  </div>
</template>
