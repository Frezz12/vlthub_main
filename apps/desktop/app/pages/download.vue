<script setup lang="ts">
import type { Ref } from 'vue'

const GITHUB_REPO = 'Frezz12/vlthub_main'

interface ReleaseAsset {
  name: string
  browser_download_url: string
  size?: number
}

const release = ref<{ tag_name: string; assets: ReleaseAsset[] } | null>(null)
const loading = ref(true)

function matchPlatform(name: string): 'mac' | 'macIntel' | 'windows' | null {
  if (name.endsWith('aarch64.dmg')) return 'mac'
  if (name.endsWith('x64.dmg')) return 'macIntel'
  if (name.match(/x64(-setup)?\.(exe|msi)$/)) return 'windows'
  return null
}

onMounted(async () => {
  try {
    const res = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`)
    if (!res.ok) throw new Error('Failed to fetch release')
    const data = await res.json()
    release.value = {
      tag_name: data.tag_name,
      assets: (data.assets || []).map((a: any) => ({
        name: a.name,
        browser_download_url: a.browser_download_url,
        size: a.size,
      })),
    }
  } catch {
    release.value = null
  } finally {
    loading.value = false
  }

  const { useIntersectionObserver } = await import('@vueuse/core')
  const observe = (el: Ref<HTMLElement | null>, key: string) => {
    if (!el.value) return
    const { stop } = useIntersectionObserver(el, ([{ isIntersecting }]) => {
      if (isIntersecting) visibleSections.value[key] = true
    })
    stopObservers.push(stop)
  }
  observe(featuresRef, 'features')
  observe(howRef, 'how')
  observe(audienceRef, 'audience')
  visibleSections.value.cta = true
})

const downloadLinks = computed(() => {
  const d = release.value
  if (!d) return null
  const assets = d.assets
  return {
    mac: assets.find(a => matchPlatform(a.name) === 'mac') || null,
    macIntel: assets.find(a => matchPlatform(a.name) === 'macIntel') || null,
    windows: assets.find(a => matchPlatform(a.name) === 'windows') || null,
    version: d.tag_name,
  }
})

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

let stopObservers: (() => void)[] = []

const visibleSections = ref<Record<string, boolean>>({})
const featuresRef = ref<HTMLElement | null>(null)
const howRef = ref<HTMLElement | null>(null)
const audienceRef = ref<HTMLElement | null>(null)
const ctaRef = ref<HTMLElement | null>(null)

onUnmounted(() => {
  stopObservers.forEach(fn => fn())
})
</script>

<template>
  <div class="download-page relative w-full overflow-x-hidden min-h-screen">
    <!-- Animated background orbs -->
    <div class="fixed inset-0 -z-10">
      <div class="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-surface" />
      <div class="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] animate-drift" />
      <div class="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[100px] animate-drift-reverse" />
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/[0.03] rounded-full blur-[150px]" />

      <!-- Floating particles -->
      <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div v-for="i in 12" :key="i" class="particle" :style="{
          left: `${10 + (i * 7) % 80}%`,
          top: `${(i * 13) % 90}%`,
          width: `${4 + (i % 3) * 2}px`,
          height: `${4 + (i % 3) * 2}px`,
          animationDuration: `${6 + (i % 5) * 2}s`,
          animationDelay: `${i * 0.4}s`,
        }" />
      </div>
    </div>

    <!-- Hero -->
    <section class="relative pt-20 pb-16 sm:pt-28 sm:pb-24 px-4">
      <div class="max-w-4xl mx-auto text-center">
        <div class="mb-8 animate-fade-in-up">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-purple-500/20 border border-primary/10 mb-6 shadow-lg shadow-primary/5">
            <svg class="w-10 h-10 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-foreground bg-gradient-to-r from-foreground via-foreground to-primary/70 bg-clip-text text-transparent">
            Менеджер DAW-проектов
          </h1>
          <p class="mt-4 text-lg sm:text-xl text-secondary max-w-2xl mx-auto">
            VLTHub — это удобное приложение для хранения, версионирования и совместной работы
            над музыкальными проектами. Загружайте проекты из любой DAW и работайте где угодно.
          </p>
          <p class="mt-2 text-sm text-secondary/60">
            <template v-if="downloadLinks">Версия {{ downloadLinks.version }} ·</template>
            Бесплатно · Для macOS и Windows
          </p>
        </div>

        <div class="mt-10 flex flex-wrap items-center justify-center gap-4 animate-fade-in-up delay-3">
          <template v-if="downloadLinks?.mac">
            <a :href="downloadLinks.mac.browser_download_url" class="download-btn-glow">
              <UiButton size="lg" class="gap-3">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Скачать для macOS
              </UiButton>
            </a>
          </template>
          <UiButton v-else size="lg" disabled class="gap-3">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <template v-if="loading">Загрузка...</template>
            <template v-else>macOS недоступен</template>
          </UiButton>
          <template v-if="downloadLinks?.windows">
            <a :href="downloadLinks.windows.browser_download_url" class="download-btn-glow">
              <UiButton variant="secondary" size="lg" class="gap-3">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Скачать для Windows
              </UiButton>
            </a>
          </template>
          <UiButton v-else variant="secondary" size="lg" disabled class="gap-3">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <template v-if="loading">Загрузка...</template>
            <template v-else>Windows недоступен</template>
          </UiButton>
          <a href="https://vlthub.ru" target="_blank">
            <UiButton variant="ghost" size="lg" class="gap-3">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              Web версия
            </UiButton>
          </a>
        </div>

        <div class="mt-6 flex items-center justify-center gap-6 text-xs text-secondary/50">
          <a v-if="downloadLinks?.macIntel" :href="downloadLinks.macIntel.browser_download_url" class="hover:text-primary transition-colors">macOS (Intel)</a>
          <span v-if="downloadLinks?.macIntel" class="text-secondary/20">·</span>
          <NuxtLink to="/login" class="hover:text-primary transition-colors">Войти</NuxtLink>
          <span class="text-secondary/20">·</span>
          <NuxtLink to="/register" class="hover:text-primary transition-colors">Регистрация</NuxtLink>
        </div>

        <div v-if="downloadLinks?.mac || downloadLinks?.macIntel" class="mt-6 mx-auto max-w-lg rounded-xl bg-amber-500/5 border border-amber-500/15 p-3 text-left">
          <p class="text-xs text-amber-600/80 dark:text-amber-400/80 leading-relaxed">
            <span class="font-medium">Для macOS:</span> После установки может потребоваться снять карантин —
            откройте Терминал и выполните:
          </p>
          <code class="mt-1.5 block text-xs bg-background/60 rounded-lg px-3 py-2 select-all font-mono text-amber-600 dark:text-amber-400 border border-amber-500/10">
            sudo xattr -rd com.apple.quarantine /Applications/VLTHub.app
          </code>
        </div>
      </div>
    </section>

    <!-- Decorative divider -->
    <div class="relative flex items-center justify-center py-4">
      <div class="w-px h-12 bg-gradient-to-b from-transparent via-primary/20 to-transparent" />
    </div>

    <!-- Features -->
    <section ref="featuresRef" class="py-16 sm:py-20 px-4">
      <div class="max-w-6xl mx-auto">
        <div :class="['transition-all duration-700', visibleSections.features ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8']">
          <h2 class="text-3xl sm:text-4xl font-bold text-center text-foreground mb-4">Возможности</h2>
          <p class="text-secondary text-center max-w-xl mx-auto mb-12 text-base">
            Всё необходимое для работы с музыкальными проектами в одном месте
          </p>
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="(f, i) in features"
            :key="i"
            :class="['card p-6 bg-gradient-to-br from-background/80 to-background/40 backdrop-blur-sm border border-separator/50 transition-all duration-500 feature-card', visibleSections.features ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12']"
            :style="{ transitionDelay: `${i * 80}ms` }"
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

    <!-- Decorative divider -->
    <div class="relative flex items-center justify-center py-4">
      <div class="flex items-center gap-3">
        <div class="w-8 h-px bg-gradient-to-r from-transparent to-primary/20" />
        <div class="w-1.5 h-1.5 rounded-full bg-primary/20" />
        <div class="w-8 h-px bg-gradient-to-l from-transparent to-primary/20" />
      </div>
    </div>

    <!-- How it works -->
    <section ref="howRef" class="py-16 sm:py-20 px-4">
      <div class="max-w-4xl mx-auto">
        <div :class="['transition-all duration-700', visibleSections.how ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8']">
          <h2 class="text-3xl sm:text-4xl font-bold text-center text-foreground mb-4">Как это работает</h2>
          <p class="text-secondary text-center max-w-xl mx-auto mb-12 text-base">
            Всё просто: установите приложение, выберите папку с проектом и сохраните его
          </p>
        </div>
        <div class="grid sm:grid-cols-3 gap-8 text-center">
          <div
            v-for="(step, i) in [
              { num: '1', title: 'Установите приложение', desc: 'Скачайте VLTHub для вашей платформы и установите', icon: 'M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
              { num: '2', title: 'Выберите папку проекта', desc: 'Укажите папку с вашим DAW-проектом в удобном диалоге', icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' },
              { num: '3', title: 'Сохраните в облако', desc: 'Проект автоматически упакуется и загрузится на сервер', icon: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' },
            ]"
            :key="i"
            :class="['transition-all duration-500', visibleSections.how ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12']"
            :style="{ transitionDelay: `${i * 120}ms` }"
          >
            <div class="p-6 step-card">
              <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-purple-500/20 text-primary flex items-center justify-center mx-auto mb-4 text-2xl font-bold border border-primary/10 transition-all duration-300 step-number">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" :d="step.icon" />
                </svg>
              </div>
              <h3 class="font-semibold text-foreground mb-2">{{ step.title }}</h3>
              <p class="text-sm text-secondary">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Decorative divider -->
    <div class="relative flex items-center justify-center py-4">
      <div class="flex items-center gap-3">
        <div class="w-16 h-px bg-gradient-to-r from-transparent to-primary/10" />
        <div class="w-2 h-2 rotate-45 border border-primary/10" />
        <div class="w-16 h-px bg-gradient-to-l from-transparent to-primary/10" />
      </div>
    </div>

    <!-- For whom -->
    <section ref="audienceRef" class="py-16 sm:py-20 px-4">
      <div class="max-w-4xl mx-auto text-center">
        <div :class="['transition-all duration-700', visibleSections.audience ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8']">
          <h2 class="text-3xl sm:text-4xl font-bold text-foreground mb-4">Для кого это</h2>
          <p class="text-secondary max-w-xl mx-auto mb-10 text-base">
            VLTHub пригодится каждому, кто работает с музыкой
          </p>
        </div>
        <div class="grid sm:grid-cols-3 gap-8 text-left">
          <div
            v-for="(item, i) in [
              { emoji: '🎹', title: 'Продюсеры', desc: 'Храните биты, инструменталы и готовые треки. Больше никаких «final_v2_окончательный.flp»' },
              { emoji: '🎧', title: 'Саунд-дизайнеры', desc: 'Версионируйте сэшны, пресеты и проекты. В любой момент вернитесь к любому варианту' },
              { emoji: '🤝', title: 'Коллабораторы', desc: 'Делитесь проектами с командой, управляйте доступом и работайте вместе без путаницы в версиях' },
            ]"
            :key="i"
            :class="['card p-6 bg-gradient-to-br from-background/80 to-background/40 backdrop-blur-sm border border-separator/50 transition-all duration-500 audience-card', visibleSections.audience ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12']"
            :style="{ transitionDelay: `${i * 100}ms` }"
          >
            <span class="text-2xl mb-2 block">{{ item.emoji }}</span>
            <h3 class="font-semibold text-foreground mb-2">{{ item.title }}</h3>
            <p class="text-sm text-secondary leading-relaxed">{{ item.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-16 sm:py-20 px-4 relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-b from-primary/[0.02] to-transparent pointer-events-none" />
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
      <div ref="ctaRef" class="max-w-2xl mx-auto text-center relative">
        <div :class="['transition-all duration-700', visibleSections.cta ? 'opacity-100 scale-100' : 'opacity-0 scale-95']">
          <h2 class="text-3xl sm:text-4xl font-bold text-foreground mb-4">Готовы начать?</h2>
          <p class="text-secondary max-w-lg mx-auto mb-8 text-base">
            Скачайте приложение или откройте веб-версию прямо сейчас
          </p>
          <div class="flex flex-wrap items-center justify-center gap-4">
            <template v-if="downloadLinks?.mac">
              <a :href="downloadLinks.mac.browser_download_url" class="download-btn-glow">
                <UiButton size="lg" class="gap-3">
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Скачать для macOS
                </UiButton>
              </a>
            </template>
            <UiButton v-else size="lg" disabled class="gap-3">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <template v-if="loading">Загрузка...</template>
              <template v-else>macOS недоступен</template>
            </UiButton>
            <template v-if="downloadLinks?.windows">
              <a :href="downloadLinks.windows.browser_download_url" class="download-btn-glow">
                <UiButton variant="secondary" size="lg" class="gap-3">
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Скачать для Windows
                </UiButton>
              </a>
            </template>
            <UiButton v-else variant="secondary" size="lg" disabled class="gap-3">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <template v-if="loading">Загрузка...</template>
              <template v-else>Windows недоступен</template>
            </UiButton>
            <a href="https://vlthub.ru" target="_blank">
              <UiButton variant="ghost" size="lg" class="gap-3">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                Web версия
              </UiButton>
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- Divider before footer -->
    <div class="relative flex items-center justify-center py-2">
      <div class="w-full max-w-4xl h-px bg-gradient-to-r from-transparent via-separator to-transparent" />
    </div>

    <!-- Footer -->
    <footer class="py-8 px-4">
      <div class="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <AppLogo />
        </div>
        <div class="flex items-center gap-6 text-xs text-secondary/50">
          <NuxtLink to="/login" class="hover:text-primary transition-colors">Войти</NuxtLink>
          <NuxtLink to="/register" class="hover:text-primary transition-colors">Регистрация</NuxtLink>
          <span v-if="downloadLinks">{{ downloadLinks.version }}</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.download-page {
  --color-primary: #007AFF;
  --color-primary-light: #409CFF;
  --color-primary-dark: #0055CC;
  --color-surface: #F5F5F7;
  --color-surface-elevated: #FFFFFF;
  --color-text: #1D1D1F;
  --color-text-muted: #48484A;
  --color-secondary: #86868B;
  --color-border: #E5E5EA;
  --color-border-light: rgba(229, 229, 234, 0.6);
  --color-separator: rgba(0, 0, 0, 0.08);
  --color-input-bg: #F5F5F7;
  --color-input-border: #E5E5EA;
  --color-avatar-ring: rgba(0, 0, 0, 0.06);
  --color-hover: rgba(0, 0, 0, 0.04);
  --color-btn-secondary: #E5E5EA;
  --color-btn-secondary-hover: #D1D1D6;
  --color-muted-surface: #FAFAFA;
  --color-glass: rgba(255, 255, 255, 0.72);
  --color-glass-panel: rgba(255, 255, 255, 0.85);
  --color-chip-bg: #F5F5F7;
  --color-tab-active-bg: #1D1D1F;
  --color-tab-active-text: #FFFFFF;
  --color-nav-muted: #6E6E73;
  --color-heatmap-empty: #EBEDF0;
  --color-background: #fff;
  background-color: var(--color-surface);
  color: var(--color-text);
}

.download-page .text-foreground {
  color: var(--color-text);
}
.download-page .text-secondary {
  color: var(--color-secondary);
}
.download-page .text-secondary\/60 {
  color: color-mix(in srgb, var(--color-secondary) 60%, transparent);
}
.download-page .text-secondary\/50 {
  color: color-mix(in srgb, var(--color-secondary) 50%, transparent);
}
.download-page .text-secondary\/20 {
  color: color-mix(in srgb, var(--color-secondary) 20%, transparent);
}
.download-page .from-foreground {
  --tw-gradient-from: var(--color-text);
}
.download-page .via-foreground {
  --tw-gradient-via: var(--color-text);
}
.download-page .to-primary\/70 {
  --tw-gradient-to: color-mix(in srgb, var(--color-primary) 70%, transparent);
}
.download-page .border-separator\/50 {
  border-color: color-mix(in srgb, var(--color-separator) 50%, transparent);
}
.download-page .from-background\/80 {
  --tw-gradient-from: color-mix(in srgb, #fff 80%, transparent);
}
.download-page .to-background\/40 {
  --tw-gradient-to: color-mix(in srgb, #fff 40%, transparent);
}
.download-page .bg-background\/60 {
  background-color: color-mix(in srgb, #fff 60%, transparent);
}

/* Particle animation */
.particle {
  position: absolute;
  border-radius: 50%;
  background: var(--color-primary);
  opacity: 0.15;
  animation: float-particle linear infinite;
}

@keyframes float-particle {
  0% {
    transform: translateY(0) translateX(0);
    opacity: 0;
  }
  10% {
    opacity: 0.15;
  }
  90% {
    opacity: 0.15;
  }
  100% {
    transform: translateY(-100vh) translateX(30px);
    opacity: 0;
  }
}

/* Animated background orbs */
@keyframes drift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

@keyframes drift-reverse {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-30px, 30px) scale(1.05); }
  66% { transform: translate(20px, -20px) scale(0.95); }
}

.animate-drift {
  animation: drift 20s ease-in-out infinite;
}

.animate-drift-reverse {
  animation: drift-reverse 25s ease-in-out infinite;
}

/* Feature card hover */
.feature-card {
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  opacity: 0;
  background: linear-gradient(135deg, var(--color-primary) 0%, transparent 50%);
  transition: opacity 0.4s ease;
  pointer-events: none;
}

.feature-card:hover::before {
  opacity: 0.04;
}

.feature-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 0 20px color-mix(in srgb, var(--color-primary) 10%, transparent);
  transform: translateY(-2px);
}

/* Step card hover */
.step-card {
  transition: transform 0.3s ease;
}

.step-card:hover {
  transform: translateY(-4px);
}

.step-card:hover .step-number {
  transform: scale(1.1);
  box-shadow: 0 0 20px color-mix(in srgb, var(--color-primary) 15%, transparent);
}

/* Audience card hover */
.audience-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.audience-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px color-mix(in srgb, var(--color-primary) 10%, transparent);
}

/* Download button glow */
.download-btn-glow {
  position: relative;
}

.download-btn-glow::after {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--color-primary), transparent, var(--color-primary));
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
  filter: blur(8px);
}

.download-btn-glow:hover::after {
  opacity: 0.5;
}

/* Staggered animation delay helpers */
.delay-1 { animation-delay: 0.05s; }
.delay-2 { animation-delay: 0.1s; }
.delay-3 { animation-delay: 0.15s; }
.delay-4 { animation-delay: 0.2s; }
.delay-5 { animation-delay: 0.25s; }
.delay-6 { animation-delay: 0.3s; }
.delay-7 { animation-delay: 0.35s; }
.delay-8 { animation-delay: 0.4s; }

/* Gradient text for heading */
.bg-clip-text {
  -webkit-background-clip: text;
  background-clip: text;
}
</style>
