const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : null

export function useTelegram() {
  return {
    initData: tg?.initData ?? '',

    tgUser: tg?.initDataUnsafe?.user ?? null,

    showBackButton: (onBack) => {
      if (!tg) return
      tg.BackButton.show()
      tg.BackButton.onClick(onBack)
    },

    hideBackButton: () => {
      if (!tg) return
      tg.BackButton.hide()
    },

    haptic: (type = 'light') => {
      tg?.HapticFeedback?.impactOccurred(type)
    },

    isInTelegram: !!tg,
  }
}
