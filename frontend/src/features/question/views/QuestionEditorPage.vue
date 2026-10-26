<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, dialog, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useQuestionStore } from '../store'
import { categoryLabel, difficultyLabel, statusLabel } from '@/shared/labels'
import { stripTags } from '@/shared/richText'
import QuestionEditor from '../components/QuestionEditor.vue'
import QuestionOutline from '../components/QuestionOutline.vue'
import TopicModal from '../components/TopicModal.vue'
import type { Category } from '../store'

const route = useRoute()
const router = useRouter()
const store = useQuestionStore()
const { t } = useI18n()

const selected = computed(() => (route.query.question as string) || '')
const question = computed(() => store.current)

const topicModalOpen = ref(false)
const topicModalCategory = ref<Category>('cub')
const topicModalName = ref<string | null>(null)

const outlineOpen = ref(false)
const settingsOpen = ref(false)

function closeDrawers() {
  outlineOpen.value = false
  settingsOpen.value = false
}

function toggleOutline() {
  settingsOpen.value = false
  outlineOpen.value = !outlineOpen.value
}

function toggleSettings() {
  outlineOpen.value = false
  settingsOpen.value = !settingsOpen.value
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') closeDrawers()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

const settings = computed(() => {
  const q = question.value
  if (!q) return []
  const topic = store.topics.find((t) => t.name === q.topicId)
  return [
    { label: t('field.topic'), value: topic?.title ?? t('editor.noValue') },
    { label: t('field.category'), value: categoryLabel(q.category) },
    { label: t('field.type'), value: q.questionType },
    { label: t('field.difficulty'), value: difficultyLabel(q.difficultyLevel) },
    { label: t('field.status'), value: statusLabel(q.status) },
    {
      label: t('editor.lengthLabel'),
      value: t('editor.lengthValue', {
        n: stripTags(q.question).length + stripTags(q.description).length,
      }),
    },
  ]
})

function selectQuestion(name: string) {
  outlineOpen.value = false
  router.replace({ query: { question: name } })
}

function openAddTopic(category: string) {
  topicModalCategory.value = category as Category
  topicModalName.value = null
  topicModalOpen.value = true
}

function openEditTopic(name: string) {
  topicModalName.value = name
  topicModalOpen.value = true
}

function onDeleteTopic(name: string) {
  dialog.danger({
    title: t('editor.deleteTopic'),
    message: t('editor.deleteTopicMessage'),
    onConfirm: async () => {
      const ok = await store.deleteTopic(name)
      if (!ok) throw new Error(store.error || 'Failed to delete topic')
      toast.success(t('editor.topicDeletedToast'))
      await store.listTopics()
      await store.list({ perPage: 200 })
    },
  })
}

function onDeleteQuestion(name: string) {
  dialog.danger({
    title: t('question.deleteTitle'),
    message: t('question.deleteQuestionMessage'),
    onConfirm: async () => {
      const ok = await store.softDelete(name)
      if (!ok) throw new Error(store.error || 'Failed to delete question')
      toast.success(t('question.deletedToast'))
      if (selected.value === name) {
        router.replace({ query: {} })
      }
      await store.list({ perPage: 200 })
    },
  })
}

watch(selected, async (name) => {
  if (name) await store.get(name)
}, { immediate: true })
</script>

<template>
  <div class="flex h-full flex-col">
    <AppPageHeader :title="question?.questionCode || t('crumb.editor')">
      <template #actions>
        <div class="flex items-center gap-2 lg:hidden">
          <Button
            variant="outline"
            theme="gray"
            icon="lucide-panel-left"
            :label="t('editor.outline')"
            :aria-expanded="outlineOpen"
            @click="toggleOutline"
          />
          <Button
            variant="outline"
            theme="gray"
            icon="lucide-settings-2"
            :label="t('form.settings')"
            :aria-expanded="settingsOpen"
            @click="toggleSettings"
          />
        </div>
        <Button
          variant="outline"
          theme="gray"
          icon-left="lucide-list"
          :label="t('editor.questionListBtn')"
          :route="{ name: 'QuestionList' }"
        />
      </template>
      <template #mobile-actions>
        <Button
          variant="ghost"
          icon="lucide-panel-left"
          :label="t('editor.outline')"
          :aria-expanded="outlineOpen"
          :data-state="outlineOpen ? 'active' : undefined"
          @click="toggleOutline"
        />
        <Button
          variant="ghost"
          icon="lucide-settings-2"
          :label="t('form.settings')"
          :aria-expanded="settingsOpen"
          :data-state="settingsOpen ? 'active' : undefined"
          @click="toggleSettings"
        />
        <Button
          variant="ghost"
          icon="lucide-list"
          :label="t('editor.questionListBtn')"
          :route="{ name: 'QuestionList' }"
        />
      </template>
    </AppPageHeader>

    <div
      class="grid h-[calc(100vh-8rem)] grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)_320px]"
    >
      <aside
        class="fixed inset-y-0 left-0 z-40 flex w-[300px] max-w-[85vw] flex-col border-r border-outline-gray-1 bg-surface-elevation-2 shadow-xl transition-transform duration-200 lg:static lg:z-auto lg:h-full lg:w-auto lg:max-w-none lg:translate-x-0 lg:shadow-none lg:transition-none lg:bg-transparent"
        :class="outlineOpen ? 'translate-x-0' : 'invisible -translate-x-full lg:visible'"
      >
        <QuestionOutline
          :active-question="selected"
          @select="selectQuestion"
          @add-topic="openAddTopic"
          @edit-topic="openEditTopic"
          @delete-topic="onDeleteTopic"
          @delete-question="onDeleteQuestion"
        />
      </aside>

      <main class="min-h-0 overflow-hidden">
        <QuestionEditor v-if="selected" :question-name="selected" />
        <div
          v-else
          class="flex h-full flex-col items-center justify-center gap-2 p-8 text-center"
        >
          <span class="lucide-panel-left size-8 text-ink-gray-4" aria-hidden="true" />
          <p class="text-p-sm text-ink-gray-5">
            {{ t('editor.noQuestionSelected') }}
          </p>
        </div>
      </main>

      <aside
        class="fixed inset-y-0 right-0 z-40 flex w-[320px] max-w-[85vw] flex-col border-l border-outline-gray-1 bg-surface-elevation-2 shadow-xl transition-transform duration-200 lg:static lg:z-auto lg:h-full lg:w-auto lg:max-w-none lg:translate-x-0 lg:shadow-none lg:transition-none lg:bg-transparent"
        :class="settingsOpen ? 'translate-x-0' : 'invisible translate-x-full lg:visible'"
      >
        <div class="border-b border-outline-gray-1 px-4 py-3">
          <p class="text-base-medium text-ink-gray-8">{{ t('form.settings') }}</p>
        </div>
        <dl v-if="settings.length" class="space-y-3 overflow-y-auto p-4" style="max-height: calc(100vh - 12rem)">
          <div v-for="row in settings" :key="row.label">
            <dt class="text-p-xs text-ink-gray-5">{{ row.label }}</dt>
            <dd class="text-p-sm text-ink-gray-8">{{ row.value }}</dd>
          </div>
        </dl>
        <p v-else class="p-4 text-p-sm text-ink-gray-5">{{ t('editor.noSettingsSelected') }}</p>
      </aside>
    </div>

    <div
      v-if="outlineOpen || settingsOpen"
      class="fixed inset-0 z-30 bg-black/40 lg:hidden"
      aria-hidden="true"
      @click="closeDrawers"
    />

    <TopicModal
      v-model:open="topicModalOpen"
      :category="topicModalCategory"
      :topic-name="topicModalName"
      @saved="
        async () => {
          await store.listTopics()
          await store.list({ perPage: 200 })
        }
      "
    />
  </div>
</template>
