import { i18n } from '@/app/i18n'

export const CATEGORY_VALUES = ['cub', 'scout', 'rover'] as const
export const DIFFICULTY_VALUES = ['Easy', 'Medium', 'Hard'] as const
export const STATUS_VALUES = ['Active', 'Inactive'] as const

function lookup(namespace: string, key: string, fallback: string): string {
  const { t, te, locale } = i18n.global
  void locale.value
  const full = `${namespace}.${key}`
  return te(full) ? t(full) : fallback
}

export function categoryLabel(value: string): string {
  return lookup('category', value, value)
}

export function difficultyLabel(value: string): string {
  return lookup('difficulty', value.toLowerCase(), value)
}

export function statusLabel(value: string): string {
  return lookup('status', value.toLowerCase(), value)
}

function withAll(options: { label: string; value: string }[]) {
  return [{ label: i18n.global.t('list.all'), value: '' }, ...options]
}

export function categoryOptions(includeAll = false) {
  const options = CATEGORY_VALUES.map((value) => ({
    label: categoryLabel(value),
    value: value as string,
  }))
  return includeAll ? withAll(options) : options
}

export function difficultyOptions(includeAll = false) {
  const options = DIFFICULTY_VALUES.map((value) => ({
    label: difficultyLabel(value),
    value,
  }))
  return includeAll ? withAll(options) : options
}

export function statusOptions(includeAll = false) {
  const options = STATUS_VALUES.map((value) => ({
    label: statusLabel(value),
    value,
  }))
  return includeAll ? withAll(options) : options
}
