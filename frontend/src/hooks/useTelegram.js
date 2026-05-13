/**
 * Хук для работы с Telegram WebApp SDK.
 * Изолируем всё взаимодействие с window.Telegram здесь —
 * проще тестировать и проще понимать что TMA-специфично.
 */

const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : null

export function useTelegram() {
  return {
    /** Сырые initData для отправки на бэкенд */
    initData: tg?.initData ?? '',

    /** Объект пользователя из Telegram (не путай с нашей БД) */
    tgUser: tg?.initDataUnsafe?.user ?? null,

    /** Вызывает нативную кнопку "назад" в TMA */
    showBackButton: (onBack) => {
      if (!tg) return
      tg.BackButton.show()
      tg.BackButton.onClick(onBack)
    },

    hideBackButton: () => {
      if (!tg) return
      tg.BackButton.hide()
    },

    /** Тактильный отклик (работает на мобильных устройствах) */
    haptic: (type = 'light') => {
      tg?.HapticFeedback?.impactOccurred(type)
    },

    /** true если открыто внутри Telegram */
    isInTelegram: !!tg,
  }
}
