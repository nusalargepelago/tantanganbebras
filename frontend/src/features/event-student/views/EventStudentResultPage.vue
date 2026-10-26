<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, ErrorMessage, Skeleton } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import CelebrationOverlay from '@/shared/components/CelebrationOverlay.vue'

import { useAuthStore } from '@/features/auth/store'
import { useEventStudentStore } from '../store'

const route = useRoute()
const store = useEventStudentStore()
const auth = useAuthStore()
const { t } = useI18n()

const attemptName = computed(() => route.params.name as string)
const attempt = computed(() => store.result)

const backToListRoute = computed(() =>
  auth.isAdmin ? { name: 'EventList' } : { name: 'EventStudentList' },
)
const dashboardRoute = computed(() =>
  auth.isAdmin ? { name: 'AdminDashboard' } : { name: 'Dashboard' },
)

onMounted(() => store.fetchResult(attemptName.value))
</script>

<template>
  <AppPageHeader>
    <template v-if="attempt" #actions>
      <Button
        variant="solid"
        theme="gray"
        :label="t('eventStudent.backToList')"
        :route="backToListRoute"
      />
      <Button
        variant="outline"
        theme="gray"
        :label="t('nav.dashboard')"
        :route="dashboardRoute"
      />
    </template>
    <template v-if="attempt" #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-arrow-left"
        :label="t('eventStudent.backToList')"
        :route="backToListRoute"
      />
      <Button
        variant="ghost"
        icon="lucide-house"
        :label="t('nav.dashboard')"
        :route="dashboardRoute"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <Skeleton v-if="store.resultLoading" class="h-40" />
    <ErrorMessage v-else-if="store.error" :message="store.error" />

    <template v-else-if="attempt">
      <div
        class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6 text-center"
        data-tour="student-event-result-score"
      >
        <p class="text-p-sm text-ink-gray-5">{{ t('eventStudent.yourScore') }}</p>
        <p class="text-5xl-semibold text-ink-green-7">{{ attempt.score ?? 0 }}</p>
        <p class="mt-2 text-p-sm text-ink-gray-5">
          {{ t('detail.durationPrefix') }}
          {{
            attempt.timeLimit != null
              ? t('eventStudent.secondsShort', { n: attempt.timeLimit })
              : '—'
          }}
        </p>
        <p v-if="attempt.finishedAt" class="text-p-xs text-ink-gray-4">
          {{ t('eventStudent.submittedAt', { date: new Date(attempt.finishedAt).toLocaleString() }) }}
        </p>
      </div>
    </template>
  </div>

  <CelebrationOverlay v-if="attempt && attempt.finishedAt" />
</template>
