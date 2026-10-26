<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Alert, Button, ErrorMessage, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useStudentStore, type ImportResult } from '../store'

const store = useStudentStore()
const { t } = useI18n()

const file = ref<File | null>(null)
const uploading = ref(false)
const result = ref<ImportResult | null>(null)
const fileError = ref('')

const canUpload = computed(() => !!file.value && !uploading.value)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  file.value = input.files?.[0] ?? null
  result.value = null
  fileError.value = ''
}

async function onUpload() {
  if (!file.value || uploading.value) return
  uploading.value = true
  result.value = null
  fileError.value = ''
  const data = await store.importStudents(file.value)
  uploading.value = false
  if (!data) {
    fileError.value = store.error || t('import.failed')
    return
  }
  result.value = data
  if (data.errors.length === 0) {
    toast.success(
      t('import.toastImported', { inserted: data.inserted, updated: data.updated }),
    )
  }
}

function pickFile() {
  ;(document.getElementById('student-import-file') as HTMLInputElement)?.click()
}
</script>

<template>
  <AppPageHeader :title="t('route.StudentImport.title')" />

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <div class="space-y-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('import.uploadTitle') }}</h2>
      <p class="text-p-sm text-ink-gray-5">
        {{ t('import.uploadDesc1') }}
        <code class="text-p-xs">first_name, last_name, email, username, password, category</code>
        {{ t('import.uploadDesc2') }}
        <code class="text-p-xs">school, city, country, status</code>
        {{ t('import.uploadDesc3') }}
      </p>

      <div class="flex items-center gap-2">
        <input
          id="student-import-file"
          type="file"
          accept=".xlsx"
          class="hidden"
          @change="onFileChange"
        />
        <Button
          variant="outline"
          theme="gray"
          icon-left="lucide-paperclip"
          :label="t('import.chooseFile')"
          @click="pickFile"
        />
        <span class="truncate text-p-sm text-ink-gray-5">
          {{ file?.name || t('import.noFile') }}
        </span>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="solid"
          icon-left="lucide-upload"
          :label="t('import.upload')"
          :loading="uploading"
          :disabled="!canUpload"
          @click="onUpload"
        />
        <Button
          variant="ghost"
          theme="gray"
          icon-left="lucide-download"
          :label="t('import.downloadTemplate')"
          href="/api/v1/student/import-template"
        />
      </div>

      <ErrorMessage v-if="fileError" :message="fileError" />
    </div>

    <template v-if="result">
      <Alert
        v-if="result.errors.length === 0"
        theme="green"
        icon="lucide-check-circle"
        :title="
          t('import.successTitle', { inserted: result.inserted, updated: result.updated })
        "
      />
      <div v-else class="space-y-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <p class="text-base-medium text-ink-gray-8">
          {{
            t('import.summary', {
              inserted: result.inserted,
              updated: result.updated,
              errors: result.errors.length,
            })
          }}
        </p>
        <ul class="space-y-1">
          <li
            v-for="(err, i) in result.errors"
            :key="i"
            class="text-p-sm text-ink-red-6"
          >
            {{ t('import.rowError', { row: err.row, message: err.message }) }}
          </li>
        </ul>
      </div>
    </template>

    <ErrorMessage v-if="store.error && !fileError" :message="store.error" />
  </div>
</template>
