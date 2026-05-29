<script setup lang="ts">
import { formatError } from '~/utils/formatError'
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const pin = ref('')
const loading = ref(false)
const done = ref(false)

async function handleSubmit() {
  if (password.value !== passwordConfirm.value) {
    toast.show('Пароли не совпадают', 'error')
    return
  }
  if (password.value.length < 6) {
    toast.show('Пароль должен быть не менее 6 символов', 'error')
    return
  }
  if (pin.value.length < 4 || pin.value.length > 6 || !/^\d{4,6}$/.test(pin.value)) {
    toast.show('PIN-код должен быть 4-6 цифр', 'error')
    return
  }
  loading.value = true
  try {
    await useApiFetch('/api/v1/auth/reset-password', {
      method: 'POST',
      body: { login: email.value, new_password: password.value, pin: pin.value },
    })
    done.value = true
    toast.show('Пароль изменён', 'success')
  } catch (e: any) {
    toast.show(formatError(e), 'error')
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
      <h1 class="text-2xl font-semibold mb-1">Новый пароль</h1>
      <p class="text-sm text-secondary mb-6" v-if="!done">
        Введите email и новый пароль
      </p>
      <p class="text-sm text-secondary mb-6" v-else>
        Пароль успешно изменён
      </p>

      <form v-if="!done" class="flex flex-col gap-4" @submit.prevent="handleSubmit">
        <UiInput v-model="email" label="Email" type="email" />
        <UiInput v-model="password" label="Новый пароль" type="password" />
        <UiInput v-model="passwordConfirm" label="Подтверждение пароля" type="password" />
        <UiInput
          v-model="pin"
          label="PIN-код"
          type="password"
          maxlength="6"
          hint="PIN-код из настроек аккаунта (4-6 цифр)"
        />
        <UiButton :loading="loading" block>Сохранить</UiButton>
      </form>

      <NuxtLink to="/login" class="block text-sm text-primary hover:underline text-center mt-6">
        Вернуться ко входу
      </NuxtLink>
    </div>
  </div>
</template>
