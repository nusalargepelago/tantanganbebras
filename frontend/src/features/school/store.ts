import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'
import { invalidateMasters } from '@/shared/masters'

export interface School {
  id: string
  name: string
  isActive: boolean
  cityId?: string
  city?: { id: string; name: string } | null
}

export const useSchoolStore = defineStore('schools', () => {
  const items = ref<School[]>([])
  const loading = ref(false)
  const error = ref('')
  const saving = ref(false)

  async function list(query: { search?: string } = {}): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const params: Record<string, string> = { includeDisabled: '1' }
      if (query.search) params.q = query.search
      const { data } = await api.get<{ items: School[] }>('/school', { params })
      items.value = data.items ?? []
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('schools.loadFailed'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function create(payload: { name: string; cityId: string }): Promise<School | null> {
    saving.value = true
    error.value = ''
    try {
      const { data } = await api.post<School>('/school', payload)
      items.value = [data, ...items.value]
      invalidateMasters()
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('schools.saveFailed'))
      return null
    } finally {
      saving.value = false
    }
  }

  async function update(
    id: string,
    patch: { name?: string; isActive?: boolean; cityId?: string },
  ): Promise<School | null> {
    saving.value = true
    error.value = ''
    try {
      const { data } = await api.patch<School>(`/school/${id}`, patch)
      items.value = items.value.map((s) => (s.id === id ? data : s))
      invalidateMasters()
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('schools.saveFailed'))
      return null
    } finally {
      saving.value = false
    }
  }

  return { items, loading, error, saving, list, create, update }
})
