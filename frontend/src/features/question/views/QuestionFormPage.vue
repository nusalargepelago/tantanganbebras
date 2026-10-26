<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  ErrorMessage,
  FormControl,
  Radio,
  RadioGroup,
  Select,
  Textarea,
  toast,
} from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu, RichTextKit, articleToolbar } from 'frappe-ui/editor'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { uploadMedia } from '@/shared/editorUpload'
import { optionToolbar } from '@/shared/editorToolbar'
import { hasRichContent } from '@/shared/richText'

import {
  useQuestionStore,
  type Category,
  type CorrectAnswer,
  type Difficulty,
  type QuestionPayload,
  type QuestionStatus,
  type QuestionType,
  type Topic,
} from '../store'
import {
  hasErrors,
  validateQuestion,
  type QuestionErrors,
} from '../validation'
import { OPTION_LETTERS, optionKey } from '@/shared/questionOptions'
import {
  categoryLabel,
  categoryOptions,
  difficultyOptions,
  statusOptions,
} from '@/shared/labels'
import TopicModal from '../components/TopicModal.vue'

const route = useRoute()
const router = useRouter()
const store = useQuestionStore()
const { t } = useI18n()

const name = computed(() => (route.name === 'QuestionEdit' ? (route.params.name as string) : null))
const isEdit = computed(() => !!name.value)

const typeSelect = computed(() => [
  { label: t('field.multipleChoice'), value: 'Multiple Choice' },
  { label: t('list.essay'), value: 'Essay' },
])

const form = reactive({
  questionCode: '',
  questionType: 'Multiple Choice' as QuestionType,
  description: '',
  question: '',
  optionA: '',
  optionB: '',
  optionC: '',
  optionD: '',
  correctAnswer: '',
  referenceAnswer: '',
  category: 'cub' as Category,
  difficultyLevel: 'Easy' as Difficulty,
  status: 'Active' as QuestionStatus,
  topicId: '' as string,
})

const errors = reactive<QuestionErrors>({})
const touched = ref(false)
const snapshot = ref('')
const submitting = ref(false)
const loadError = ref('')

const CODE_PREFIX: Record<string, string> = { cub: 'CUB', scout: 'SCOUT', rover: 'ROVER' }
let codegenToken = 0

const editorExtensions = [RichTextKit]

async function generateCode() {
  if (isEdit.value) return
  const token = ++codegenToken
  const prefix = CODE_PREFIX[form.category] ?? 'QC'
  const pattern = new RegExp(`^${prefix}-(\\d+)$`)
  let max = 0
  try {
    await store.list({
      category: form.category,
      includeDisabled: true,
      page: 1,
      perPage: 200,
    })
    for (const item of store.items) {
      const match = item.questionCode.match(pattern)
      if (match) max = Math.max(max, Number(match[1]))
    }
  } catch {
    max = 0
  }
  if (token !== codegenToken) return
  form.questionCode = `${prefix}-${String(max + 1).padStart(3, '0')}`
}

const isEssay = computed(() => form.questionType === 'Essay')
const isDirty = computed(() => JSON.stringify(form) !== snapshot.value)
const canSave = computed(
  () =>
    isDirty.value &&
    !submitting.value &&
    (isEdit.value || form.questionCode.trim() !== ''),
)

const topicOptions = computed(() => [
  { label: t('question.topicNone'), value: '' },
  ...[...store.topics]
    .sort((a, b) => a.category.localeCompare(b.category) || a.idx - b.idx)
    .map((t) => ({
      label: `${t.title} · ${categoryLabel(t.category)}`,
      value: t.name,
    })),
  { label: t('question.newTopic'), value: NEW_TOPIC, icon: 'lucide-plus' },
])

const categorySelect = computed(() => categoryOptions())

const topicModalOpen = ref(false)
const NEW_TOPIC = '__new_topic__'

function openAddTopic() {
  topicModalOpen.value = true
}

async function onTopicSaved(topic: Topic | null) {
  await store.listTopics()
  if (topic) form.topicId = topic.name
}

watch(
  () => form.topicId,
  (value, old) => {
    if (value !== NEW_TOPIC) return
    form.topicId = old ?? ''
    openAddTopic()
  },
)
const difficultySelect = computed(() => difficultyOptions())
const statusSelect = computed(() => statusOptions())

const correctOptions = OPTION_LETTERS.map((l) => ({ label: l.toUpperCase(), value: l }))

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

function snapshotForm() {
  snapshot.value = JSON.stringify(form)
}

async function load() {
  await store.listTopics()
  if (name.value) {
    const question = await store.get(name.value)
    if (!question) {
      loadError.value = store.error || t('question.loadFailed')
      return
    }
    Object.assign(form, {
      questionCode: question.questionCode,
      questionType: question.questionType,
      description: question.description ?? '',
      question: question.question,
      optionA: question.optionA ?? '',
      optionB: question.optionB ?? '',
      optionC: question.optionC ?? '',
      optionD: question.optionD ?? '',
      correctAnswer: question.correctAnswer ?? '',
      referenceAnswer: question.referenceAnswer ?? '',
      category: question.category,
      difficultyLevel: question.difficultyLevel,
      status: question.status,
      topicId: question.topicId ?? '',
    })
  } else if (route.query.type === 'essay') {
    form.questionType = 'Essay'
  }
  snapshotForm()
}

function buildPayload(): QuestionPayload {
  const base = {
    questionCode: form.questionCode.trim(),
    question: form.question,
    description: hasRichContent(form.description) ? form.description : null,
    questionType: form.questionType,
    category: form.category,
    difficultyLevel: form.difficultyLevel,
    status: form.status,
    topicId: form.topicId || null,
  }
  if (isEssay.value) {
    return { ...base, referenceAnswer: form.referenceAnswer }
  }
  return {
    ...base,
    optionA: form.optionA,
    optionB: form.optionB,
    optionC: form.optionC,
    optionD: form.optionD,
    correctAnswer: form.correctAnswer as CorrectAnswer,
  }
}

async function onSubmit() {
  if (!isDirty.value || submitting.value) return
  resetErrors()
  const found = validateQuestion(buildPayload())
  Object.assign(errors, found)
  touched.value = true
  if (hasErrors(found)) return

  submitting.value = true
  const saved = isEdit.value
    ? await store.update(name.value!, buildPayload())
    : await store.create(buildPayload())
  submitting.value = false

  if (!saved) {
    toast.error(store.error || t('question.saveFailed'))
    return
  }
  toast.success(isEdit.value ? t('question.updatedToast') : t('question.createdToast'))
  router.push({ name: 'QuestionDetail', params: { name: saved.name } })
}

function onCancel() {
  if (isEdit.value) {
    router.push({ name: 'QuestionDetail', params: { name: name.value } })
  } else {
    router.push({ name: 'QuestionList' })
  }
}

watch(
  () => ({ ...form }),
  () => {
    if (!touched.value) return
    const found = validateQuestion(buildPayload())
    resetErrors()
    Object.assign(errors, found)
  },
)

watch(
  () => form.category,
  () => {
    void generateCode()
  },
)

onMounted(async () => {
  await load()
  if (!isEdit.value) {
    await generateCode()
    snapshotForm()
  }
})
</script>

<template>
  <AppPageHeader
    :title="isEdit ? t('route.QuestionEdit.title') : t('route.QuestionNew.title')"
  >
    <template #leading>
      <Badge v-if="isDirty" :label="t('form.unsaved')" theme="amber" variant="subtle" />
    </template>
    <template #actions>
      <Button variant="outline" theme="gray" :label="t('shared.cancel')" @click="onCancel" />
      <Button
        variant="solid"
        :label="t('shared.save')"
        :loading="submitting"
        :disabled="!canSave"
        data-tour="admin-question-save"
        @click="onSubmit"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-x"
        :label="t('shared.cancel')"
        @click="onCancel"
      />
      <Button
        variant="ghost"
        icon="lucide-check"
        :label="t('shared.save')"
        :loading="submitting"
        :disabled="!canSave"
        data-tour="admin-question-save"
        @click="onSubmit"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <ErrorMessage v-if="loadError" :message="loadError" />

    <section class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5" data-tour="admin-question-detail">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('form.detail') }}</h2>
      <div class="grid gap-4 sm:grid-cols-2">
        <FormControl
          v-model="form.questionCode"
          :label="t('field.questionCode')"
          placeholder="CUB-001"
          required
        />
        <Select
          v-model="form.questionType"
          :label="t('field.type')"
          :options="typeSelect"
          :disabled="isEdit"
        />
      </div>
    </section>

    <section class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5" data-tour="admin-question-content">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('form.content') }}</h2>
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
            <EditorContent class="min-h-24 px-3 py-2 text-p-sm" />
          </div>
        </Editor>
        <p v-if="fieldError('question')" class="text-p-xs text-ink-red-6">
          {{ fieldError('question') }}
        </p>
      </div>

      <template v-if="!isEssay">
        <div class="grid gap-3">
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
        </div>
        <RadioGroup
          v-model="form.correctAnswer"
          :label="t('field.correctAnswer')"
          :error="fieldError('correctAnswer')"
          required
        >
          <div class="flex gap-4">
            <Radio
              v-for="opt in correctOptions"
              :key="opt.value"
              :value="opt.value"
              :label="opt.label"
            />
          </div>
        </RadioGroup>
      </template>

      <Textarea
        v-else
        v-model="form.referenceAnswer"
        :label="t('field.referenceAnswer')"
        :placeholder="t('question.referencePlaceholder')"
        :rows="4"
        :error="fieldError('referenceAnswer')"
        required
      />
    </section>

    <section class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5" data-tour="admin-question-settings">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('form.settings') }}</h2>
      <div class="grid gap-4 sm:grid-cols-2">
        <Select v-model="form.category" :label="t('field.category')" :options="categorySelect" />
        <Select
          v-model="form.difficultyLevel"
          :label="t('field.difficulty')"
          :options="difficultySelect"
        />
        <Select v-model="form.status" :label="t('field.status')" :options="statusSelect" />
        <Select v-model="form.topicId" :label="t('field.topic')" :options="topicOptions" />
      </div>
    </section>

    <TopicModal
      v-model:open="topicModalOpen"
      :category="form.category"
      @saved="onTopicSaved"
    />
  </div>
</template>
