import { watch } from 'vue'
import { createI18n } from 'vue-i18n'

import en from './locales/en.json'
import id from './locales/id.json'

const STORAGE_KEY = 'minimals-lang'
const SUPPORTED = ['en', 'id']

export const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Bahasa Indonesia', value: 'id' },
]

declare global {
  interface Window {
    appLang?: string
  }
}

function cookieLocale(): string {
  const hit = document.cookie.match(/(?:^|;\s*)minimals-lang=([^;]*)/)
  return hit ? decodeURIComponent(hit[1]) : ''
}

function storedLocale(): string {
  const candidates = [
    localStorage.getItem(STORAGE_KEY) ?? '',
    cookieLocale(),
    window.appLang ?? '',
  ]
  for (const candidate of candidates) {
    const lang = candidate.trim().toLowerCase()
    if (SUPPORTED.includes(lang)) return lang
  }
  return 'en'
}

export const i18n = createI18n({
  legacy: false,
  locale: storedLocale(),
  fallbackLocale: 'en',
  messages: { en, id },
})

watch(
  () => i18n.global.locale.value,
  (locale) => {
    localStorage.setItem(STORAGE_KEY, locale)
    document.cookie = `minimals-lang=${locale}; path=/; max-age=31536000; samesite=lax`
    document.documentElement.lang = locale
  },
  { immediate: true },
)
