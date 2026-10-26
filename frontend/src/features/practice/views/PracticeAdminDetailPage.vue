<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { categoryLabel } from '@/shared/labels'
import { hasRichContent } from '@/shared/richText'
import { sanitizeHtml } from '@/shared/sanitize'

import QuestionOptions from '../components/QuestionOptions.vue'
import { usePracticeStore, type PracticeShuffleRow } from '../store'

const route = useRoute()
const router = useRouter()
const store = usePracticeStore()
const { t } = useI18n()

const name = computed(() => route.params.name as string)
const data = computed(() => store.detail)
const practice = computed(() => data.value?.practice ?? null)
const student = computed(() => data.value?.student ?? null)
const testing = ref(false)

async function onTest() {
  if (testing.value) return
  testing.value = true
  const created = await store.create(true, practice.value?.category)
  testing.value = false
  if (!created) {
    toast.error(store.error || t('practice.testFailed'))
    return
  }
  router.push({ name: 'PracticeRunner' })
}

const answerMap = computed(() => {
  const map: Record<string, { answer: string; isCorrect: boolean }> = {}
  for (const row of data.value?.answers ?? []) {
    map[row.questionId] = { answer: row.answer, isCorrect: row.isCorrect }
  }
  return map
})

function shortId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}…` : id
}

const ANSWER_LETTER = /^[a-d]$/i

function answerLetter(questionId: string): string | null {
  const raw = (answerMap.value[questionId]?.answer ?? '').trim()
  return ANSWER_LETTER.test(raw) ? raw.toLowerCase() : null
}

function isMultipleChoice(question: Record<string, any> | null | undefined): boolean {
  return question?.questionType === 'Multiple Choice'
}

function showRawAnswer(row: PracticeShuffleRow): boolean {
  const answer = (answerMap.value[row.questionId]?.answer ?? '').trim()
  if (!answer) return true
  return !isMultipleChoice(row.question) || answerLetter(row.questionId) === null
}

const statusBadge = computed(() => {
  const p = practice.value
  if (!p) return null
  return p.finishedAt
    ? { label: t('practice.scoreBadge', { score: p.score ?? '—' }), theme: 'green' as const }
    : { label: t('list.inProgress'), theme: 'amber' as const }
})

onMounted(() => store.fetchAdminDetail(name.value))
</script>

<template>
  <AppPageHeader>
    <template v-if="practice" #actions>
      <Button
        variant="outline"
        theme="gray"
        icon-left="lucide-play"
        :label="t('practice.testQuiz')"
        :loading="testing"
        @click="onTest"
      />
    </template>
    <template v-if="practice" #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-play"
        :label="t('practice.testQuiz')"
        :loading="testing"
        @click="onTest"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <Skeleton v-if="store.detailLoading" class="h-40" />
    <ErrorMessage v-else-if="store.error" :message="store.error" />

    <template v-else-if="data && practice">
      <div class="space-y-1">
        <h1 class="text-2xl-semibold text-ink-gray-8">
          {{ t('route.PracticeAdminList.title') }}
        </h1>
        <template v-if="student">
          <p class="text-p-sm text-ink-gray-5">
            {{ t('detail.studentLabel') }} {{ student.firstName }} {{ student.lastName }}
            <Badge :label="categoryLabel(student.category)" variant="subtle" class="ml-1" />
            <Badge
              v-if="statusBadge"
              :label="statusBadge.label"
              :theme="statusBadge.theme"
              variant="subtle"
              class="ml-1"
            />
          </p>
          <p
            v-if="student.email || student.school"
            class="text-p-xs text-ink-gray-4"
          >
            {{ [student.email, student.school].filter(Boolean).join(' • ') }}
          </p>
        </template>
        <p v-else class="text-p-sm text-ink-gray-5">
          {{ t('detail.studentLabel') }} {{ shortId(practice.studentId) }}
          <Badge
            v-if="statusBadge"
            :label="statusBadge.label"
            :theme="statusBadge.theme"
            variant="subtle"
            class="ml-1"
          />
        </p>
      </div>

      <section class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5" data-tour="admin-practice-before">
        <h2 class="text-xl-semibold text-ink-gray-8">{{ t('detail.beforeShuffle') }}</h2>
        <ol class="mt-3 space-y-2">
          <li
            v-for="(row, i) in data.beforeShuffle"
            :key="row.questionId"
            class="flex gap-2 text-p-sm"
          >
            <span class="text-ink-gray-5">{{ i + 1 }}.</span>
            <div v-if="row.question" class="min-w-0 flex-1">
              <p class="text-p-xs text-ink-gray-4">{{ row.question.questionCode }}</p>
              <div v-if="hasRichContent(row.question.description)" class="mb-2 space-y-2">
                <div
                  class="rich-text text-p-xs text-ink-gray-5"
                  v-html="sanitizeHtml(row.question.description)"
                />
                <div class="border-t border-outline-gray-2" />
              </div>
              <div
                v-if="hasRichContent(row.question.question)"
                class="rich-text text-ink-gray-8"
                v-html="sanitizeHtml(row.question.question)"
              />
              <QuestionOptions :question="row.question" />
            </div>
            <span v-else class="min-w-0 text-ink-gray-5">(question unavailable)</span>
          </li>
        </ol>
      </section>

      <section class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5" data-tour="admin-practice-after">
        <h2 class="text-xl-semibold text-ink-gray-8">{{ t('detail.afterShuffle') }}</h2>
        <ol class="mt-3 space-y-2">
          <li
            v-for="(row, i) in data.afterShuffle ?? []"
            :key="row.questionId"
            class="flex gap-2 text-p-sm"
          >
            <span class="text-ink-gray-5">{{ i + 1 }}.</span>
            <div v-if="row.question" class="min-w-0 flex-1">
              <p class="text-p-xs text-ink-gray-4">{{ row.question.questionCode }}</p>
              <div v-if="hasRichContent(row.question.description)" class="mb-2 space-y-2">
                <div
                  class="rich-text text-p-xs text-ink-gray-5"
                  v-html="sanitizeHtml(row.question.description)"
                />
                <div class="border-t border-outline-gray-2" />
              </div>
              <div
                v-if="hasRichContent(row.question.question)"
                class="rich-text text-ink-gray-8"
                v-html="sanitizeHtml(row.question.question)"
              />
              <QuestionOptions :question="row.question" />
            </div>
            <span v-else class="min-w-0 text-ink-gray-5">(question unavailable)</span>
          </li>
        </ol>
      </section>

      <section class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5" data-tour="admin-practice-answers">
        <h2 class="text-xl-semibold text-ink-gray-8">{{ t('detail.answers') }}</h2>
        <ol v-if="(data.afterShuffle ?? []).length" class="mt-3 space-y-3">
          <li
            v-for="(row, i) in data.afterShuffle ?? []"
            :key="row.questionId"
            class="border-b border-outline-gray-1 pb-3 last:border-0 last:pb-0"
          >
            <div class="flex gap-2">
              <span class="text-base-medium text-ink-gray-5">{{ i + 1 }}.</span>
              <div class="min-w-0 flex-1">
                <template v-if="row.question">
                  <p class="text-p-xs text-ink-gray-4">{{ row.question.questionCode }}</p>
                  <div v-if="hasRichContent(row.question.description)" class="mb-2 space-y-2">
                    <div
                      class="rich-text text-p-xs text-ink-gray-5"
                      v-html="sanitizeHtml(row.question.description)"
                    />
                    <div class="border-t border-outline-gray-2" />
                  </div>
                  <div
                    v-if="hasRichContent(row.question.question)"
                    class="rich-text text-p-sm text-ink-gray-8"
                    v-html="sanitizeHtml(row.question.question)"
                  />
                  <QuestionOptions
                    :question="row.question"
                    :selected="answerLetter(row.questionId)"
                    show-correct
                    :selected-correct="answerMap[row.questionId]?.isCorrect ?? false"
                  />
                </template>
                <p v-else class="text-p-sm text-ink-gray-5">(question unavailable)</p>
                <div v-if="showRawAnswer(row)" class="mt-1 flex items-start gap-2">
                  <Badge
                    v-if="answerMap[row.questionId]?.isCorrect"
                    label="✓"
                    theme="green"
                    variant="subtle"
                  />
                  <Badge v-else label="✗" theme="red" variant="subtle" />
                  <span
                    class="whitespace-pre-wrap text-p-sm"
                    :class="answerMap[row.questionId]?.answer ? 'text-ink-gray-8' : 'text-ink-gray-4 italic'"
                  >
                    {{ answerMap[row.questionId]?.answer || t('detail.notAnswered') }}
                  </span>
                </div>
              </div>
            </div>
          </li>
        </ol>
        <p v-else class="mt-2 text-p-sm text-ink-gray-5">{{ t('detail.noAnswers') }}</p>
      </section>
    </template>
  </div>
</template>
