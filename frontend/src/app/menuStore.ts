import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'
import {
  orderedNavItems,
  visibleNavItems,
  type MenuPreference,
} from './navigation'

const ENDPOINT = '/account/menu-preferences'

function stringList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((key): key is string => typeof key === 'string')
    : []
}

export const useMenuStore = defineStore('menu', () => {
  const order = ref<string[]>([])
  const hidden = ref<string[]>([])
  const loaded = ref(false)
  const saving = ref(false)
  const error = ref('')

  let confirmed: MenuPreference = { order: [], hidden: [] }
  let generation = 0

  const allItems = computed(() => orderedNavItems(order.value))
  const items = computed(() => visibleNavItems(order.value, hidden.value))

  function apply(preference: MenuPreference) {
    order.value = [...preference.order]
    hidden.value = [...preference.hidden]
    confirmed = {
      order: [...preference.order],
      hidden: [...preference.hidden],
    }
  }

  async function fetchPreference() {
    const current = ++generation
    error.value = ''
    loaded.value = false
    try {
      const { data } = await api.get(ENDPOINT)
      if (current !== generation) return
      apply({ order: stringList(data.order), hidden: stringList(data.hidden) })
    } catch {
      if (current !== generation) return
      apply({ order: [], hidden: [] })
    } finally {
      if (current === generation) loaded.value = true
    }
  }

  async function persist(next: MenuPreference): Promise<boolean> {
    const current = generation
    error.value = ''
    order.value = [...next.order]
    hidden.value = [...next.hidden]
    saving.value = true
    try {
      await api.put(ENDPOINT, next)
      if (current === generation) {
        confirmed = { order: [...next.order], hidden: [...next.hidden] }
      }
      return true
    } catch (e: any) {
      if (current === generation) {
        order.value = [...confirmed.order]
        hidden.value = [...confirmed.hidden]
        error.value = getErrorMessage(
          e,
          i18n.global.t('settings.menu.saveFailed'),
        )
      }
      return false
    } finally {
      if (current === generation) saving.value = false
    }
  }

  async function move(from: number, to: number): Promise<boolean> {
    const keys = allItems.value.map((item) => item.key)
    if (from === to) return true
    if (from < 0 || to < 0 || from >= keys.length || to >= keys.length) return false

    const [moved] = keys.splice(from, 1)
    keys.splice(to, 0, moved)
    return persist({ order: keys, hidden: hidden.value })
  }

  async function setVisible(key: string, visible: boolean): Promise<boolean> {
    const others = hidden.value.filter((item) => item !== key)
    return persist({
      order: order.value,
      hidden: visible ? others : [...others, key],
    })
  }

  function reset() {
    generation += 1
    order.value = []
    hidden.value = []
    loaded.value = false
    saving.value = false
    error.value = ''
    confirmed = { order: [], hidden: [] }
  }

  return {
    order,
    hidden,
    loaded,
    saving,
    error,
    allItems,
    items,
    fetchPreference,
    move,
    setVisible,
    reset,
  }
})
