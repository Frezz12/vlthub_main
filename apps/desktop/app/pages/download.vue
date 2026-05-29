<script setup lang="ts">
import AnimatedBackground from '~/components/AnimatedBackground.vue'

const features = [
  {
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4',
    title: 'Хранилище проектов',
    desc: 'Загружайте и храните все свои DAW-проекты в облаке. Больше никаких потерянных файлов и запутанных папок.',
  },
  {
    icon: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4',
    title: 'Управление версиями',
    desc: 'Сохраняйте несколько версий одного проекта. В любой момент можно откатиться назад или продолжить работу с любого чекпоинта.',
  },
  {
    icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
    title: 'Совместная работа',
    desc: 'Делитесь проектами с другими пользователями, управляйте доступом и работайте вместе над треками.',
  },
  {
    icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    title: 'Статистика и аналитика',
    desc: 'Отслеживайте активность по проектам, просматривайте историю изменений и анализируйте свою продуктивность.',
  },
  {
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    title: 'Безопасность',
    desc: 'Все данные передаются по защищённому соединению. Доступ к проектам контролируется через гибкую систему разрешений.',
  },
  {
    icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
    title: 'Превью и файлы',
    desc: 'Загружайте превью, обложки и сопутствующие файлы. Всё хранится вместе с проектом и доступно в один клик.',
  },
]

const downloadLinks = {
  mac: { label: 'macOS (Apple Silicon)', arch: 'arm64', file: 'VLTHub_0.2.0_aarch64.dmg' },
  macIntel: { label: 'macOS (Intel)', arch: 'x64', file: 'VLTHub_0.2.0_x64.dmg' },
  windows: { label: 'Windows', arch: 'x64', file: 'VLTHub_0.2.0_x64.exe' },
}

const apiBaseUrl = (typeof __API_BASE_URL__ !== 'undefined' && __API_BASE_URL__) ? __API_BASE_URL__ : 'https://vlthub.ru'

function downloadUrl(file: string) {
  return `${apiBaseUrl}/downloads/${file}`
}
</script>

<template>
  <div class="relative min-h-screen">
    <AnimatedBackground />

    <!-- Hero -->
    <section class="relative pt-24 pb-16 sm:pt-32 sm:pb-24 px-4">
      <div class="max-w-4xl mx-auto text-center">
        <div class="mb-8 animate-fade-in-up">
          <AppLogo size="lg" />
        </div>
        <h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-foreground animate-fade-in-up delay-1">
          Менеджер DAW-проектов
        </h1>
        <p class="mt-4 text-lg sm:text-xl text-secondary max-w-2xl mx-auto animate-fade-in-up delay-2">
          VLTHub — это удобное приложение для хранения, версионирования и совместной работы
          над музыкальными проектами. Загружайте проекты из любой DAW и работайте где угодно.
        </p>
        <div class="mt-10 flex flex-wrap items-center justify-center gap-4 animate-fade-in-up delay-3">
          <a :href="downloadUrl(downloadLinks.mac.file)">
            <UiButton size="lg" class="gap-3">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Скачать для macOS
            </UiButton>
          </a>
          <a :href="downloadUrl(downloadLinks.windows.file)">
            <UiButton variant="secondary" size="lg" class="gap-3">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Скачать для Windows
            </UiButton>
          </a>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="py-16 sm:py-20 px-4 border-t border-separator">
      <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl sm:text-4xl font-bold text-center text-foreground mb-4">Возможности</h2>
        <p class="text-secondary text-center max-w-xl mx-auto mb-12 text-base">
          Всё необходимое для работы с музыкальными проектами в одном месте
        </p>
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="(f, i) in features"
            :key="i"
            class="card p-6 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300 group"
          >
            <div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-4 group-hover:bg-primary group-hover:text-white transition-all duration-300">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" :d="f.icon" />
              </svg>
            </div>
            <h3 class="text-base font-semibold text-foreground mb-2">{{ f.title }}</h3>
            <p class="text-sm text-secondary leading-relaxed">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="py-16 sm:py-20 px-4 border-t border-separator">
      <div class="max-w-4xl mx-auto">
        <h2 class="text-3xl sm:text-4xl font-bold text-center text-foreground mb-4">Как это работает</h2>
        <p class="text-secondary text-center max-w-xl mx-auto mb-12 text-base">
          Всё просто: установите приложение, выберите папку с проектом и сохраните его
        </p>
        <div class="grid sm:grid-cols-3 gap-8 text-center">
          <div>
            <div class="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-4 text-2xl font-bold">1</div>
            <h3 class="font-semibold text-foreground mb-2">Установите приложение</h3>
            <p class="text-sm text-secondary">Скачайте VLTHub для вашей платформы и установите</p>
          </div>
          <div>
            <div class="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-4 text-2xl font-bold">2</div>
            <h3 class="font-semibold text-foreground mb-2">Выберите папку проекта</h3>
            <p class="text-sm text-secondary">Укажите папку с вашим DAW-проектом в удобном диалоге</p>
          </div>
          <div>
            <div class="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-4 text-2xl font-bold">3</div>
            <h3 class="font-semibold text-foreground mb-2">Сохраните в облако</h3>
            <p class="text-sm text-secondary">Проект автоматически упакуется и загрузится на сервер</p>
          </div>
        </div>
      </div>
    </section>

    <!-- For whom -->
    <section class="py-16 sm:py-20 px-4 border-t border-separator">
      <div class="max-w-4xl mx-auto text-center">
        <h2 class="text-3xl sm:text-4xl font-bold text-foreground mb-4">Для кого это</h2>
        <p class="text-secondary max-w-xl mx-auto mb-10 text-base">
          VLTHub пригодится каждому, кто работает с музыкой
        </p>
        <div class="grid sm:grid-cols-3 gap-8 text-left">
          <div class="card p-6">
            <p class="text-2xl mb-2">🎹</p>
            <h3 class="font-semibold text-foreground mb-2">Продюсеры</h3>
            <p class="text-sm text-secondary leading-relaxed">Храните биты, инструменталы и готовые треки. Больше никаких «final_v2_окончательный.flp»</p>
          </div>
          <div class="card p-6">
            <p class="text-2xl mb-2">🎧</p>
            <h3 class="font-semibold text-foreground mb-2">Саунд-дизайнеры</h3>
            <p class="text-sm text-secondary leading-relaxed">Версионируйте сэшны, пресеты и проекты. В любой момент вернитесь к любому варианту</p>
          </div>
          <div class="card p-6">
            <p class="text-2xl mb-2">🤝</p>
            <h3 class="font-semibold text-foreground mb-2">Коллабораторы</h3>
            <p class="text-sm text-secondary leading-relaxed">Делитесь проектами с командой, управляйте доступом и работайте вместе без путаницы в версиях</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="py-8 px-4 border-t border-separator">
      <div class="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <AppLogo />
        </div>
        <div class="flex items-center gap-6 text-xs text-secondary/50">
          <NuxtLink to="/login" class="hover:text-primary transition-colors">Войти</NuxtLink>
          <NuxtLink to="/register" class="hover:text-primary transition-colors">Регистрация</NuxtLink>
          <span>v0.2.0</span>
        </div>
      </div>
    </footer>
  </div>
</template>
