import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface SetupStatus {
  setupRequired: boolean
  reason: 'no_schema' | 'no_users' | null
  activeEngine: string
  activeUrl: string
}

export interface DbConfig {
  engine: string
  host?: string
  port?: number | string
  database?: string
  username?: string
  password?: string
  path?: string
}

export interface SetupAdmin {
  email: string
  password: string
  fullName: string
  username?: string
}

export interface SetupBrand {
  name: string
  tagline: string
  description: string
  siteUrl?: string
}

export interface SetupResult {
  adminId: string
  email: string
  restartRequired: boolean
}

export const useSetupStore = defineStore('setup', () => {
  const status = ref<SetupStatus | null>(null)
  const error = ref('')
  const statusFailed = ref(false)

  async function fetchStatus(): Promise<void> {
    try {
      const { data } = await api.get('/setup/status')
      status.value = data
      statusFailed.value = false
    } catch {
      // Fail-open: keep null so the guard treats setup as
      // satisfied, but stop refetching on every navigation.
      statusFailed.value = true
    }
  }

  async function testDb(cfg: DbConfig): Promise<string | null> {
    error.value = ''
    try {
      const { data } = await api.post('/setup/db-test', cfg)
      return data.url as string
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('setup.connectionFailed'))
      return null
    }
  }

  async function run(
    cfg: DbConfig,
    brand: SetupBrand,
    admin: SetupAdmin,
    lang: string,
  ): Promise<SetupResult | null> {
    error.value = ''
    try {
      const { data } = await api.post('/setup', { db: cfg, brand, admin, lang })
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('setup.setupFailed'))
      return null
    }
  }

  function markComplete(): void {
    status.value = status.value
      ? { ...status.value, setupRequired: false, reason: null }
      : { setupRequired: false, reason: null, activeEngine: '', activeUrl: '' }
  }

  return { status, error, statusFailed, fetchStatus, testDb, run, markComplete }
})
