<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Dialog, FormControl, Select, Skeleton, toast, type DialogAction } from 'frappe-ui'

import { useQuestionStore, type Category, type Topic } from '../store'
import { categoryOptions as buildCategoryOptions } from '@/shared/labels'

const props = defineProps<{
  open: boolean
  category?: Category
  topicName?: string | null
}>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: [topic: Topic | null]
}>()

const store = useQuestionStore()
const { t } = useI18n()
const saving = ref(false)
const loading = ref(false)
const localError = ref('')

const form = reactive({ title: '', category: 'cub' as Category, idx: 0 })
const isEdit = computed(() => !!props.topicName)
const canSave = computed(() => form.title.trim() !== '' && !saving.value)
const categoryOptions = computed(() => buildCategoryOptions())

const actions = computed<DialogAction[]>(() => [
  { label: t('shared.cancel'), variant: 'outline', theme: 'gray', onClick: ({ close }: { close: () => void }) => close() },
  { label: t('shared.save'), variant: 'solid', theme: 'gray', onClick: ({ close }: { close: () => void }) => onSave(close) },
])

async function load() {
  localError.value = ''
  form.title = ''
  form.category = props.category ?? 'cub'
  form.idx = 0
  if (!props.topicName) return

  loading.value = true
  await store.listTopics()
  const topic = store.topics.find((t) => t.name === props.topicName)
  if (topic) {
    form.title = topic.title
    form.category = topic.category
    form.idx = topic.idx
  } else {
    localError.value = t('editor.topicNotFound')
    emit('update:open', false)
  }
  loading.value = false
}

async function onSave(close: () => void) {
  if (!canSave.value) return
  saving.value = true
  const payload = { title: form.title.trim(), category: form.category, idx: form.idx }
  const saved = props.topicName
    ? await store.updateTopic(props.topicName, payload)
    : await store.createTopic(payload)
  saving.value = false

  if (!saved) {
    toast.error(store.error || t('editor.topicSaveFailed'))
    return
  }
  toast.success(props.topicName ? t('editor.topicUpdatedToast') : t('editor.topicCreatedToast'))
  emit('saved', saved)
  close()
}

function submit() {
  onSave(() => emit('update:open', false))
}

watch(
  () => props.open,
  (open) => {
    if (open) load()
  },
)
</script>

<template>
  <Dialog
    :open="open"
    :title="isEdit ? t('editor.topicEditTitle') : t('editor.topicNewTitle')"
    size="sm"
    :actions="actions"
    @update:open="emit('update:open', $event)"
  >
    <div v-if="loading" class="space-y-3">
      <Skeleton class="h-10" />
      <Skeleton class="h-10" />
    </div>
    <div v-else class="space-y-4">
      <FormControl
        v-model="form.title"
        :label="t('list.title')"
        :placeholder="t('editor.topicTitlePlaceholder')"
        required
        @keyup.enter="submit"
      />
      <div class="grid grid-cols-2 gap-4">
        <Select v-model="form.category" :label="t('field.category')" :options="categoryOptions" />
        <FormControl
          v-model.number="form.idx"
          :label="t('editor.topicOrder')"
          type="number"
          :min="0"
        />
      </div>
    </div>
  </Dialog>
</template>
