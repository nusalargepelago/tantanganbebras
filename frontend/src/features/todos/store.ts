import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface Todo {
  id: string
  title: string
  description?: string | null
  completed: boolean
  dueDate?: string | null
  creatorId: string
  createdAt?: string | null
  updatedAt?: string | null
}

export interface TodoPayload {
  title: string
  description?: string | null
  completed?: boolean
  dueDate?: string | null
}

export interface TodoPage {
  items: Todo[]
  total: number
  page: number
  perPage: number
}

export const useTodosStore = defineStore('todos', () => {
  const items = ref<Todo[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const loading = ref(false)
  const error = ref('')

  async function list(
    query: { search?: string; completed?: string; page?: number; perPage?: number } = {},
  ): Promise<boolean> {
    error.value = ''
    loading.value = true
    try {
      const params: Record<string, string | number> = {
        page: query.page ?? page.value,
        per_page: query.perPage ?? perPage.value,
      }
      if (query.search) params.search = query.search
      if (query.completed) params.completed = query.completed
      const { data } = await api.get<TodoPage>('/todos', { params })
      items.value = data.items ?? []
      total.value = data.total
      page.value = data.page
      perPage.value = data.perPage
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('todos.loadTodos'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function create(payload: TodoPayload): Promise<Todo | null> {
    error.value = ''
    try {
      const { data } = await api.post<Todo>('/todos', payload)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('todos.createTodo'))
      return null
    }
  }

  async function update(id: string, payload: TodoPayload): Promise<Todo | null> {
    error.value = ''
    try {
      const { data } = await api.patch<Todo>(`/todos/${id}`, payload)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('todos.updateTodo'))
      return null
    }
  }

  async function remove(id: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/todos/${id}`)
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('todos.deleteFailed'))
      return false
    }
  }

  return { items, total, page, perPage, loading, error, list, create, update, remove }
})
