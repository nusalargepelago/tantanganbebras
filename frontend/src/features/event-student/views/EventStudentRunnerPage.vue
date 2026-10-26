<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, ErrorMessage, Skeleton } from 'frappe-ui'

import QuizRunnerShell, {
  type RunnerQuestion,
} from '@/shared/components/QuizRunnerShell.vue'

import { useEventStudentStore } from '../store'

const route = useRoute()
const router = useRouter()
const store = useEventStudentStore()
const { t } = useI18n()
const notFound = ref(false)

const attemptName = computed(() => route.params.name as string)
const active = computed(() => store.active)

const runnerQuestions = computed<RunnerQuestion[]>(() =>
  (active.value?.questions ?? []).map((q) => ({
    id: q.eventQuestionId,
    question: q.question as RunnerQuestion['question'],
  })),
)

const savedAnswers = computed(() =>
  (active.value?.savedAnswers ?? []).map((s) => ({
    id: s.eventQuestionId,
    answer: s.answer,
  })),
)

const durationMin = computed(() => (active.value?.event?.timeLimit as number | undefined) ?? 0)
const startedAt = computed(() => active.value?.eventStudent?.startedAt ?? null)
const redirectAfterSubmit = computed(() => ({
  name: 'EventStudentResult',
  params: { name: attemptName.value },
}))

function onAnswer(eventQuestionId: string, value: string) {
  store.saveAnswer(attemptName.value, eventQuestionId, value)
}

async function submitFn(answers: { id: string; answer: string }[]): Promise<boolean> {
  return store.submit(
    attemptName.value,
    answers.map((a) => ({ eventQuestionId: a.id, answer: a.answer })),
  )
}

onMounted(async () => {
  const result = await store.start(attemptName.value)
  if (!result) {
    notFound.value = true
    return
  }
  if (result.eventStudent.finishedAt) {
    await router.replace({
      name: 'EventStudentResult',
      params: { name: attemptName.value },
    })
  }
})
</script>

<template>
  <div class="mx-auto w-full max-w-3xl px-5 py-6">
    <div v-if="!active && !notFound" class="space-y-3">
      <Skeleton class="h-10" />
      <Skeleton class="h-64" />
    </div>

    <div
      v-else-if="notFound || !active"
      class="flex flex-col items-center gap-3 rounded-6 border border-outline-gray-1 py-12 text-center"
    >
      <ErrorMessage v-if="store.error" :message="store.error" />
      <span v-else class="lucide-calendar-x size-8 text-ink-gray-4" aria-hidden="true" />
      <p v-if="!store.error" class="text-p-sm text-ink-gray-5">
        {{ t('runner.attemptNotFound') }}
      </p>
      <Button
        variant="outline"
        theme="gray"
        :label="t('runner.backToEvents')"
        :route="{ name: 'EventStudentList' }"
      />
    </div>

    <div v-else class="h-[calc(100vh-8rem)] overflow-hidden rounded-6 border border-outline-gray-1">
      <QuizRunnerShell
        :title="active.event.eventName"
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
