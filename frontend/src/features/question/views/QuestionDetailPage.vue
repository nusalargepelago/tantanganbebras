<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton, dialog, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useQuestionStore } from '../store'
import { OPTION_LETTERS } from '@/shared/questionOptions'
import { hasRichContent } from '@/shared/richText'
import { sanitizeHtml } from '@/shared/sanitize'
import { categoryLabel, difficultyLabel, statusLabel } from '@/shared/labels'

const route = useRoute()
const router = useRouter()
const store = useQuestionStore()
const { t } = useI18n()

const name = computed(() => route.params.name as string)
const question = computed(() => store.current)

const pgOptions = computed(() => {
  const q = question.value
  if (!q || q.questionType !== 'Multiple Choice') return []
  return OPTION_LETTERS.map((letter) => ({
    letter,
    text: String((q as any)[`option${letter.toUpperCase()}`] ?? ''),
    correct: q.correctAnswer === letter,
  }))
})

async function load() {
  await store.get(name.value)
}

function onDelete() {
  dialog.danger({
    title: t('question.deleteTitle'),
    message: t('question.deleteMessageShort', { code: question.value?.questionCode ?? '' }),
    onConfirm: async () => {
      const ok = await store.softDelete(name.value)
      if (!ok) throw new Error(store.error || 'Failed to delete question')
      toast.success(t('question.deletedToast'))
      router.push({ name: 'QuestionList' })
    },
  })
}

onMounted(load)
</script>

<template>
  <AppPageHeader :title="question?.questionCode || t('route.QuestionDetail.title')">
    <template #actions>
      <Button
        variant="outline"
        theme="gray"
        :label="t('list.edit')"
        :route="{ name: 'QuestionEdit', params: { name } }"
      />
      <Button
        v-if="question && !question.disabled"
        variant="outline"
        theme="red"
        icon-left="lucide-trash-2"
        :label="t('list.delete')"
        @click="onDelete"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-pencil"
        :label="t('list.edit')"
        :route="{ name: 'QuestionEdit', params: { name } }"
      />
      <Button
        v-if="question && !question.disabled"
        variant="ghost"
        icon="lucide-trash-2"
        :label="t('list.delete')"
        @click="onDelete"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <Skeleton v-if="store.currentLoading" class="h-40" />
    <ErrorMessage v-else-if="store.error" :message="store.error" />

    <template v-else-if="question">
      <div class="flex flex-wrap items-center gap-2">
        <Badge :label="categoryLabel(question.category)" variant="subtle" />
        <Badge :label="question.questionType" :theme="question.questionType === 'Essay' ? 'blue' : 'gray'" variant="subtle" />
        <Badge :label="question.difficultyLevel" variant="subtle" />
        <Badge
          v-if="question.disabled"
          :label="t('list.deleted')"
          theme="red"
          variant="subtle"
        />
        <Badge
          v-else
          :label="question.status"
          :theme="question.status === 'Active' ? 'green' : 'gray'"
          variant="subtle"
        />
      </div>

      <div class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <h1 class="text-2xl-semibold text-ink-gray-8">{{ question.questionCode }}</h1>
        <div v-if="hasRichContent(question.description)" class="space-y-4">
          <div
            class="rich-text text-p-sm text-ink-gray-5"
            v-html="sanitizeHtml(question.description)"
          />
          <div class="border-t border-outline-gray-2" />
        </div>
        <div
          v-if="hasRichContent(question.question)"
          class="rich-text text-p-base text-ink-gray-8"
          v-html="sanitizeHtml(question.question)"
        />
        <p v-else class="text-p-base text-ink-gray-8">(empty)</p>

        <template v-if="question.questionType === 'Multiple Choice'">
          <div class="space-y-2">
            <div
              v-for="opt in pgOptions"
              :key="opt.letter"
              class="flex items-start gap-3 rounded-4 border px-3 py-2"
              :class="opt.correct ? 'border-outline-green-7 bg-surface-green-2' : 'border-outline-gray-1'"
            >
              <span
                class="flex size-6 shrink-0 items-center justify-center rounded-full text-base-medium"
                :class="opt.correct ? 'bg-surface-green-7 text-white' : 'bg-surface-gray-2 text-ink-gray-6'"
              >
                {{ opt.letter.toUpperCase() }}
              </span>
              <div
                v-if="hasRichContent(opt.text)"
                class="rich-text min-w-0 flex-1 text-p-sm text-ink-gray-8 [&_img]:max-h-48"
                v-html="sanitizeHtml(opt.text)"
              />
              <span v-else class="flex-1 text-p-sm italic text-ink-gray-4">
                {{ t('list.emptyValue') }}
              </span>
              <Badge v-if="opt.correct" label="Correct" theme="green" variant="subtle" class="ml-auto shrink-0" />
            </div>
          </div>
        </template>

        <template v-else>
          <div>
            <p class="text-base-medium text-ink-gray-5">{{ t('detail.referenceAnswer') }}</p>
            <div
              v-if="hasRichContent(question.referenceAnswer)"
              class="rich-text mt-1 text-p-sm text-ink-gray-8"
              v-html="sanitizeHtml(question.referenceAnswer)"
            />
            <p v-else class="mt-1 text-p-sm italic text-ink-gray-4">(none)</p>
          </div>
        </template>
      </div>

      <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
        <h2 class="text-xl-semibold text-ink-gray-8">{{ t('detail.info') }}</h2>
        <dl class="mt-3 grid gap-2 text-p-sm sm:grid-cols-2">
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.category') }}</dt>
            <dd class="text-ink-gray-8">{{ categoryLabel(question.category) }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.difficulty') }}</dt>
            <dd class="text-ink-gray-8">{{ difficultyLabel(question.difficultyLevel) }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.status') }}</dt>
            <dd class="text-ink-gray-8">{{ statusLabel(question.status) }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('field.type') }}</dt>
            <dd class="text-ink-gray-8">{{ question.questionType }}</dd>
          </div>
          <div v-if="question.topicId" class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">Topic</dt>
            <dd class="text-ink-gray-8">{{ question.topicId }}</dd>
          </div>
          <div class="flex min-w-0 justify-between gap-4 sm:block">
            <dt class="text-ink-gray-5">{{ t('detail.slug') }}</dt>
            <dd class="text-ink-gray-8">{{ question.name }}</dd>
          </div>
        </dl>
      </div>
    </template>
  </div>
</template>
