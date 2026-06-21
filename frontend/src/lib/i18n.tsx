import { createContext, useContext, useState } from 'react'
import zhCN from '../locales/zh-CN'
import enUS from '../locales/en-US'

export type LocaleKey = 'zh-CN' | 'en-US'

type DeepString<T> = T extends (...args: infer A) => infer R
  ? (...args: A) => DeepString<R>
  : T extends object
    ? { [K in keyof T]: DeepString<T[K]> }
    : string

const dictionaries: Record<LocaleKey, DeepString<typeof zhCN>> = {
  'zh-CN': zhCN as DeepString<typeof zhCN>,
  'en-US': enUS as DeepString<typeof zhCN>,
}

const I18nContext = createContext<{
  locale: LocaleKey
  setLocale: (l: LocaleKey) => void
  t: DeepString<typeof zhCN>
}>({
  locale: 'zh-CN',
  setLocale: () => {},
  t: dictionaries['zh-CN'],
})

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocale] = useState<LocaleKey>('zh-CN')
  const t = dictionaries[locale]
  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>
}

export function useI18n() {
  return useContext(I18nContext)
}
