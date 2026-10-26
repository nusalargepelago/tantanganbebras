<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import type { RouteLocationRaw } from 'vue-router'
import { Badge, Button, Radio, RadioGroup, Textarea, dialog } from 'frappe-ui'

import { useCountdown } from '@/shared/composables/useCountdown'
import { hasRichContent } from '@/shared/richText'
import { OPTION_LETTERS, optionKey } from '@/shared/questionOptions'
import { sanitizeHtml } from '@/shared/sanitize'
import { useFocusMode } from '@/app/focus-mode'

export interface RunnerQuestionPayload {
  questionType: 'Multiple Choice' | 'Essay'
  question: string
  description?: string | null
  optionA?: string | null
  optionB?: string | null
  optionC?: string | null
  optionD?: string | null
}

export interface RunnerQuestion {
  id: string
  question: RunnerQuestionPayload | null
}

const props = defineProps<{
  title: string
  questions: RunnerQuestion[]
  savedAnswers: { id: string; answer: string }[]
  durationMin: number
  startedAt: string | null
  submitFn: (answers: { id: string; answer: string }[]) => Promise<boolean>
  redirectAfterSubmit: RouteLocationRaw
}>()

const emit = defineEmits<{ answer: [id: string, value: string] }>()

const router = useRouter()
const { t } = useI18n()
const { active: focusMode, toggle: toggleFocus } = useFocusMode()
const index = ref(0)
const answers = reactive<Record<string, string>>({})
const submitting = ref(false)
const done = ref(false)

const current = computed(() => props.questions[index.value])
const question = computed(() => current.value?.question ?? null)
const isEssay = computed(() => question.value?.questionType === 'Essay')
const answeredCount = computed(
  () => props.questions.filter((q) => (answers[q.id] ?? '').trim() !== '').length,
)

const deadline = computed(() => {
  if (props.durationMin <= 0 || !props.startedAt) return null
  const started = Date.parse(props.startedAt)
  if (Number.isNaN(started)) return null
  return started + props.durationMin * 60_000
})

const { timeLeft, expired, format } = useCountdown(() => deadline.value, () => {
  if (!done.value && !submitting.value) void onSubmit()
})

const currentAnswer = computed({
  get: () => answers[current.value?.id ?? ''] ?? '',
  set: (value: string) => setAnswer(value),
})

const countdownTone = computed<'red' | 'amber' | 'gray'>(() => {
  if (expired.value) return 'red'
  if (timeLeft.value !== null && timeLeft.value <= 60_000) return 'amber'
  return 'gray'
})

const pagerTheme = (i: number): 'blue' | 'green' | 'gray' => {
  if (i === index.value) return 'blue'
  return isAnswered(props.questions[i]?.id ?? '') ? 'green' : 'gray'
}

const options = computed(() =>
  OPTION_LETTERS.map((letter) => ({
    letter,
    html: (question.value?.[optionKey(letter)] ?? '').trim(),
  })),
)

function isAnswered(id: string): boolean {
  return (answers[id] ?? '').trim() !== ''
}

function setAnswer(value: string) {
  const id = current.value?.id
  if (!id) return
  answers[id] = value
  emit('answer', id, value)
}

function goTo(i: number) {
  index.value = Math.max(0, Math.min(props.questions.length - 1, i))
}

let submitPromise: Promise<boolean> | null = null

async function performSubmit(): Promise<boolean> {
  if (done.value) return true
  if (submitPromise) return submitPromise
  submitting.value = true
  const payload = props.questions.map((q) => ({
    id: q.id,
    answer: answers[q.id] ?? '',
  }))
  submitPromise = props.submitFn(payload).then((ok) => {
    if (ok) done.value = true
    return ok
  })
  try {
    return await submitPromise
  } finally {
    submitting.value = false
    submitPromise = null
  }
}

async function onSubmit() {
  if (await performSubmit()) {
    await router.push(props.redirectAfterSubmit)
  }
}

onBeforeRouteLeave(() => {
  if (done.value) return true
  return new Promise<boolean | RouteLocationRaw>((resolve) => {
    dialog.confirm({
      title: t('runner.leaveTitle'),
      message: t('runner.leaveMessage'),
      confirmLabel: t('runner.leaveConfirm'),
      cancelLabel: t('runner.leaveCancel'),
      theme: 'amber',
      onConfirm: async () => {
        const ok = await performSubmit()
        resolve(ok ? props.redirectAfterSubmit : false)
      },
      onCancel: () => resolve(false),
    })
  })
})

watch(
  () => props.savedAnswers,
  (saved) => {
    for (const row of saved) answers[row.id] = row.answer
  },
  { immediate: true },
)

watch(
  () => props.questions,
  (qs) => {
    if (index.value >= qs.length) index.value = 0
  },
)

function onBeforeUnload(event: BeforeUnloadEvent) {
  if (done.value) return
  event.preventDefault()
  event.returnValue = ''
}

onMounted(() => {
  window.addEventListener('beforeunload', onBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
})
</script>

<template>
  <div class="flex h-full flex-col">
    <header
      class="flex items-center justify-between gap-3 border-b border-outline-gray-1 px-4 py-3"
      data-tour="runner-header"
    >
      <div class="min-w-0">
        <p class="truncate text-base-medium text-ink-gray-8">{{ title }}</p>
          <p class="text-p-xs text-ink-gray-5">
            {{
              t('runner.questionOf', {
                i: questions.length ? index + 1 : 0,
                n: questions.length,
              })
            }}
            <span v-if="!submitting"> • {{ t('runner.autoSaved') }}</span>
          </p>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <Badge
          v-if="expired"
          :label="t('runner.timeUp')"
          theme="red"
          variant="subtle"
          data-tour="runner-timer"
        />
        <Badge
          v-else-if="timeLeft !== null"
          :label="format(timeLeft)"
          :theme="countdownTone as 'red' | 'amber' | 'gray'"
          variant="subtle"
          data-tour="runner-timer"
        />
        <Button
          variant="ghost"
          theme="gray"
          :icon="focusMode ? 'lucide-panel-left-open' : 'lucide-panel-left-close'"
          :label="focusMode ? t('runner.showSidebar') : t('runner.focusMode')"
          @click="toggleFocus"
        />
        <Button
          variant="solid"
          :label="t('runner.submit')"
          :loading="submitting"
          :disabled="done"
          data-tour="runner-submit"
          @click="onSubmit"
        />
      </div>
    </header>

    <div v-if="questions.length === 0" class="flex flex-1 items-center justify-center p-8">
      <p class="text-p-sm text-ink-gray-5">{{ t('runner.noQuestions') }}</p>
    </div>

    <div v-else class="flex min-h-0 flex-1 flex-col">
      <div class="flex-1 space-y-4 overflow-y-auto p-4">
        <template v-if="question">
          <div v-if="hasRichContent(question.description)" class="space-y-4">
            <div
              class="rich-text text-p-sm text-ink-gray-5"
              v-html="sanitizeHtml(question.description)"
            />
            <div class="border-t border-outline-gray-2" />
          </div>
          <div class="rich-text text-p-base text-ink-gray-8" v-html="sanitizeHtml(question.question)" />

          <RadioGroup v-if="!isEssay" v-model="currentAnswer" :label="t('runner.yourAnswer')">
            <div class="space-y-2">
              <div
                v-for="option in options"
                :key="option.letter"
                class="rounded-4 border px-3 py-2 transition-colors"
                :class="
                  currentAnswer === option.letter
                    ? 'border-outline-blue-6 bg-surface-blue-1'
                    : 'border-outline-gray-1'
                "
              >
                <Radio :value="option.letter">
                  <template #label>
                    <span class="flex items-start gap-2">
                      <span class="shrink-0 font-medium">{{ option.letter.toUpperCase() }}.</span>
                      <span
                        v-if="hasRichContent(option.html)"
                        class="rich-text min-w-0 flex-1 select-text [&_img]:max-h-48"
                        v-html="sanitizeHtml(option.html)"
                      />
                      <span v-else class="flex-1 italic text-ink-gray-4">
                        {{ t('list.emptyValue') }}
                      </span>
                    </span>
                  </template>
                </Radio>
              </div>
            </div>
          </RadioGroup>

          <Textarea
            v-else
            v-model="currentAnswer"
            :label="t('runner.yourAnswer')"
            :rows="6"
            :placeholder="t('runner.answerPlaceholder')"
          />
        </template>
        <p v-else class="text-p-sm text-ink-gray-5">{{ t('runner.unavailable') }}</p>
      </div>

      <footer class="flex items-center justify-between gap-3 border-t border-outline-gray-1 px-4 py-3">
        <Button
          variant="outline"
          theme="gray"
          :label="t('runner.previous')"
          :disabled="index === 0"
          @click="goTo(index - 1)"
        />

        <div class="flex flex-wrap justify-center gap-1" data-tour="runner-pager">
          <Button
            v-for="(_, i) in questions"
            :key="i"
            :variant="i === index ? 'solid' : 'outline'"
            :theme="pagerTheme(i)"
            size="sm"
            :label="String(i + 1)"
            @click="goTo(i)"
          />
        </div>

        <Button
          variant="solid"
          theme="gray"
          :label="t('runner.next')"
          :disabled="index >= questions.length - 1"
          @click="goTo(index + 1)"
        />
      </footer>
    </div>
  </div>
</template>
