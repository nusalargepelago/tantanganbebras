import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface AuthUser {
  id: string
  email: string
  username: string
  fullName: string
  appRole: string | null
  roles: string[]
  isActive: boolean
  createdOn: string | null
}

export interface AuthStudent {
  userId: string
  username: string
  email: string
  firstName: string
  lastName: string
  category: string
  school?: string | null
  city?: string | null
  country?: string | null
  status: string
  disabled: boolean
}

interface StudentSession {
  user: { id: string; email: string; username: string; firstName: string; lastName: string; isActive: boolean }
  student: AuthStudent | null
}

function studentUserToAuthUser(u: StudentSession['user']): AuthUser {
  return {
    id: u.id,
    email: u.email,
    username: u.username,
    fullName: `${u.firstName} ${u.lastName}`.trim(),
    appRole: null,
    roles: [],
    isActive: u.isActive,
    createdOn: null,
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const student = ref<AuthStudent | null>(null)
  const checked = ref(false)
  const error = ref('')
  const registrationMode = ref<'open' | 'closed' | null>(null)

  const isStudent = computed(() => !!student.value)
  const isAdmin = computed(() => user.value?.appRole === 'admin')
  // Mirrors the backend require_staff gate: admin, or an account without a student row.
  const isStaff = computed(() => !!user.value && (!student.value || isAdmin.value))

  async function syncStudentSession() {
    try {
      const { data: session } = await api.get('/student/auth/me')
      student.value = session.student
      // The student payload carries no appRole; never demote an existing staff identity.
      if (session.student && !user.value) {
        user.value = studentUserToAuthUser(session.user)
      }
    } catch {
      student.value = null
    }
  }

  async function login(identifier: string, password: string): Promise<boolean> {
    error.value = ''
    try {
      const { data } = await api.post('/auth/login', { identifier, password })
      user.value = data
      student.value = null
      checked.value = true
      await syncStudentSession()
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('auth.errors.loginFailed'))
      return false
    }
  }

  async function register(payload: {
    fullName: string
    username: string
    email: string
    password: string
  }): Promise<boolean> {
    error.value = ''
    try {
      const { data } = await api.post('/auth/register', payload)
      user.value = data
      student.value = null
      checked.value = true
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('auth.errors.registrationFailed'))
      return false
    }
  }

  async function studentLogin(username: string, password: string): Promise<boolean> {
    error.value = ''
    try {
      const { data } = await api.post<StudentSession>('/student/auth/login', { username, password })
      student.value = data.student
      user.value = data.student ? studentUserToAuthUser(data.user) : null
      checked.value = true
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('auth.errors.loginFailed'))
      return false
    }
  }

  async function studentRegister(payload: {
    firstName: string
    lastName: string
    email: string
    username: string
    password: string
    category: string
    school?: string
    city?: string
    country?: string
  }): Promise<boolean> {
    error.value = ''
    try {
      const { data } = await api.post<StudentSession>('/student/auth/register', payload)
      student.value = data.student
      user.value = data.student ? studentUserToAuthUser(data.user) : null
      checked.value = true
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('auth.errors.registrationFailed'))
      return false
    }
  }

  async function studentLogout() {
    try {
      await api.post('/student/auth/logout')
    } catch {
      // Local session is cleared in finally even if the server call fails.
    } finally {
      user.value = null
      student.value = null
      error.value = ''
    }
  }

  async function fetchMe() {
    try {
      const { data: me } = await api.get('/auth/me')
      user.value = me
      await syncStudentSession()
    } catch {
      user.value = null
      student.value = null
    } finally {
      checked.value = true
    }
  }

  async function fetchRegistrationMode() {
    if (registrationMode.value !== null) return
    try {
      const { data } = await api.get('/auth/registration')
      registrationMode.value = data.mode === 'closed' ? 'closed' : 'open'
    } catch {
      // Fail open — matches the backend default; a blocked attempt still 403s.
      registrationMode.value = 'open'
    }
  }

  async function logout() {
    const wasStudent = !!student.value
    try {
      await api.post(wasStudent ? '/student/auth/logout' : '/auth/logout')
    } catch {
      // Local session is cleared in finally even if the server call fails.
    } finally {
      user.value = null
      student.value = null
      error.value = ''
    }
  }

  return {
    user,
    student,
    checked,
    error,
    registrationMode,
    isStudent,
    isStaff,
    isAdmin,
    login,
    register,
    studentLogin,
    studentRegister,
    studentLogout,
    fetchMe,
    fetchRegistrationMode,
    logout,
  }
})
