<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Checkbox,
  ErrorMessage,
  FormControl,
  Select,
  Textarea,
  TextInput,
  toast,
} from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { categoryLabel, categoryOptions } from '@/shared/labels'
import { useQuestionStore } from '@/features/question/store'
import { useEventStore } from '../store'

const categorySelect = computed(() => categoryOptions())

const route = useRoute()
const router = useRouter()
const store = useEventStore()
const { t } = useI18n()
const questionStore = useQuestionStore()

const eventName = computed(() => (route.name === 'EventEdit' ? (route.params.name as string) : null))
const isEdit = computed(() => !!eventName.value)

const form = reactive({
  eventName: '',
  category: 'cub',
  timeLimit: 60,
  eventDeadline: '',
  description: '',
  published: false,
})
const selectedQuestions = ref<string[]>([])
const snapshot = ref('')
const ready = ref(false)
const submitting = ref(false)
const loadError = ref('')

function formState() {
  return { form: { ...form }, questions: [...selectedQuestions.value] }
}

const isDirty = computed(() => JSON.stringify(formState()) !== snapshot.value)

const availableQuestions = computed(() =>
  questionStore.items.filter(
    (q) =>
      q.category === form.category &&
      !q.disabled &&
      (q.status === 'Active' || selectedQuestions.value.includes(q.name)),
  ),
)

const canSave = computed(() => {
  if (!isDirty.value || submitting.value) return false
  if (!form.eventName.trim() || !form.eventDeadline) return false
  return selectedQuestions.value.length > 0
})

function isPicked(name: string): boolean {
  return selectedQuestions.value.includes(name)
}

function toggle(name: string) {
  const i = selectedQuestions.value.indexOf(name)
  if (i === -1) selectedQuestions.value.push(name)
  else selectedQuestions.value.splice(i, 1)
}

async function load() {
  await questionStore.list({ perPage: 200 })
  if (eventName.value) {
    const event = await store.get(eventName.value)
    if (!event) {
      loadError.value = store.error || t('event.loadFailed')
      return
    }
    form.eventName = event.eventName
    form.category = event.category
    form.timeLimit = event.timeLimit
    form.eventDeadline = event.eventDeadline.slice(0, 16)
    form.description = event.description ?? ''
    form.published = event.published
    selectedQuestions.value = event.questions.map((q) => q.name)
    selectedQuestions.value = selectedQuestions.value.filter((name) =>
      availableQuestions.value.some((q) => q.name === name),
    )
  } else {
    form.eventDeadline = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16)
  }
  snapshot.value = JSON.stringify(formState())
  ready.value = true
}

function payload() {
  return {
    eventName: form.eventName.trim(),
    eventDeadline: new Date(form.eventDeadline).toISOString(),
    category: form.category,
    timeLimit: Number(form.timeLimit),
    questionsId: selectedQuestions.value,
    published: form.published,
    description: form.description.trim() || null,
  }
}

async function onSubmit() {
  if (!canSave.value) return
  submitting.value = true
  const saved = isEdit.value
    ? await store.update(eventName.value!, payload())
    : await store.create(payload())
  submitting.value = false

  if (!saved) {
    toast.error(store.error || t('event.saveFailed'))
    return
  }
  toast.success(isEdit.value ? t('event.updatedToast') : t('event.createdToast'))
  router.push({ name: 'EventDetail', params: { name: saved.name } })
}

watch(
  () => form.category,
  () => {
    if (!ready.value) return
    selectedQuestions.value = selectedQuestions.value.filter((name) =>
      availableQuestions.value.some((q) => q.name === name),
    )
  },
)

onMounted(load)
</script>

<template>
  <AppPageHeader
    :title="isEdit ? t('route.EventEdit.title') : t('route.EventNew.title')"
  >
    <template #leading>
      <Badge v-if="isDirty" :label="t('form.unsaved')" theme="amber" variant="subtle" />
    </template>
    <template #actions>
      <Button
        variant="outline"
        theme="gray"
        :label="t('shared.cancel')"
        :route="isEdit ? { name: 'EventDetail', params: { name: eventName } } : { name: 'EventList' }"
      />
      <Button
        variant="solid"
        :label="t('shared.save')"
        :loading="submitting"
        :disabled="!canSave"
        data-tour="admin-event-save"
        @click="onSubmit"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-x"
        :label="t('shared.cancel')"
        :route="isEdit ? { name: 'EventDetail', params: { name: eventName } } : { name: 'EventList' }"
      />
      <Button
        variant="ghost"
        icon="lucide-check"
        :label="t('shared.save')"
        :loading="submitting"
        :disabled="!canSave"
        data-tour="admin-event-save"
        @click="onSubmit"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <ErrorMessage v-if="loadError" :message="loadError" />

    <section class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5" data-tour="admin-event-details">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('form.details') }}</h2>
      <FormControl
        v-model="form.eventName"
        :label="t('field.eventName')"
        placeholder="Bebras 2026"
        required
      />
      <div class="grid gap-4 sm:grid-cols-2">
        <Select v-model="form.category" :label="t('field.category')" :options="categorySelect" />
        <TextInput
          v-model.number="form.timeLimit"
          type="number"
          :label="t('field.durationMinutes')"
          :min="1"
          :max="600"
        />
      </div>
      <FormControl
        v-model="form.eventDeadline"
        type="datetime-local"
        :label="t('field.eventDeadline')"
        required
      />
      <Textarea
        v-model="form.description"
        :label="t('field.description')"
        :rows="3"
        :placeholder="t('event.descriptionPlaceholder')"
      />
      <Checkbox v-model="form.published" :label="t('field.publish')" />
    </section>

    <section class="space-y-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5" data-tour="admin-event-questions">
      <div class="flex items-center justify-between">
        <h2 class="text-xl-semibold text-ink-gray-8">
          {{ t('event.selectQuestions', { count: availableQuestions.length }) }}
        </h2>
        <Badge
          :label="t('event.selectedBadge', { n: selectedQuestions.length })"
          variant="subtle"
        />
      </div>
      <p v-if="availableQuestions.length === 0" class="text-p-sm text-ink-gray-5">
        {{ t('event.noActiveQuestions', { category: categoryLabel(form.category) }) }}
      </p>
      <div v-else class="max-h-64 space-y-1 overflow-y-auto rounded-4 border border-outline-gray-1 p-2">
        <div
          v-for="q in availableQuestions"
          :key="q.name"
          class="rounded-4 px-2 py-1 hover:bg-surface-gray-2"
        >
          <Checkbox
            :model-value="isPicked(q.name)"
            :label="q.questionCode"
            @update:model-value="toggle(q.name)"
          />
        </div>
      </div>
    </section>
  </div>
</template>
