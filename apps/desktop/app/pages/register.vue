<script setup lang="ts">
const auth = useAuthStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const nickname = ref('')
const username = ref('')
const loading = ref(false)
const termsAccepted = ref(false)
const showTermsModal = ref(false)

async function handleRegister() {
  if (password.value !== passwordConfirm.value) {
    toast.show('Пароли не совпадают', 'error')
    return
  }
  if (password.value.length < 6) {
    toast.show('Пароль должен быть не менее 6 символов', 'error')
    return
  }
  if (!termsAccepted.value) {
    toast.show('Необходимо принять пользовательское соглашение', 'error')
    return
  }
  loading.value = true
  try {
    await auth.register({ email: email.value, password: password.value, nickname: nickname.value, username: username.value })
    toast.show('Аккаунт создан', 'success')
    navigateTo('/')
  } catch (e: any) {
    toast.show(e.message || 'Ошибка регистрации', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-sm mx-4 animate-fade-in-up">
    <div class="mb-8 flex justify-center">
      <AppLogo size="lg" />
    </div>
    <div class="card p-8 shadow-xl shadow-black/[0.04]">
      <h1 class="text-2xl font-semibold mb-1">Регистрация</h1>
      <p class="text-sm text-secondary mb-6">Создайте аккаунт для работы с проектами</p>

      <form class="flex flex-col gap-4" @submit.prevent="handleRegister">
        <UiInput v-model="email" label="Email" type="email" />
        <UiInput v-model="nickname" label="Никнейм" />
        <UiInput v-model="username" label="Username" />
        <UiInput v-model="password" label="Пароль" type="password" />
        <UiInput v-model="passwordConfirm" label="Подтверждение пароля" type="password" />

        <div class="flex items-start gap-2 text-sm text-secondary">
          <input
            id="terms-checkbox"
            v-model="termsAccepted"
            type="checkbox"
            class="mt-0.5 w-4 h-4 rounded border-border bg-input-bg text-primary focus:ring-primary/30 shrink-0"
          />
          <label for="terms-checkbox" class="cursor-pointer">
            Я принимаю
          </label>
          <button type="button" class="text-primary font-medium hover:underline underline-offset-2 bg-transparent border-none p-0 inline cursor-pointer" @click="showTermsModal = true">пользовательское соглашение</button>
        </div>

        <UiButton :loading="loading" block class="mt-2">
          Создать аккаунт
        </UiButton>
      </form>

      <p class="text-sm text-secondary text-center mt-6">
        Уже есть аккаунт?
        <NuxtLink to="/login" class="text-primary font-medium hover:underline">Войти</NuxtLink>
      </p>
    </div>
  </div>

  <UiModal v-model="showTermsModal" title="Пользовательское соглашение" max-width="640px">
    <div class="space-y-4 text-sm leading-relaxed text-[#1d1d1f] dark:text-[#f5f5f7]">
      <p>Пожалуйста, внимательно прочтите следующее соглашение об условиях использования перед использованием сервиса VLTHub. Получая доступ к веб-сайту <strong>vlthub.ru</strong> и/или услугам, предлагаемым VLTHub через веб-сайт, вы соглашаетесь соблюдать все условия настоящего Соглашения, включая вносимые в него время от времени правки. Если вы не согласны с этими условиями, пожалуйста, не используйте данный сайт.</p>

      <section>
        <h3 class="font-semibold mt-6 mb-2">1. Внесение изменений в настоящее Соглашение</h3>
        <p>VLTHub оставляет за собой право пересматривать настоящее Соглашение по своему собственному усмотрению в любое время и без предварительного уведомления вас, за исключением размещения пересмотренного Соглашения на Сайте. Любые изменения к настоящему Соглашению вступают в силу с момента их публикации. Вы обязаны периодически посещать данную страницу, чтобы обеспечить дальнейшее принятие настоящего Соглашения вами.</p>
      </section>

      <section>
        <h3 class="font-semibold mt-6 mb-2">2. Использование Сайта и Услуг</h3>
        <p><strong>Правомочность.</strong> VLTHub предоставляет Сайт и Услуги только сторонам, которые могут на законных основаниях заключать договоры.</p>
        <p><strong>Лицензия.</strong> VLTHub предоставляет вам ограниченную лицензию с возможностью отзыва на доступ и использование Сайта и Услуг по их прямому назначению.</p>
        <p><strong>Запрещенное использование.</strong> Вы не можете: вмешиваться в работу Сервисов; изменять, декомпилировать или дизассемблировать технологии VLTHub; использовать программы-роботы; собирать данные о третьих лицах; выдавать себя за другое лицо.</p>
        <p><strong>Политика конфиденциальности.</strong> Заключая настоящее Соглашение, вы соглашаетесь на сбор, использование и раскрытие ваших персональных данных в соответствии с Политикой конфиденциальности VLTHub.</p>
      </section>

      <section>
        <h3 class="font-semibold mt-6 mb-2">3. Имущественные Права</h3>
        <p>Сайт и его содержание защищены законами об авторском праве, товарных знаках и другими законами. Все права на интеллектуальную собственность являются исключительной собственностью VLTHub.</p>
      </section>

      <section>
        <h3 class="font-semibold mt-6 mb-2">4. Отказ от ответственности</h3>
        <p>VLTHub ПРЕДОСТАВЛЯЕТ САЙТ И УСЛУГИ НА УСЛОВИЯХ «КАК ЕСТЬ». VLTHub НЕ ГАРАНТИРУЕТ, ЧТО САЙТ БУДЕТ БЕСПЕРЕБОЙНЫМ ИЛИ БЕЗ ОШИБОК. VLTHub НЕ НЕСЕТ ОТВЕТСТВЕННОСТИ ЗА ЛЮБОЙ КОСВЕННЫЙ ИЛИ СЛУЧАЙНЫЙ УЩЕРБ. ОТВЕТСТВЕННОСТЬ VLTHub НЕ ПРЕВЫСИТ 100 ДОЛЛАРОВ США.</p>
      </section>

      <section>
        <h3 class="font-semibold mt-6 mb-2">5. Прекращение использования</h3>
        <p>VLTHub может приостановить или прекратить использование вами Сайта, если считает, что вы нарушили настоящее Соглашение.</p>
      </section>

      <section>
        <h3 class="font-semibold mt-6 mb-2">6. Уведомления</h3>
        <p>Для связи с VLTHub используйте: <strong>support@vlthub.ru</strong>.</p>
      </section>

      <section>
        <h3 class="font-semibold mt-6 mb-2">7. Разрешение споров</h3>
        <p>Споры разрешаются в соответствии с законодательством Российской Федерации.</p>
      </section>

      <section>
        <h3 class="font-semibold mt-6 mb-2">8. Прочие условия</h3>
        <p>Соглашение регулируется законодательством Российской Федерации. Вы даёте согласие на рассылку новостей сервиса и уведомлений на почту, указанную при регистрации.</p>
      </section>
    </div>
  </UiModal>
</template>
