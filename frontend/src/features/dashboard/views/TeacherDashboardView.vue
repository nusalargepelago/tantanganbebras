<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import { Button } from 'frappe-ui'
import { useAuthStore } from '@/features/auth/store'

const auth = useAuthStore()
const { t } = useI18n()

const firstName = computed(() => (auth.user?.fullName ?? '').trim().split(/\s+/)[0] ?? '')
</script>

<template>
  <AppPageHeader :title="t('nav.dashboard')" />
  <div class="p-6">
    <div
      data-tour="teacher-hero"
      class="flex flex-col items-center gap-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 px-6 py-12 text-center"
    >
      <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
        <span class="lucide-presentation size-8" aria-hidden="true" />
      </div>
      <h1 class="text-2xl-semibold text-ink-gray-8">
        {{ t('teacher.welcomeTitle', { name: firstName }) }}
      </h1>
      <p class="max-w-md text-p-base text-ink-gray-5">
        {{ t('teacher.welcomeBody') }}
      </p>
      <div data-tour="teacher-actions" class="flex flex-wrap items-center justify-center gap-2">
        <Button
          variant="solid"
          icon-left="lucide-users"
          :label="t('teacher.manageStudents')"
          :route="{ name: 'StudentList' }"
        />
        <Button
          variant="outline"
          theme="gray"
          icon-left="lucide-clipboard-list"
          :label="t('teacher.viewPractices')"
          :route="{ name: 'PracticeAdminList' }"
        />
      </div>
    </div>
  </div>
</template>
