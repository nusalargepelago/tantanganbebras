import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface Practice {
  name: string
  studentId: string
  studentName?: string | null
  studentEmail?: string | null
  studentSchool?: string | null
  category: string
  score?: number | null
  timeLimit?: number | null
  startedAt?: string | null
  finishedAt?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}

export interface PracticeQuestionRef {
  questionId: string
  question: Record<string, any> | null
}

export interface PracticeStartPayload {
  practice: Practice
  questions: PracticeQuestionRef[]
  savedAnswers: { questionId: string; answer: string }[]
}

export interface PracticeAnswerRow {
  questionId: string
  answer: string
  isCorrect: boolean
}

export interface PracticeShuffleRow {
  questionId: string
  question: Record<string, any> | null
  originalIdx?: number
  shuffledIdx?: number
}

export interface PracticeDetailPayload {
  practice: Practice
  questions?: PracticeQuestionRef[]
  answers?: PracticeAnswerRow[]
  beforeShuffle: PracticeShuffleRow[]
  afterShuffle?: PracticeShuffleRow[]
  student?: Record<string, any> | null
}

export interface PracticePage {
  items: Practice[]
  total: number
  page: number
  perPage: number
}

export interface PracticeSettings {
  minQuestions: number
}

export const usePracticeStore = defineStore('practice', () => {
  const mine = ref<Practice[]>([])
  const active = ref<PracticeStartPayload | null>(null)
  const detail = ref<PracticeDetailPayload | null>(null)
  const adminItems = ref<Practice[]>([])
  const adminTotal = ref(0)
  const adminPage = ref(1)
  const adminPerPage = ref(20)
  const loading = ref(false)
  const detailLoading = ref(false)
  const error = ref('')
  const settings = ref<PracticeSettings | null>(null)
  const settingsLoading = ref(false)
  const settingsError = ref('')

  async function fetchSettings(): Promise<boolean> {
    settingsError.value = ''
    settingsLoading.value = true
    try {
      const { data } = await api.get<PracticeSettings>('/practice/settings')
      settings.value = data
      return true
    } catch (e: any) {
      settingsError.value = getErrorMessage(e, i18n.global.t('practice.loadSettings'))
      return false
    } finally {
      settingsLoading.value = false
    }
  }

  async function updateSettings(minQuestions: number): Promise<boolean> {
    settingsError.value = ''
    try {
      const { data } = await api.put<PracticeSettings>('/practice/settings', { minQuestions })
      settings.value = data
      return true
    } catch (e: any) {
      settingsError.value = getErrorMessage(e, i18n.global.t('practice.settingsFailed'))
      return false
    }
  }

  async function listMine(): Promise<boolean> {
    error.value = ''
    loading.value = true
    try {
      const { data } = await api.get<{ items: Practice[] }>('/student/practice/mine')
      mine.value = data.items ?? []
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('practice.loadPractices'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function create(test = false, category?: string): Promise<Practice | null> {
    error.value = ''
    try {
      const { data } = await api.post<Practice>('/student/practice/create', null, {
        params: {
          ...(test ? { test: 1 } : {}),
          ...(category ? { category } : {}),
        },
      })
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('practice.startFailed'))
      return null
    }
  }

  async function start(): Promise<PracticeStartPayload | null> {
    error.value = ''
    active.value = null
    try {
      const { data } = await api.get<PracticeStartPayload>('/student/practice/start')
      active.value = data
      return data
    } catch (e: any) {
      if (e?.response?.status !== 404) {
        error.value = getErrorMessage(e, i18n.global.t('practice.loadPractice'))
      }
      return null
    }
  }

  async function saveAnswer(practiceName: string, questionId: string, answer: string): Promise<void> {
    try {
      await api.post('/student/practice/answer-temp', {
        practiceName,
        questionId,
        answer,
      })
    } catch {
      // Autosave is fire-and-forget; the submit path surfaces real errors.
    }
  }

  async function submit(
    practiceName: string,
    answers: { questionId: string; answer: string }[],
  ): Promise<boolean> {
    error.value = ''
    try {
      await api.post('/student/practice/store', { practiceName, answers })
      return true
    } catch (e: any) {
      if (
        e?.response?.status === 409 &&
        e?.response?.data?.message === 'practice_already_submitted'
      ) {
        return true
      }
      error.value = getErrorMessage(e, i18n.global.t('practice.submitPractice'))
      return false
    }
  }

  async function fetchDetail(name: string): Promise<PracticeDetailPayload | null> {
    error.value = ''
    detailLoading.value = true
    detail.value = null
    try {
      const { data } = await api.get<PracticeDetailPayload>(`/student/practice/${name}`)
      detail.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('practice.loadPractice'))
      return null
    } finally {
      detailLoading.value = false
    }
  }

  async function fetchAdminDetail(name: string): Promise<PracticeDetailPayload | null> {
    error.value = ''
    detailLoading.value = true
    detail.value = null
    try {
      const { data } = await api.get<PracticeDetailPayload>(`/practice/${name}`)
      detail.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('practice.loadPractice'))
      return null
    } finally {
      detailLoading.value = false
    }
  }

  async function listAdmin(
    query: { category?: string; page?: number; perPage?: number } = {},
  ): Promise<boolean> {
    error.value = ''
    loading.value = true
    try {
      const params: Record<string, string | number> = {
        page: query.page ?? adminPage.value,
        per_page: query.perPage ?? adminPerPage.value,
      }
      if (query.category) params.category = query.category
      const { data } = await api.get<PracticePage>('/practice', { params })
      adminItems.value = data.items ?? []
      adminTotal.value = data.total
      adminPage.value = data.page
      adminPerPage.value = data.perPage
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('practice.loadPractices'))
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    mine,
    active,
    detail,
    adminItems,
    adminTotal,
    adminPage,
    adminPerPage,
    loading,
    detailLoading,
    error,
    settings,
    settingsLoading,
    settingsError,
    fetchSettings,
    updateSettings,
    listMine,
    create,
    start,
    saveAnswer,
    submit,
    fetchDetail,
    fetchAdminDetail,
    listAdmin,
  }
})
