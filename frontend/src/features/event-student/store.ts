import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface CandidateEvent {
  name: string
  eventName: string
  category: string
  timeLimit: number
  eventDeadline: string
  published: boolean
  description?: string | null
  questionCount: number
  categoryMatch: boolean
  alreadyAttempted: boolean
  attemptName: string | null
  attemptScore: number | null
  attemptCompleted: boolean
}

export interface EventAttempt {
  name: string
  studentId: string
  eventId: string
  score?: number | null
  timeLimit?: number | null
  startedAt?: string | null
  finishedAt?: string | null
}

export interface EventStartPayload {
  event: Record<string, any>
  eventStudent: EventAttempt
  questions: { eventQuestionId: string; question: Record<string, any> | null }[]
  savedAnswers: { eventQuestionId: string; answer: string }[]
}

export const useEventStudentStore = defineStore('eventStudent', () => {
  const candidates = ref<CandidateEvent[]>([])
  const active = ref<EventStartPayload | null>(null)
  const result = ref<EventAttempt | null>(null)
  const loading = ref(false)
  const resultLoading = ref(false)
  const error = ref('')

  async function listCandidates(): Promise<boolean> {
    error.value = ''
    loading.value = true
    try {
      const { data } = await api.get<{ items: CandidateEvent[] }>('/student/event')
      candidates.value = data.items ?? []
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('eventStudent.loadEvents'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function make(
    eventName: string,
    test = false,
  ): Promise<EventAttempt | null> {
    error.value = ''
    try {
      const { data } = await api.post<EventAttempt>(
        `/student/event/make/${eventName}`,
        null,
        { params: test ? { test: 1 } : undefined },
      )
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('eventStudent.startFailed'))
      return null
    }
  }

  async function start(attemptName: string): Promise<EventStartPayload | null> {
    error.value = ''
    active.value = null
    try {
      const { data } = await api.get<EventStartPayload>(
        `/student/event/start/${attemptName}`,
      )
      active.value = data
      return data
    } catch (e: any) {
      if (e?.response?.status !== 404) {
        error.value = getErrorMessage(e, i18n.global.t('eventStudent.loadEvent'))
      }
      return null
    }
  }

  async function saveAnswer(
    attemptName: string,
    eventQuestionId: string,
    answer: string,
  ): Promise<void> {
    try {
      await api.post('/student/event/answer-temp', {
        eventStudentName: attemptName,
        eventQuestionId,
        answer,
      })
    } catch {
      // Autosave is fire-and-forget.
    }
  }

  async function submit(
    attemptName: string,
    answers: { eventQuestionId: string; answer: string }[],
  ): Promise<boolean> {
    error.value = ''
    try {
      await api.post('/student/event/store', {
        eventStudentName: attemptName,
        answers,
      })
      return true
    } catch (e: any) {
      if (
        e?.response?.status === 409 &&
        e?.response?.data?.message === 'attempt_already_submitted'
      ) {
        return true
      }
      error.value = getErrorMessage(e, 'Failed to submit the event')
      return false
    }
  }

  async function fetchResult(attemptName: string): Promise<EventAttempt | null> {
    error.value = ''
    resultLoading.value = true
    result.value = null
    try {
      const { data } = await api.get<EventAttempt>(
        `/student/event/${attemptName}`,
      )
      result.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('eventStudent.loadResult'))
      return null
    } finally {
      resultLoading.value = false
    }
  }

  return {
    candidates,
    active,
    result,
    loading,
    resultLoading,
    error,
    listCandidates,
    make,
    start,
    saveAnswer,
    submit,
    fetchResult,
  }
})
