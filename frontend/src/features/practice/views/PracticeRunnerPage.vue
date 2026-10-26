<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, ErrorMessage, Skeleton } from 'frappe-ui'

import QuizRunnerShell, {
  type RunnerQuestion,
} from '@/shared/components/QuizRunnerShell.vue'

import { usePracticeStore } from '../store'

const store = usePracticeStore()
const { t } = useI18n()
const notFound = ref(false)

const active = computed(() => store.active)
const practice = computed(() => active.value?.practice ?? null)

const runnerQuestions = computed<RunnerQuestion[]>(() =>
  (active.value?.questions ?? []).map((q) => ({
    id: q.questionId,
    question: q.question as RunnerQuestion['question'],
  })),
)

const savedAnswers = computed(() =>
  (active.value?.savedAnswers ?? []).map((s) => ({
    id: s.questionId,
    answer: s.answer,
  })),
)

const durationMin = computed(() => practice.value?.timeLimit ?? 30)
const startedAt = computed(() => practice.value?.startedAt ?? null)
const redirectAfterSubmit = computed(() => ({
  name: 'PracticeResult',
  params: { name: practice.value?.name ?? '' },
}))

function onAnswer(id: string, value: string) {
  if (practice.value) store.saveAnswer(practice.value.name, id, value)
}

async function submitFn(answers: { id: string; answer: string }[]): Promise<boolean> {
  if (!practice.value) return false
  return store.submit(
    practice.value.name,
    answers.map((a) => ({ questionId: a.id, answer: a.answer })),
  )
}

onMounted(async () => {
  const result = await store.start()
  if (!result) notFound.value = true
})
</script>

<template>
  <div class="mx-auto w-full max-w-3xl px-5 py-6">
    <div v-if="store.loading || (!active && !notFound)" class="space-y-3">
      <Skeleton class="h-10" />
      <Skeleton class="h-64" />
    </div>

    <div
      v-else-if="notFound || !active"
      class="flex flex-col items-center gap-3 rounded-6 border border-outline-gray-1 py-12 text-center"
    >
      <ErrorMessage v-if="store.error" :message="store.error" />
      <span v-else class="lucide-clipboard-x size-8 text-ink-gray-4" aria-hidden="true" />
      <p v-if="!store.error" class="text-p-sm text-ink-gray-5">
        {{ t('runner.noPracticeInProgress') }}
      </p>
      <Button
        variant="outline"
        theme="gray"
        :label="t('practice.backToList')"
        :route="{ name: 'PracticeList' }"
      />
    </div>

    <div v-else class="h-[calc(100vh-8rem)] overflow-hidden rounded-6 border border-outline-gray-1">
      <QuizRunnerShell
        title="Practice"
        :questions="runnerQuestions"
        :saved-answers="savedAnswers"
        :duration-min="durationMin"
        :started-at="startedAt"
        :submit-fn="submitFn"
        :redirect-after-submit="redirectAfterSubmit"
        @answer="onAnswer"
      />
    </div>
  </div>
</template>
