import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'
import { setBrandLogo } from '@/shared/brand'

export const useBrandStore = defineStore('brand', () => {
  const uploading = ref(false)
  const removing = ref(false)
  const error = ref('')

  const busy = computed(() => uploading.value || removing.value)

  async function uploadLogo(file: File): Promise<boolean> {
    error.value = ''
    uploading.value = true
    let url = ''
    try {
      const body = new FormData()
      body.append('file', file)
      const { data } = await api.post('/uploads', body)
      url = typeof data?.url === 'string' ? data.url : ''
      if (!url) throw new Error('upload_failed')
      await api.put('/brand/logo', { logoUrl: url })
      setBrandLogo(url)
      return true
    } catch (e: any) {
      if (url) {
        const name = url.split('/').pop()
        if (name) await api.delete(`/uploads/${name}`).catch(() => {})
      }
      error.value = getErrorMessage(
        e,
        i18n.global.t('settings.brand.updateFailed'),
      )
      return false
    } finally {
      uploading.value = false
    }
  }

  async function removeLogo(): Promise<boolean> {
    error.value = ''
    removing.value = true
    try {
      await api.put('/brand/logo', { logoUrl: '' })
      setBrandLogo('')
      return true
    } catch (e: any) {
      error.value = getErrorMessage(
        e,
        i18n.global.t('settings.brand.removeFailed'),
      )
      return false
    } finally {
      removing.value = false
    }
  }

  return { uploading, removing, busy, error, uploadLogo, removeLogo }
})
