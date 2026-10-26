<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import CelebrationOverlay from '@/shared/components/CelebrationOverlay.vue'
import { categoryLabel } from '@/shared/labels'
import { hasRichContent } from '@/shared/richText'
import { sanitizeHtml } from '@/shared/sanitize'

import { usePracticeStore } from '../store'

const route = useRoute()
const store = usePracticeStore()
const { t } = useI18n()

const name = computed(() => route.params.name as string)
const data = computed(() => store.detail)
const practice = computed(() => data.value?.practice ?? null)

const answerMap = computed(() => {
  const map: Record<string, { answer: string; isCorrect: boolean }> = {}
  for (const row of data.value?.answers ?? []) {
    map[row.questionId] = { answer: row.answer, isCorrect: row.isCorrect }
  }
  return map
})

function answerFor(questionId: string) {
  return answerMap.value[questionId]
}

const score = computed(() => practice.value?.score ?? 0)

onMounted(() => store.fetchDetail(name.value))
</script>

<template>
  <AppPageHeader>
    <template v-if="practice" #actions>
      <Button
        variant="outline"
        theme="gray"
        :label="t('practice.backToList')"
        :route="{ name: 'PracticeList' }"
      />
    </template>
    <template v-if="practice" #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-arrow-left"
        :label="t('practice.backToList')"
        :route="{ name: 'PracticeList' }"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <Skeleton v-if="store.detailLoading" class="h-40" />
    <ErrorMessage v-else-if="store.error" :message="store.error" />

    <template v-else-if="data && practice">
      <div class="space-y-1">
        <h1 class="text-2xl-semibold text-ink-gray-8">
          {{ t('route.PracticeList.title') }}
        </h1>
        <p class="text-p-sm text-ink-gray-5">
          {{ t('detail.categoryPrefix') }} {{ categoryLabel(practice.category) }}
          <template v-if="practice.finishedAt">
            {{ t('practice.finishedPrefix') }} {{ new Date(practice.finishedAt).toLocaleString() }}
          </template>
        </p>
      </div>

      <div
        class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 text-center"
        data-tour="student-practice-result"
      >
        <p class="text-p-sm text-ink-gray-5">{{ t('detail.score') }}</p>
        <p class="text-5xl-semibold text-ink-green-7">{{ score }}</p>
      </div>

      <div
        class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
        data-tour="student-practice-answers"
      >
        <h2 class="text-xl-semibold text-ink-gray-8">{{ t('detail.answerDetail') }}</h2>
        <ol class="mt-3 space-y-3">
          <li
            v-for="(ref, i) in data.questions ?? []"
            :key="ref.questionId"
            class="border-b border-outline-gray-1 pb-3 last:border-0 last:pb-0"
          >
            <div class="flex gap-2">
              <span class="text-base-medium text-ink-gray-5">{{ i + 1 }}.</span>
              <div class="min-w-0 flex-1">
                <template v-if="ref.question">
                  <div
                    v-if="hasRichContent(ref.question.description)"
                    class="rich-text text-p-sm text-ink-gray-5"
                    v-html="sanitizeHtml(ref.question.description)"
                  />
                  <div
                    class="rich-text text-p-sm text-ink-gray-8 [&_img]:max-h-48"
                    v-html="sanitizeHtml(ref.question.question)"
                  />
                </template>
                <p v-else class="text-p-sm italic text-ink-gray-4">
                  {{ t('runner.unavailable') }}
                </p>
                <div class="mt-1 flex items-start gap-2">
                  <Badge
                    v-if="answerFor(ref.questionId)?.isCorrect"
                    label="✓"
                    theme="green"
                    variant="subtle"
                  />
                  <Badge v-else label="✗" theme="red" variant="subtle" />
                  <span
                    class="whitespace-pre-wrap text-p-sm"
                    :class="answerFor(ref.questionId)?.answer ? 'text-ink-gray-8' : 'text-ink-gray-4 italic'"
                  >
                    {{ answerFor(ref.questionId)?.answer || t('detail.notAnswered') }}
                  </span>
                </div>
              </div>
            </div>
          </li>
        </ol>
      </div>
    </template>
  </div>

  <CelebrationOverlay v-if="practice && practice.finishedAt" />
</template>
