import { createI18n } from 'vue-i18n'
import en from './locales/en'
import zhCN from './locales/zh-CN'
import zhHK from './locales/zh-HK'

export const SUPPORTED_LOCALES = [
  { code: 'en', label: 'English' },
  { code: 'zh-CN', label: '普通话' },
  { code: 'zh-HK', label: '廣東話' },
] as const

export type LocaleCode = (typeof SUPPORTED_LOCALES)[number]['code']

const STORAGE_KEY = 'cantolens-locale'

function detectLocale(): LocaleCode {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved && SUPPORTED_LOCALES.some((l) => l.code === saved)) {
    return saved as LocaleCode
  }
  const browserLang = navigator.language
  if (browserLang.startsWith('zh')) {
    return /HK|MO|Hant/i.test(browserLang) ? 'zh-HK' : 'zh-CN'
  }
  return 'en'
}

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: detectLocale(),
  fallbackLocale: 'en',
  messages: {
    en,
    'zh-CN': zhCN,
    'zh-HK': zhHK,
  },
})

export function setLocale(code: LocaleCode) {
  i18n.global.locale.value = code
  localStorage.setItem(STORAGE_KEY, code)
}

export default i18n
