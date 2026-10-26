import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface AdminEvent {
  name: string
  eventName: string
  category: string
  timeLimit: number
  eventDeadline: string
  published: boolean
  description?: string | null
  disabled: boolean
  disabledAt?: string | null
  createdAt?: string | null
  updatedAt?: string | null
  questionCount: number
}

export interface AdminEventDetail extends AdminEvent {
  questions: Record<string, any>[]
}

export interface AdminEventPayload {
  eventName: string
  eventDeadline: string
  category: string
  timeLimit: number
  questionsId: string[]
  published: boolean
  description?: string | null
}

export interface AdminEventPage {
  items: AdminEvent[]
  total: number
  page: number
  perPage: number
}

export interface EventResultRow {
  name: string
  studentId: string
  score?: number | null
  timeLimit?: number | null
  startedAt?: string | null
  finishedAt?: string | null
}

export const useEventStore = defineStore('event', () => {
  const items = ref<AdminEvent[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const loading = ref(false)
  const error = ref('')
  const current = ref<AdminEventDetail | null>(null)
  const currentLoading = ref(false)
  const results = ref<EventResultRow[]>([])

  async function list(
    query: { category?: string; published?: boolean; page?: number; perPage?: number } = {},
  ): Promise<boolean> {
    error.value = ''
    loading.value = true
    try {
      const params: Record<string, string | number> = {
        page: query.page ?? page.value,
        per_page: query.perPage ?? perPage.value,
      }
      if (query.category) params.category = query.category
      if (query.published !== undefined) params.published = String(query.published)
      const { data } = await api.get<AdminEventPage>('/event', { params })
      items.value = data.items ?? []
      total.value = data.total
      page.value = data.page
      perPage.value = data.perPage
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('event.loadEvents'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function get(name: string): Promise<AdminEventDetail | null> {
    error.value = ''
    currentLoading.value = true
    current.value = null
    try {
      const { data } = await api.get<AdminEventDetail>(`/event/${name}`)
      current.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('event.loadEvent'))
      return null
    } finally {
      currentLoading.value = false
    }
  }

  async function create(payload: AdminEventPayload): Promise<AdminEvent | null> {
    error.value = ''
    try {
      const { data } = await api.post<AdminEvent>('/event', payload)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('event.createFailed'))
      return null
    }
  }

  async function update(name: string, payload: Partial<AdminEventPayload>): Promise<AdminEvent | null> {
    error.value = ''
    try {
      const { data } = await api.patch<AdminEvent>(`/event/${name}`, payload)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('event.updateEvent'))
      return null
    }
  }

  async function softDelete(name: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/event/${name}`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('event.deleteEvent'))
      return false
    }
  }

  async function restore(name: string): Promise<AdminEvent | null> {
    error.value = ''
    try {
      const { data } = await api.post<AdminEvent>(`/event/${name}/restore`)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('event.restoreFailed'))
      return null
    }
  }

  async function purge(name: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/event/${name}/purge`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('event.purgeEvent'))
      return false
    }
  }

  async function fetchResults(name: string): Promise<boolean> {
    error.value = ''
    try {
      const { data } = await api.get<{ items: EventResultRow[] }>(
        `/event/${name}/results`,
      )
      results.value = data.items ?? []
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('event.loadResults'))
      return false
    }
  }

  return {
    items,
    total,
    page,
    perPage,
    loading,
    error,
    current,
    currentLoading,
    results,
    list,
    get,
    create,
    update,
    softDelete,
    restore,
    purge,
    fetchResults,
  }
})
