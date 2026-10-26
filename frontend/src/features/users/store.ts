import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface AdminUser {
  id: string
  email: string
  username: string
  fullName: string
  appRole: string
  roles: string[]
  isActive: boolean
  createdOn?: string | null
}

export interface AdminUserPage {
  items: AdminUser[]
  total: number
  page: number
  perPage: number
}

export interface AdminUserPayload {
  fullName: string
  email?: string
  username?: string
  password?: string
  appRole?: string
}

export const useUsersStore = defineStore('users', () => {
  const items = ref<AdminUser[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const loading = ref(false)
  const error = ref('')
  const current = ref<AdminUser | null>(null)
  const currentLoading = ref(false)

  async function list(query: { q?: string; page?: number; perPage?: number } = {}): Promise<boolean> {
    error.value = ''
    loading.value = true
    try {
      const params: Record<string, string | number> = {
        page: query.page ?? page.value,
        per_page: query.perPage ?? perPage.value,
      }
      if (query.q) params.search = query.q
      const { data } = await api.get<AdminUserPage>('/account/users', { params })
      items.value = data.items ?? []
      total.value = data.total
      page.value = data.page
      perPage.value = data.perPage
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('users.loadUsers'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function get(id: string): Promise<AdminUser | null> {
    error.value = ''
    currentLoading.value = true
    current.value = null
    try {
      const { data } = await api.get<AdminUser>(`/account/users/${id}`)
      current.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('users.loadUser'))
      return null
    } finally {
      currentLoading.value = false
    }
  }

  async function create(payload: AdminUserPayload): Promise<AdminUser | null> {
    error.value = ''
    try {
      const { data } = await api.post<AdminUser>('/account/users', payload)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('users.createUser'))
      return null
    }
  }

  async function update(id: string, payload: Partial<AdminUserPayload>): Promise<AdminUser | null> {
    error.value = ''
    try {
      const { data } = await api.patch<AdminUser>(`/account/users/${id}`, payload)
      current.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('users.updateUser'))
      return null
    }
  }

  async function remove(id: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/account/users/${id}`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('users.deleteFailed'))
      return false
    }
  }

  return { items, total, page, perPage, loading, error, current, currentLoading, list, get, create, update, remove }
})
