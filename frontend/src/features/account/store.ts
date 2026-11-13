import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface AdminUser {
  id: string
  email: string
  username: string
  fullName: string
  appRole: string | null
  roles: string[]
  isActive: boolean
  createdOn: string | null
}

export interface AccountRole {
  id: string
  name: string
}

export interface UserPage {
  items: AdminUser[]
  total: number
  page: number
  perPage: number
}

export interface UserQuery {
  search?: string
  page?: number
  perPage?: number
}

export interface UserUpdatePayload {
  fullName?: string
  appRole?: string
  isActive?: boolean
  roleNames?: string[]
}

export interface UserCreatePayload {
  email: string
  username: string
  password: string
  fullName: string
  appRole: string
  roleNames: string[]
}

export const useAccountStore = defineStore('account', () => {
  const items = ref<AdminUser[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const loading = ref(false)
  const error = ref('')
  const roles = ref<AccountRole[]>([])
  const rolesLoaded = ref(false)

  async function fetchUserTotal(): Promise<number | null> {
    try {
      const { data } = await api.get<UserPage>('/account/users', {
        params: { page: 1, per_page: 1 },
      })
      return data.total ?? 0
    } catch {
      return null
    }
  }

  async function fetchUsers(query: UserQuery = {}): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const params: Record<string, string | number> = {
        page: query.page ?? page.value,
        per_page: query.perPage ?? perPage.value,
      }
      if (query.search) params.search = query.search
      const { data } = await api.get<UserPage>('/account/users', { params })
      items.value = data.items ?? []
      total.value = data.total ?? 0
      page.value = data.page ?? 1
      perPage.value = data.perPage ?? 20
      return true
    } catch (e: any) {
      error.value = getErrorMessage(
        e,
        i18n.global.t('account.errors.loadUsersFailed'),
      )
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchRoles(): Promise<void> {
    if (rolesLoaded.value) return
    try {
      const { data } = await api.get<{ items: AccountRole[] }>('/account/roles')
      roles.value = data.items ?? []
      rolesLoaded.value = true
    } catch {
      roles.value = []
    }
  }

  async function updateUser(
    id: string,
    payload: UserUpdatePayload,
  ): Promise<AdminUser | null> {
    error.value = ''
    try {
      const { data } = await api.patch<AdminUser>(`/account/users/${id}`, payload)
      const index = items.value.findIndex((user) => user.id === id)
      if (index !== -1) items.value.splice(index, 1, data)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(
        e,
        i18n.global.t('account.errors.updateUserFailed'),
      )
      return null
    }
  }

  async function createUser(
    payload: UserCreatePayload,
  ): Promise<AdminUser | null> {
    error.value = ''
    try {
      const { data } = await api.post<AdminUser>('/account/users', payload)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(
        e,
        i18n.global.t('account.errors.createUserFailed'),
      )
      return null
    }
  }

  return {
    items,
    total,
    page,
    perPage,
    loading,
    error,
    roles,
    fetchUserTotal,
    fetchUsers,
    fetchRoles,
    createUser,
    updateUser,
  }
})
