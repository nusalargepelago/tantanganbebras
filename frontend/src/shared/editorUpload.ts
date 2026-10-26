import type { UploadFunction } from 'frappe-ui/editor'

import { api } from '@/shared/api'

export const uploadMedia: UploadFunction = async (file) => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<{ url: string }>('/uploads', form)
  return { file_url: data.url }
}
