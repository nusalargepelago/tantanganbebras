<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, Radio, RadioGroup, Textarea, TextInput, dialog, toast } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu, RichTextKit, articleToolbar } from 'frappe-ui/editor'

import { useQuestionStore, type Question, type QuestionPayload } from '../store'
import {
  hasErrors,
  validateQuestion,
  type QuestionErrors,
} from '../validation'
import { OPTION_LETTERS, optionKey } from '@/shared/questionOptions'
import { uploadMedia } from '@/shared/editorUpload'
import { optionToolbar } from '@/shared/editorToolbar'
import { hasRichContent } from '@/shared/richText'

const props = defineProps<{ questionName: string }>()
const emit = defineEmits<{ saved: []; discarded: [] }>()

const store = useQuestionStore()
const { t } = useI18n()

const editorExtensions = [RichTextKit]

const form = reactive({
  questionCode: '',
  description: '',
  question: '',
  optionA: '',
  optionB: '',
  optionC: '',
  optionD: '',
  correctAnswer: '',
  referenceAnswer: '',
})
const questionType = ref<'Multiple Choice' | 'Essay'>('Multiple Choice')

const errors = reactive<QuestionErrors>({})
const touched = ref(false)
const snapshot = ref('')
const saving = ref(false)
const saved = ref(false)
const failed = ref(false)
const lastSavedAt = ref<Date | null>(null)
const now = ref(Date.now())

let debounceTimer: ReturnType<typeof setTimeout> | null = null
let clock: ReturnType<typeof setInterval> | null = null
let inFlight = false
let saveGeneration = 0

const isEssay = computed(() => questionType.value === 'Essay')
const isDirty = computed(() => JSON.stringify(form) !== snapshot.value)
const canAct = computed(() => isDirty.value && !saving.value)

const statusBadge = computed(() => {
  if (failed.value) return { label: t('editor.saveFailedBadge'), theme: 'red' as const }
  if (saving.value) return { label: t('editor.savingBadge'), theme: 'amber' as const }
  if (saved.value)
    return { label: t('editor.savedStatus', { relative: relative.value }), theme: 'green' as const }
  return null
})

const relative = computed(() => {
  if (!lastSavedAt.value) return t('editor.justNow')
  const secs = Math.max(0, Math.floor((now.value - lastSavedAt.value.getTime()) / 1000))
  if (secs < 5) return t('editor.justNow')
  if (secs < 60) return t('editor.secondsAgo', { n: secs })
  return t('editor.minutesAgo', { n: Math.floor(secs / 60) })
})

function resetErrors() {
  for (const key of Object.keys(errors)) {
    delete (errors as Record<string, unknown>)[key]
  }
}

function fieldError(key: keyof QuestionErrors): string {
  const raw = errors[key]
  if (!touched.value || !raw) return ''
  if (key.startsWith('option')) return t(raw, { letter: key.slice(6) })
  return t(raw)
}

function applyQuestion(q: Question) {
  questionType.value = q.questionType
  form.questionCode = q.questionCode
  form.description = q.description ?? ''
  form.question = q.question
  form.optionA = q.optionA ?? ''
  form.optionB = q.optionB ?? ''
  form.optionC = q.optionC ?? ''
  form.optionD = q.optionD ?? ''
  form.correctAnswer = q.correctAnswer ?? ''
  form.referenceAnswer = q.referenceAnswer ?? ''
  snapshot.value = JSON.stringify(form)
  touched.value = false
  failed.value = false
  saved.value = false
  resetErrors()
}

function resetForm() {
  questionType.value = 'Multiple Choice'
  form.questionCode = ''
  form.description = ''
  form.question = ''
  form.optionA = ''
  form.optionB = ''
  form.optionC = ''
  form.optionD = ''
  form.correctAnswer = ''
  form.referenceAnswer = ''
  snapshot.value = JSON.stringify(form)
  touched.value = false
  failed.value = false
  saved.value = false
  resetErrors()
}

function buildPayload(): Partial<QuestionPayload> {
  const base = {
    questionCode: form.questionCode,
    question: form.question,
    description: hasRichContent(form.description) ? form.description : null,
  }
  if (isEssay.value) return { ...base, referenceAnswer: form.referenceAnswer }
  return {
    ...base,
    optionA: form.optionA,
    optionB: form.optionB,
    optionC: form.optionC,
    optionD: form.optionD,
    correctAnswer: form.correctAnswer as QuestionPayload['correctAnswer'],
  }
}

function validate(): boolean {
  const found = validateQuestion({
    ...buildPayload(),
    questionType: questionType.value,
  } as QuestionPayload)
  resetErrors()
  Object.assign(errors, found)
  return !hasErrors(found)
}

async function runAutoSave(): Promise<boolean> {
  if (!isDirty.value) return true
  if (inFlight) return false
  touched.value = true
  if (!validate()) return false

  const target = props.questionName
  const generation = ++saveGeneration
  const payload = buildPayload()
  const requested = JSON.stringify(form)

  inFlight = true
  saving.value = true
  const updated = await store.update(target, payload)
  const ok = updated !== null
  inFlight = false

  if (generation !== saveGeneration) return false
  saving.value = false

  if (ok) {
    snapshot.value = requested
    saved.value = true
    failed.value = false
    lastSavedAt.value = new Date()
    emit('saved')
    if (isDirty.value) schedule()
  } else {
    failed.value = true
    toast.error(store.error || 'Failed to save question')
  }
  return ok
}

function cancelPendingSave() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
}

function schedule() {
  cancelPendingSave()
  debounceTimer = setTimeout(runAutoSave, 3000)
}

function flushDraft(target: string) {
  if (!isDirty.value || inFlight) return
  const payload = buildPayload()
  const found = validateQuestion({ ...payload, questionType: questionType.value } as QuestionPayload)
  if (!hasErrors(found)) void store.update(target, payload)
}

async function onSave() {
  if (!canAct.value) return
  cancelPendingSave()
  const ok = await runAutoSave()
  if (ok) toast.success(t('editor.savedToast'))
}

function onDiscard() {
  dialog.confirm({
    title: t('editor.discardTitle'),
    message: t('editor.discardMessage'),
    onConfirm: async () => {
      const fresh = await store.get(props.questionName)
      if (fresh) applyQuestion(fresh)
      emit('discarded')
    },
  })
}

watch(
  form,
  () => {
    if (!isDirty.value) return
    schedule()
  },
  { deep: true },
)

watch(
  () => props.questionName,
  async (name, previous) => {
    saveGeneration++
    cancelPendingSave()
    saving.value = false
    if (previous) flushDraft(previous)
    resetForm()
    if (!name) return
    const q = await store.get(name)
    if (q && props.questionName === name) applyQuestion(q)
  },
)

onMounted(async () => {
  clock = setInterval(() => {
    now.value = Date.now()
  }, 1000)
  const q = store.current && store.current.name === props.questionName ? store.current : await store.get(props.questionName)
  if (q) applyQuestion(q)
})

onBeforeUnmount(() => {
  cancelPendingSave()
  if (clock) clearInterval(clock)
  // Unmount cannot await, and overlapping writes could reorder.
  flushDraft(props.questionName)
})
</script>

<template>
  <div class="flex h-full flex-col">
    <div class="flex items-center justify-between gap-2 border-b border-outline-gray-1 px-4 py-3">
      <div class="min-w-0">
        <p class="truncate text-base-medium text-ink-gray-8">
          {{ form.questionCode || t('editor.untitledHeading') }}
        </p>
        <Badge
          v-if="statusBadge"
          :label="statusBadge.label"
          :theme="statusBadge.theme"
          variant="subtle"
          class="mt-1"
        />
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <Button
          variant="outline"
          theme="gray"
          :label="t('shared.cancel')"
          :disabled="!canAct"
          @click="onDiscard"
        />
        <Button
          variant="solid"
          :label="t('shared.save')"
          :disabled="!canAct"
          :loading="saving"
          @click="onSave"
        />
      </div>
    </div>

    <div class="flex-1 space-y-4 overflow-y-auto p-4">
      <TextInput
        v-model="form.questionCode"
        :label="t('field.questionCode')"
        placeholder="Mini Challenge"
      />

      <div class="space-y-1.5">
        <span class="text-base-medium text-ink-gray-8">{{ t('field.description') }}</span>
        <Editor
          v-model="form.description"
          :extensions="editorExtensions"
          :placeholder="t('question.descriptionPlaceholder')"
          :upload-function="uploadMedia"
        >
          <div
            class="rounded-4 border border-outline-gray-2 bg-surface-gray-2 transition-colors focus-within:border-outline-gray-4 focus-within:bg-surface-base"
          >
            <EditorFixedMenu
              :items="articleToolbar"
              class="overflow-x-auto border-b border-outline-gray-2 px-1.5 py-1"
            />
            <EditorContent class="min-h-20 px-3 py-2 text-p-sm" />
          </div>
        </Editor>
      </div>

      <div class="space-y-1.5">
        <span class="text-base-medium text-ink-gray-8">
          {{ t('field.question') }}
          <span class="text-ink-red-6">*</span>
        </span>
        <Editor
          v-model="form.question"
          :extensions="editorExtensions"
          :placeholder="t('question.questionPlaceholder')"
          :upload-function="uploadMedia"
        >
          <div
            class="rounded-4 border border-outline-gray-2 bg-surface-gray-2 transition-colors focus-within:border-outline-gray-4 focus-within:bg-surface-base"
          >
            <EditorFixedMenu
              :items="articleToolbar"
              class="overflow-x-auto border-b border-outline-gray-2 px-1.5 py-1"
            />
            <EditorContent class="min-h-32 px-3 py-2 text-p-sm" />
          </div>
        </Editor>
        <p v-if="fieldError('question')" class="text-p-xs text-ink-red-6">
          {{ fieldError('question') }}
        </p>
      </div>

      <template v-if="!isEssay">
        <div
          v-for="letter in OPTION_LETTERS"
          :key="letter"
          class="space-y-1.5"
        >
          <span class="text-base-medium text-ink-gray-8">
            {{ t('field.option', { letter: letter.toUpperCase() }) }}
          </span>
          <Editor
            v-model="form[optionKey(letter)]"
            :extensions="editorExtensions"
            :placeholder="t('field.option', { letter: letter.toUpperCase() })"
            :upload-function="uploadMedia"
          >
            <div
              class="rounded-4 border border-outline-gray-2 bg-surface-gray-2 transition-colors focus-within:border-outline-gray-4 focus-within:bg-surface-base"
            >
              <EditorFixedMenu
                :items="optionToolbar"
                size="xs"
                class="overflow-x-auto border-b border-outline-gray-2 px-1.5 py-0.5"
              />
              <EditorContent class="min-h-10 px-3 py-2 text-p-sm" />
            </div>
          </Editor>
          <p
            v-if="fieldError(optionKey(letter))"
            class="text-p-xs text-ink-red-6"
          >
            {{ fieldError(optionKey(letter)) }}
          </p>
        </div>

        <RadioGroup
          v-model="form.correctAnswer"
          :label="t('field.correctAnswer')"
          :error="fieldError('correctAnswer')"
        >
          <div class="flex gap-4">
            <Radio v-for="l in OPTION_LETTERS" :key="l" :value="l" :label="l.toUpperCase()" />
          </div>
        </RadioGroup>
      </template>

      <Textarea
        v-else
        v-model="form.referenceAnswer"
        :label="t('field.referenceAnswer')"
        :placeholder="t('editor.referencePlaceholder')"
        :rows="5"
        :error="fieldError('referenceAnswer')"
      />
    </div>
  </div>
</template>
