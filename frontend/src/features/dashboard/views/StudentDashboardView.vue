<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useAuthStore } from '@/features/auth/store'
import { categoryLabel } from '@/shared/labels'
import { useDashboardStore } from '../store'

const router = useRouter()
const auth = useAuthStore()
const store = useDashboardStore()
const { t } = useI18n()

const firstName = computed(() => auth.user?.fullName || auth.student?.firstName || '')

const stats = computed(() => {
  const d = store.student
  if (!d) return []
  return [
    { label: t('dash.student.totalPractice'), value: d.totalPractice, route: 'PracticeList' },
    { label: t('dash.student.totalChallenges'), value: d.totalChallenge, route: 'EventStudentList' },
  ]
})

onMounted(store.fetchStudent)
</script>

<template>
  <AppPageHeader :title="t('nav.dashboard')">
    <template #actions>
      <Button
        variant="solid"
        icon-left="lucide-play"
        :label="t('dash.student.startPractice')"
        :route="{ name: 'PracticeList' }"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-play"
        :label="t('dash.student.startPractice')"
        :route="{ name: 'PracticeList' }"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ErrorMessage v-if="store.error" :message="store.error" />

    <Skeleton v-if="store.loading" class="h-40" />

    <template v-else-if="store.student">
      <div class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <p class="text-p-sm text-ink-gray-5">{{ t('dash.student.welcome') }}</p>
        <h1 class="text-2xl-semibold text-ink-gray-8">{{ firstName }}</h1>
        <p class="text-p-sm text-ink-gray-5">
          {{ t('dash.student.category') }}
          <Badge
            :label="categoryLabel(store.student.category)"
            variant="subtle"
            class="ml-1"
          />
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-2" data-tour="student-dashboard-stats">
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="cursor-pointer rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 transition-colors hover:border-outline-gray-3"
          @click="router.push({ name: stat.route })"
        >
          <p class="text-p-sm text-ink-gray-5">{{ stat.label }}</p>
          <p class="text-4xl-semibold text-ink-gray-8">{{ stat.value }}</p>
        </div>
      </div>

      <div class="flex flex-wrap gap-2" data-tour="student-dashboard-actions">
        <Button variant="solid" theme="gray" icon-left="lucide-play" :label="t('dash.student.practice')" :route="{ name: 'PracticeList' }" />
        <Button variant="outline" theme="gray" icon-left="lucide-calendar" :label="t('dash.student.challenges')" :route="{ name: 'EventStudentList' }" />
      </div>

      <div
        v-if="store.student.lastPractice || store.student.lastEvent"
        class="grid gap-4 md:grid-cols-2"
      >
        <section
          v-if="store.student.lastPractice"
          class="cursor-pointer rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 transition-colors hover:border-outline-gray-3"
          @click="router.push({ name: 'PracticeResult', params: { name: store.student.lastPractice.name } })"
        >
          <p class="text-p-sm text-ink-gray-5">{{ t('dash.student.lastPractice') }}</p>
          <p class="text-base-medium text-ink-gray-8">
            {{
              store.student.lastPractice.finishedAt
                ? t('dash.student.scoreWith', { score: store.student.lastPractice.score ?? 0 })
                : t('dash.student.notSubmitted')
            }}
          </p>
        </section>
        <section
          v-if="store.student.lastEvent"
          class="cursor-pointer rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 transition-colors hover:border-outline-gray-3"
          @click="router.push({ name: 'EventStudentResult', params: { name: store.student.lastEvent.name } })"
        >
          <p class="text-p-sm text-ink-gray-5">{{ t('dash.student.lastChallenge') }}</p>
          <p class="text-base-medium text-ink-gray-8">
            {{
              store.student.lastEvent.finishedAt
                ? t('dash.student.scoreWith', { score: store.student.lastEvent.score ?? 0 })
                : t('dash.student.inProgress')
            }}
          </p>
        </section>
      </div>
    </template>
  </div>
</template>
