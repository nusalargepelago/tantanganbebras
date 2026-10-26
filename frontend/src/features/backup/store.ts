import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export interface RestoreResult {
  tables: number
  rows: number
}

function stamp(): string {
  const now = new Date()
  const pad = (value: number) => String(value).padStart(2, '0')
  return (
    `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-` +
    `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
  )
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export const useBackupStore = defineStore('backup', () => {
  const error = ref('')
  const restoring = ref(false)

  async function takeSnapshot(): Promise<string | null> {
    try {
      const { data } = await api.get<Blob>('/backup/export', { responseType: 'blob' })
      download(data, `minimals-pre-restore-${stamp()}.sql`)
      return null
    } catch (e: any) {
      return getErrorMessage(e, i18n.global.t('backup.snapshotFailed'))
    }
  }

  async function restore(file: File): Promise<RestoreResult | null> {
    error.value = ''
    restoring.value = true
    try {
      const snapshotError = await takeSnapshot()
      if (snapshotError) {
        error.value = snapshotError
        return null
      }
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post<RestoreResult>('/backup/import', form)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('backup.restoreFailed'))
      return null
    } finally {
      restoring.value = false
    }
  }

  return {
    error,
    restoring,
    restore,
  }
})
