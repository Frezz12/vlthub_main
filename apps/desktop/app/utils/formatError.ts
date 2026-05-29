const errorMap: [RegExp, string][] = [
  [/NetworkError|Failed to fetch|fetch failed|network.*error/i, 'Нет соединения с сервером. Проверьте интернет и попробуйте снова.'],
  [/Unauthorized/i, 'Сессия истекла. Войдите в аккаунт заново.'],
  [/Storage limit|413|storage.*limit/i, 'Лимит хранилища исчерпан. Освободите место или увеличьте лимит.'],
  [/not.*found|404/i, 'Запрашиваемый ресурс не найден. Возможно, он был удалён.'],
  [/forbidden|403/i, 'Нет доступа к этому ресурсу.'],
  [/conflict|409/i, 'Конфликт данных. Возможно, кто-то уже изменил этот ресурс.'],
  [/(?:already|уже).*(?:exist|существует)/i, 'Запись с таким названием уже существует.'],
  [/too large|file.*too big/i, 'Файл слишком большой.'],
  [/invalid.*credentials|неверный.*(?:email|пароль|логин)/i, 'Неверный email или пароль.'],
  [/invalid.*token/i, 'Ссылка устарела или недействительна. Запросите новую.'],
  [/expired/i, 'Срок действия истёк. Попробуйте снова.'],
  [/rate.*limit/i, 'Слишком много запросов. Подождите немного и попробуйте снова.'],
  [/locked|blocked/i, 'Аккаунт заблокирован.'],
  [/validation.*error|422/i, 'Проверьте введённые данные и попробуйте снова.'],
  [/5\d{2}/, 'Ошибка сервера. Попробуйте позже.'],
  [/invalid updater binary/i, 'Ошибка при загрузке обновления. Попробуйте позже.'],
]

export function formatError(err: unknown): string {
  if (!err) return 'Произошла неизвестная ошибка.'

  const msg = typeof err === 'string' ? err : (err as any)?.message || (err as any)?.toString?.() || ''
  if (!msg) return 'Произошла неизвестная ошибка.'

  for (const [pattern, friendly] of errorMap) {
    if (pattern.test(msg)) return friendly
  }

  return msg
}
