// Canonical category list — id is stored lower-cased in the DB, but the
// frontend uses the Capitalised form when looking up colors/emojis.
export const CATEGORIES = [
  { id: 'Food',          emoji: '🍕' },
  { id: 'Transport',     emoji: '🚌' },
  { id: 'Shopping',      emoji: '🛍' },
  { id: 'Entertainment', emoji: '🎬' },
  { id: 'Health',        emoji: '💊' },
  { id: 'Beauty',        emoji: '💅' },
  { id: 'Housing',       emoji: '🏠' },
  { id: 'Utilities',     emoji: '💡' },
  { id: 'Education',     emoji: '📚' },
  { id: 'Travel',        emoji: '✈️' },
  { id: 'Gifts',         emoji: '🎁' },
  { id: 'Transfer',      emoji: '💸' },
  { id: 'Other',         emoji: '💰' },
]

export const CATEGORY_COLORS = {
  Food: '#F59E0B',
  Transport: '#3B82F6',
  Shopping: '#EC4899',
  Entertainment: '#8B5CF6',
  Health: '#22C55E',
  Beauty: '#D946EF',
  Housing: '#F97316',
  Utilities: '#06B6D4',
  Education: '#6366F1',
  Travel: '#14B8A6',
  Gifts: '#EF4444',
  Transfer: '#0EA5E9',
  Other: '#94A3B8',
}

export const CATEGORY_EMOJI = Object.fromEntries(
  CATEGORIES.map((c) => [c.id, c.emoji]),
)

// DB stores the category lower-cased; UI maps look it up Capitalised.
export const capCat = (cat) =>
  cat ? cat.charAt(0).toUpperCase() + cat.slice(1).toLowerCase() : ''
