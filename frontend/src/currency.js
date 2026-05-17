// Mirrors utils/currency.py on the backend. No conversion — amounts are
// always stored and shown in their original currency.
export const CURRENCIES = ['EUR', 'USD', 'UAH', 'GBP']

export const CURRENCY_SYMBOLS = {
  EUR: '€',
  USD: '$',
  UAH: '₴',
  GBP: '£',
}

export const currencySymbol = (code) => CURRENCY_SYMBOLS[code] ?? code

export const normalizeCurrency = (code) =>
  CURRENCIES.includes(code) ? code : 'EUR'
