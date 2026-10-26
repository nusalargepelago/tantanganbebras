<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useAuthStore } from '@/features/auth/store'
import { categoryLabel } from '@/shared/labels'
import { useEventStudentStore, type CandidateEvent } from '../store'

const router = useRouter()
const auth = useAuthStore()
const store = useEventStudentStore()
const { t } = useI18n()

const empty = computed(() => !store.loading && store.candidates.length === 0)
const myCategory = computed(() => auth.student?.category ?? '')

const starting = ref<string | null>(null)

function statusBadge(item: CandidateEvent) {
  if (item.alreadyAttempted && item.attemptCompleted)
    return { label: t('list.completed'), theme: 'green' as const }
  if (item.alreadyAttempted) return { label: t('list.inProgress'), theme: 'amber' as const }
  return null
}

async function onStart(item: CandidateEvent) {
  starting.value = item.name
  const attempt = await store.make(item.name)
  starting.value = null
  if (!attempt) {
    toast.error(store.error || t('eventStudent.startFailed'))
    return
  }
  toast.success(t('eventStudent.startedToast'))
  await router.push({ name: 'EventStudentRunner', params: { name: attempt.name } })
}

function onContinue(item: CandidateEvent) {
  if (!item.attemptName) return
  router.push({ name: 'EventStudentRunner', params: { name: item.attemptName } })
}

function onViewResult(item: CandidateEvent) {
  if (!item.attemptName) return
  router.push({ name: 'EventStudentResult', params: { name: item.attemptName } })
}

onMounted(store.listCandidates)
</script>

<template>
  <AppPageHeader>
    <template #leading>
      <span v-if="myCategory" class="text-p-sm text-ink-gray-5">
        {{ t('eventStudent.yourCategory') }} {{ categoryLabel(myCategory) }}
      </span>
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ErrorMessage v-if="store.error" :message="store.error" />

    <div v-if="store.loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Skeleton v-for="i in 6" :key="i" class="h-40" />
    </div>

    <div
      v-else-if="empty"
      class="rounded-6 border border-outline-gray-1 py-12 text-center text-p-sm text-ink-gray-5"
    >
      {{ t('eventStudent.noData') }}
    </div>

    <div
      v-else
      class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      data-tour="student-event-grid"
    >
      <div
        v-for="item in store.candidates"
        :key="item.name"
        class="flex flex-col gap-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-4"
      >
        <div class="flex items-start justify-between gap-2">
          <span class="text-base-medium text-ink-gray-8">{{ item.eventName }}</span>
          <Badge v-if="statusBadge(item)" :label="statusBadge(item)!.label" :theme="statusBadge(item)!.theme" variant="subtle" />
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <Badge
            :label="categoryLabel(item.category)"
            :theme="item.categoryMatch ? 'blue' : 'gray'"
            variant="subtle"
          />
          <Badge
            v-if="!item.categoryMatch"
            :label="t('eventStudent.categoryMismatch')"
            theme="red"
            variant="subtle"
          />
        </div>

        <div class="space-y-1 text-p-xs text-ink-gray-5">
          <p>
            {{
              t('eventStudent.metaLine', {
                timeLimit: item.timeLimit,
                questionCount: item.questionCount,
              })
            }}
          </p>
          <p>
            {{
              t('eventStudent.deadline', {
                date: new Date(item.eventDeadline).toLocaleString(),
              })
            }}
          </p>
          <p v-if="item.description" class="line-clamp-2">{{ item.description }}</p>
        </div>

        <div class="mt-auto flex items-center justify-between gap-2">
          <span
            v-if="item.attemptCompleted && item.attemptScore != null"
            class="text-p-sm-medium text-ink-green-7"
          >
            {{ t('eventStudent.scoreLabel', { score: item.attemptScore }) }}
          </span>
          <span v-else class="text-p-sm text-ink-gray-4">—</span>

          <Button
            v-if="item.attemptCompleted"
            variant="outline"
            theme="gray"
            :label="t('eventStudent.viewResult')"
            data-tour="student-event-result-action"
            @click="onViewResult(item)"
          />
          <Button
            v-else-if="item.alreadyAttempted"
            variant="solid"
            theme="gray"
            :label="t('eventStudent.continue')"
            @click="onContinue(item)"
          />
          <Button
            v-else
            variant="solid"
            :label="t('eventStudent.start')"
            :disabled="!item.categoryMatch"
            :loading="starting === item.name"
            data-tour="student-event-start"
            @click="onStart(item)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
