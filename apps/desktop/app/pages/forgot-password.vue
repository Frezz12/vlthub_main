<script setup lang="ts">
</script>

<template>
  <div class="w-full max-w-sm mx-4">
    <div class="mb-6 flex justify-center">
      <AppLogo size="lg" :show-icon="false" />
    </div>
    <div class="card p-8 text-center shadow-xl shadow-black/[0.04]">
      <h1 class="text-2xl font-semibold mb-4">Сброс пароля</h1>
      <p class="text-sm text-secondary mb-6">
        Смена пароля без email —
        <NuxtLink to="/reset-password" class="text-primary hover:underline">перейти</NuxtLink>
      </p>
      <NuxtLink to="/login" class="block text-sm text-primary hover:underline text-center">
        Вернуться ко входу
      </NuxtLink>
    </div>
  </div>
</template>
