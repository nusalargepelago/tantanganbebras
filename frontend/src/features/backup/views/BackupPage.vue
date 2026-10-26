<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Alert, Button, ErrorMessage, dialog, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'

import { useBackupStore, type RestoreResult } from '../store'

const store = useBackupStore()
const { t } = useI18n()

const file = ref<File | null>(null)
const result = ref<RestoreResult | null>(null)
const fileError = ref('')

const canRestore = computed(() => !!file.value && !store.restoring)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  file.value = input.files?.[0] ?? null
  result.value = null
  fileError.value = ''
}

function pickFile() {
  ;(document.getElementById('backup-file') as HTMLInputElement)?.click()
}

function onRestore() {
  const picked = file.value
  if (!picked) return
  dialog.danger({
    title: t('backup.confirmTitle'),
    message: t('backup.confirmMessage', { name: picked.name }),
    onConfirm: async () => {
      const data = await store.restore(picked)
      if (!data) {
        fileError.value = store.error || t('backup.restoreFailed')
        return
      }
      result.value = data
      file.value = null
      toast.success(t('backup.restored', { tables: data.tables, rows: data.rows }))
    },
  })
}
</script>

<template>
  <AppPageHeader />

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <div class="space-y-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('backup.exportTitle') }}</h2>
      <p class="text-p-sm text-ink-gray-5">{{ t('backup.exportDesc') }}</p>
      <div>
        <Button
          variant="outline"
          theme="gray"
          icon-left="lucide-download"
          :label="t('backup.exportBtn')"
          href="/api/v1/backup/export"
        />
      </div>
    </div>

    <div class="space-y-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('backup.importTitle') }}</h2>
      <Alert
        theme="red"
        icon="lucide-alert-triangle"
        :title="t('backup.importWarn')"
      />
      <p class="text-p-sm text-ink-gray-5">{{ t('backup.importDesc') }}</p>

      <div class="flex items-center gap-2">
        <input
          id="backup-file"
          type="file"
          accept=".sql,.txt"
          class="hidden"
          @change="onFileChange"
        />
        <Button
          variant="outline"
          theme="gray"
          icon-left="lucide-paperclip"
          :label="t('backup.chooseFile')"
          @click="pickFile"
        />
        <span class="truncate text-p-sm text-ink-gray-5">
          {{ file?.name || t('backup.noFile') }}
        </span>
      </div>

      <div>
        <Button
          variant="solid"
          theme="red"
          icon-left="lucide-upload"
          :label="t('backup.restoreBtn')"
          :loading="store.restoring"
          :disabled="!canRestore"
          @click="onRestore"
        />
      </div>

      <ErrorMessage v-if="fileError" :message="fileError" />
    </div>

    <Alert
      v-if="result"
      theme="green"
      icon="lucide-check-circle"
      :title="t('backup.restoredTitle', { tables: result.tables, rows: result.rows })"
    />
  </div>
</template>
