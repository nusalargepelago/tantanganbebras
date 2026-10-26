import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface Student {
  userId: string
  username: string
  email: string
  firstName: string
  lastName: string
  category: 'cub' | 'scout' | 'rover'
  school?: string | null
  city?: string | null
  country?: string | null
  status: 'Active' | 'Inactive'
  disabled: boolean
  disabledAt?: string | null
  createdAt?: string | null
}

export interface StudentPayload {
  firstName: string
  lastName: string
  email: string
  username: string
  password?: string
  category: string
  school?: string | null
  city?: string | null
  country?: string | null
  status?: string
}

export interface StudentUpdatePayload {
  firstName?: string
  lastName?: string
  email?: string
  username?: string
  password?: string
  category?: string
  school?: string | null
  city?: string | null
  country?: string | null
  status?: string
}

export interface StudentQuery {
  q?: string
  category?: string
  status?: string
  includeDisabled?: boolean
  page?: number
  perPage?: number
}

export interface StudentPage {
  items: Student[]
  total: number
  page: number
  perPage: number
}

export interface ImportResult {
  inserted: number
  updated: number
  errors: { row: number; message: string }[]
}

export const useStudentStore = defineStore('student', () => {
  const items = ref<Student[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const loading = ref(false)
  const error = ref('')
  const current = ref<Student | null>(null)
  const currentLoading = ref(false)

  async function list(query: StudentQuery = {}): Promise<boolean> {
    error.value = ''
    loading.value = true
    try {
      const params: Record<string, string | number> = {
        page: query.page ?? page.value,
        per_page: query.perPage ?? perPage.value,
      }
      if (query.q) params.q = query.q
      if (query.category) params.category = query.category
      if (query.status) params.status = query.status
      if (query.includeDisabled) params.includeDisabled = 'true'
      const { data } = await api.get<StudentPage>('/student', { params })
      items.value = data.items ?? []
      total.value = data.total
      page.value = data.page
      perPage.value = data.perPage
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.loadStudents'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function get(userId: string): Promise<Student | null> {
    error.value = ''
    currentLoading.value = true
    current.value = null
    try {
      const { data } = await api.get<Student>(`/student/${userId}`)
      current.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.loadStudent'))
      return null
    } finally {
      currentLoading.value = false
    }
  }

  async function create(payload: StudentPayload): Promise<Student | null> {
    error.value = ''
    try {
      const { data } = await api.post<Student>('/student', payload)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.createStudent'))
      return null
    }
  }

  async function update(userId: string, payload: StudentUpdatePayload): Promise<Student | null> {
    error.value = ''
    try {
      const { data } = await api.patch<Student>(`/student/${userId}`, payload)
      current.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.updateStudent'))
      return null
    }
  }

  async function softDelete(userId: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/student/${userId}`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.deleteFailed'))
      return false
    }
  }

  async function restore(userId: string): Promise<Student | null> {
    error.value = ''
    try {
      const { data } = await api.post<Student>(`/student/${userId}/restore`)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.restoreFailed'))
      return null
    }
  }

  async function activate(userId: string): Promise<Student | null> {
    error.value = ''
    try {
      const { data } = await api.post<Student>(`/student/${userId}/activate`)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.activateFailed'))
      return null
    }
  }

  async function purge(userId: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/student/${userId}/purge`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.purgeStudent'))
      return false
    }
  }

  async function importStudents(file: File): Promise<ImportResult | null> {
    error.value = ''
    const form = new FormData()
    form.append('file', file)
    try {
      const { data } = await api.post<ImportResult>('/student/import', form)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('student.importStudents'))
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
    current,
    currentLoading,
    list,
    get,
    create,
    update,
    softDelete,
    restore,
    activate,
    purge,
    importStudents,
  }
})
