import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export type QuestionType = 'Multiple Choice' | 'Essay'
export type Difficulty = 'Easy' | 'Medium' | 'Hard'
export type QuestionStatus = 'Active' | 'Inactive'
export type Category = 'cub' | 'scout' | 'rover'
export type CorrectAnswer = 'a' | 'b' | 'c' | 'd'

export interface Question {
  name: string
  questionCode: string
  question: string
  description?: string | null
  questionType: QuestionType
  optionA?: string | null
  optionB?: string | null
  optionC?: string | null
  optionD?: string | null
  referenceAnswer?: string | null
  correctAnswer?: CorrectAnswer | null
  category: Category
  difficultyLevel: Difficulty
  status: QuestionStatus
  creatorId?: string | null
  topicId?: string | null
  disabled: boolean
  disabledAt?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}

export interface QuestionPayload {
  questionCode?: string
  question: string
  description?: string | null
  questionType: QuestionType
  optionA?: string | null
  optionB?: string | null
  optionC?: string | null
  optionD?: string | null
  referenceAnswer?: string | null
  correctAnswer?: CorrectAnswer | null
  category: Category
  difficultyLevel: Difficulty
  status: QuestionStatus
  topicId?: string | null
}

export interface QuestionQuery {
  q?: string
  category?: string
  status?: string
  difficultyLevel?: string
  topicId?: string
  includeDisabled?: boolean
  page?: number
  perPage?: number
}

export interface QuestionPage {
  items: Question[]
  total: number
  page: number
  perPage: number
}

export interface Topic {
  name: string
  title: string
  category: Category
  idx: number
  creatorId?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}

export interface TopicPayload {
  title: string
  category: Category
  idx?: number
}

export interface OptionList {
  category: string[]
  difficultyLevel: string[]
  questionType: string[]
  option: string[]
  status: string[]
}

export const useQuestionStore = defineStore('question', () => {
  const items = ref<Question[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const loading = ref(false)
  const error = ref('')

  const current = ref<Question | null>(null)
  const currentLoading = ref(false)

  const topics = ref<Topic[]>([])
  const topicsLoading = ref(false)
  const optionList = ref<OptionList | null>(null)

  async function list(query: QuestionQuery = {}): Promise<boolean> {
    error.value = ''
    loading.value = true
    try {
      const params: Record<string, string | number | boolean> = {
        page: query.page ?? page.value,
        per_page: query.perPage ?? perPage.value,
      }
      if (query.q) params.q = query.q
      if (query.category) params.category = query.category
      if (query.status) params.status = query.status
      if (query.difficultyLevel) params.difficultyLevel = query.difficultyLevel
      if (query.topicId) params.topicId = query.topicId
      if (query.includeDisabled) params.includeDisabled = 'true'
      const { data } = await api.get<QuestionPage>('/question', { params })
      items.value = data.items ?? []
      total.value = data.total
      page.value = data.page
      perPage.value = data.perPage
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.loadQuestions'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function get(name: string): Promise<Question | null> {
    error.value = ''
    currentLoading.value = true
    current.value = null
    try {
      const { data } = await api.get<Question>(`/question/${name}`)
      current.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.loadFailed'))
      return null
    } finally {
      currentLoading.value = false
    }
  }

  async function create(payload: QuestionPayload): Promise<Question | null> {
    error.value = ''
    try {
      const { data } = await api.post<Question>('/question', payload)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.createQuestion'))
      return null
    }
  }

  async function update(name: string, payload: Partial<QuestionPayload>): Promise<Question | null> {
    error.value = ''
    try {
      const { data } = await api.patch<Question>(`/question/${name}`, payload)
      // Ignore late responses for a question the editor already navigated away from.
      if (!current.value || current.value.name === name) current.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.saveFailed'))
      return null
    }
  }

  async function softDelete(name: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/question/${name}`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.deleteFailed'))
      return false
    }
  }

  async function restore(name: string): Promise<boolean> {
    error.value = ''
    try {
      await api.post(`/question/${name}/restore`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.restoreFailed'))
      return false
    }
  }

  async function purge(name: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/question/${name}/purge`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.purgeFailed'))
      return false
    }
  }

  async function listTopics(): Promise<boolean> {
    topicsLoading.value = true
    try {
      const { data } = await api.get<{ items: Topic[] }>('/topic', {
        params: { per_page: 200 },
      })
      topics.value = data.items ?? []
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.loadTopics'))
      return false
    } finally {
      topicsLoading.value = false
    }
  }

  async function createTopic(payload: TopicPayload): Promise<Topic | null> {
    error.value = ''
    try {
      const { data } = await api.post<Topic>('/topic', payload)
      topics.value.push(data)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.createTopic'))
      return null
    }
  }

  async function updateTopic(name: string, payload: Partial<TopicPayload>): Promise<Topic | null> {
    error.value = ''
    try {
      const { data } = await api.patch<Topic>(`/topic/${name}`, payload)
      const i = topics.value.findIndex((t) => t.name === name)
      if (i !== -1) topics.value[i] = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.updateTopic'))
      return null
    }
  }

  async function deleteTopic(name: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/topic/${name}`)
      topics.value = topics.value.filter((t) => t.name !== name)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.deleteTopic'))
      return false
    }
  }

  async function reorderTopics(items: { name: string; idx: number }[]): Promise<boolean> {
    error.value = ''
    try {
      await api.post('/topic/reorder', { items })
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('question.reorderTopics'))
      return false
    }
  }

  async function fetchOptionList(): Promise<void> {
    if (optionList.value) return
    try {
      const { data } = await api.get<OptionList>('/question/option-list')
      optionList.value = data
    } catch {
      // Non-fatal: filters fall back to hardcoded enums in the view.
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
    topics,
    topicsLoading,
    optionList,
    list,
    get,
    create,
    update,
    softDelete,
    restore,
    purge,
    listTopics,
    createTopic,
    updateTopic,
    deleteTopic,
    reorderTopics,
    fetchOptionList,
  }
})
