import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface AdminDashboardCounts {
  questionCub: number
  questionScout: number
  questionRover: number
  eventActive: number
  studentActive: number
  studentInactive: number
  eventStudentToday: number
}

export interface AdminDashboardPayload {
  counts: AdminDashboardCounts
  recentEvents: Record<string, any>[]
  recentStudents: Record<string, any>[]
}

export interface StudentDashboardPayload {
  category: string
  totalPractice: number
  totalChallenge: number
  lastPractice: Record<string, any> | null
  lastEvent: Record<string, any> | null
}

export interface SchoolCount {
  school: string
  count: number
}

export interface YearCount {
  year: number
  count: number
}

export interface CategoryCount {
  category: string
  count: number
}

export interface AdminDashboardStats {
  totals: { students: number; schools: number }
  schools: SchoolCount[]
  registrations: YearCount[]
  categories: CategoryCount[]
}

export const useDashboardStore = defineStore('dashboard', () => {
  const admin = ref<AdminDashboardPayload | null>(null)
  const student = ref<StudentDashboardPayload | null>(null)
  const stats = ref<AdminDashboardStats | null>(null)
  const loading = ref(false)
  const statsLoading = ref(false)
  const error = ref('')
  const statsError = ref('')

  async function fetchStats(): Promise<boolean> {
    statsError.value = ''
    statsLoading.value = true
    stats.value = null
    try {
      const { data } = await api.get<AdminDashboardStats>('/dashboard/stats')
      stats.value = data
      return true
    } catch (e: any) {
      statsError.value = getErrorMessage(e, i18n.global.t('dash.loadStatistics'))
      return false
    } finally {
      statsLoading.value = false
    }
  }

  async function fetchAdmin(): Promise<boolean> {
    error.value = ''
    loading.value = true
    admin.value = null
    try {
      const { data } = await api.get<AdminDashboardPayload>('/dashboard')
      admin.value = data
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('dash.loadDashboard'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchStudent(): Promise<boolean> {
    error.value = ''
    loading.value = true
    student.value = null
    try {
      const { data } = await api.get<StudentDashboardPayload>('/student/dashboard')
      student.value = data
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('dash.loadDashboard'))
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    admin,
    student,
    stats,
    loading,
    statsLoading,
    error,
    statsError,
    fetchAdmin,
    fetchStudent,
    fetchStats,
  }
})
