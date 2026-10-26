<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Dropdown,
  ErrorMessage,
  Select,
  Skeleton,
  Switch,
  dialog,
  toast,
} from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import {
  List,
  ListCell,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'
import { useListControls } from '@/shared/composables/useListControls'

import { useQuestionStore, type Question } from '../store'
import { stripTags } from '@/shared/richText'
import {
  categoryLabel,
  categoryOptions,
  difficultyLabel,
  difficultyOptions,
  statusLabel,
  statusOptions,
} from '@/shared/labels'

const router = useRouter()
const store = useQuestionStore()
const { t } = useI18n()

const category = ref('')
const difficulty = ref('')
const status = ref('')
const includeDisabled = ref(false)

const empty = computed(() => !store.loading && store.items.length === 0)

const categoryFilter = computed(() => categoryOptions(true))
const difficultyFilter = computed(() => difficultyOptions(true))
const statusFilter = computed(() => statusOptions(true))

const columns = {
  base: ['minmax(0,1fr)', '5.5rem', '2.5rem'],
  md: ['minmax(0,1fr)', '6rem', '5rem', '5rem', '5rem'],
  lg: ['minmax(0,1.5fr)', '6rem', '5rem', '5rem', '5rem', '5rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  setPage: (page) => {
    store.page = page
  },
  fetch: (query) => {
    store.list({
      q: query.search || undefined,
      category: category.value || undefined,
      difficultyLevel: difficulty.value || undefined,
      status: status.value || undefined,
      includeDisabled: includeDisabled.value,
      page: store.page,
      perPage: query.perPage,
    })
  },
})

watch([category, difficulty, status, includeDisabled], () => {
  store.page = 1
  refresh()
})

function rowActions(item: Question) {
  const actions = [
    {
      label: t('list.edit'),
      icon: 'lucide-pencil',
      onClick: () => router.push({ name: 'QuestionEdit', params: { name: item.name } }),
    },
  ]
  if (item.disabled) {
    actions.push({
      label: t('list.restore'),
      icon: 'lucide-rotate-ccw',
      onClick: () => onRestore(item),
    })
    actions.push({
      label: t('list.purge'),
      icon: 'lucide-trash-2',
      onClick: () => onPurge(item),
    })
  } else {
    actions.push({
      label: t('list.delete'),
      icon: 'lucide-trash-2',
      onClick: () => onDelete(item),
    })
  }
  return actions
}

function openRow(item: Question) {
  router.push({ name: 'QuestionDetail', params: { name: item.name } })
}

async function onDelete(item: Question) {
  dialog.danger({
    title: t('question.deleteTitle'),
    message: t('question.deleteMessage', { code: item.questionCode }),
    onConfirm: async () => {
      const ok = await store.softDelete(item.name)
      if (!ok) throw new Error(store.error || t('question.deleteFailed'))
      toast.success(t('question.deletedToast'))
      refresh()
    },
  })
}

async function onRestore(item: Question) {
  const ok = await store.restore(item.name)
  if (!ok) {
    toast.error(store.error || t('question.restoreFailed'))
    return
  }
  toast.success(t('question.restoreToast'))
  refresh()
}

async function onPurge(item: Question) {
  dialog.danger({
    title: t('question.purgeTitle'),
    message: t('question.purgeMessage', { code: item.questionCode }),
    onConfirm: async () => {
      const ok = await store.purge(item.name)
      if (!ok) throw new Error(store.error || t('question.purgeFailed'))
      toast.success(t('question.purgedToast'))
      refresh()
    },
  })
}

onMounted(() => {
  store.fetchOptionList()
  refresh()
})
</script>

<template>
  <AppPageHeader>
    <template #actions>
      <Button
        variant="outline"
        theme="gray"
        icon-left="lucide-square-pen"
        :label="t('question.openEditor')"
        :route="{ name: 'QuestionEditor' }"
      />
      <Button
        variant="solid"
        icon-left="lucide-plus"
        :label="t('question.addQuestion')"
        :route="{ name: 'QuestionNew' }"
        data-tour="admin-question-add"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-square-pen"
        :label="t('question.openEditor')"
        :route="{ name: 'QuestionEditor' }"
      />
      <Button
        variant="ghost"
        icon="lucide-plus"
        :label="t('question.addQuestion')"
        :route="{ name: 'QuestionNew' }"
        data-tour="admin-question-add"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('question.searchPlaceholder')"
    >
      <Select v-model="category" :options="categoryFilter" class="w-32 max-sm:flex-1 sm:flex-1 sm:min-w-[5rem]" />
      <Select v-model="difficulty" :options="difficultyFilter" class="w-32 max-sm:flex-1 sm:flex-1 sm:min-w-[5rem]" />
      <Select v-model="status" :options="statusFilter" class="w-32 max-sm:flex-1 sm:flex-1 sm:min-w-[5rem]" />
      <div class="flex items-center gap-2">
        <span class="shrink-0 text-p-sm text-ink-gray-5">{{ t('list.deleted') }}</span>
        <Switch v-model="includeDisabled" />
      </div>
    </ListToolbar>

    <div>
      <div v-if="store.loading" class="space-y-2">
        <Skeleton v-for="i in 6" :key="i" class="h-9" />
      </div>

      <div
        v-else-if="empty"
        class="flex flex-col items-center gap-2 py-10 text-center"
      >
        <span class="lucide-file-question size-8 text-ink-gray-4" aria-hidden="true" />
        <p class="text-p-sm text-ink-gray-5">
          {{
            search || category || difficulty || status
              ? t('question.noMatch')
              : t('question.noData')
          }}
        </p>
        <Button
          v-if="!search && !category && !difficulty && !status"
          variant="outline"
          theme="gray"
          icon-left="lucide-plus"
          :label="t('question.addQuestion')"
          :route="{ name: 'QuestionNew' }"
        />
      </div>

      <List v-else :row-height="40" :columns="columns" class="list-row-px-3">
        <ListHead>
          <ListHeaderCell>{{ t('list.code') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.type') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.category') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.difficulty') }}</ListHeaderCell>
          <ListHeaderCell class="max-lg:hidden">{{ t('list.status') }}</ListHeaderCell>
          <ListHeaderCell>
            <span class="max-md:hidden">{{ t('list.actions') }}</span>
          </ListHeaderCell>
        </ListHead>
        <ListRows :items="store.items" v-slot="{ item }">
          <ListRow :value="item.name" @click="openRow(item)">
            <ListCell>
              <div class="flex min-w-0 flex-col">
                <span class="truncate text-base-medium text-ink-gray-8">
                  {{ item.questionCode }}
                </span>
                <span class="truncate text-p-xs text-ink-gray-5">
                  {{ stripTags(item.question).slice(0, 60) || t('list.emptyValue') }}
                </span>
              </div>
            </ListCell>
            <ListCell class="max-md:hidden">
              <Badge
                :label="item.questionType === 'Essay' ? t('list.essay') : 'MC'"
                :theme="item.questionType === 'Essay' ? 'blue' : 'gray'"
                variant="subtle"
              />
            </ListCell>
            <ListCell>
              <Badge :label="categoryLabel(item.category)" variant="subtle" />
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="text-p-sm text-ink-gray-5">{{ difficultyLabel(item.difficultyLevel) }}</span>
            </ListCell>
            <ListCell class="max-lg:hidden">
              <Badge
                v-if="item.disabled"
                :label="t('list.deleted')"
                theme="red"
                variant="subtle"
              />
              <Badge
                v-else
                :label="statusLabel(item.status)"
                :theme="item.status === 'Active' ? 'green' : 'gray'"
                variant="subtle"
              />
            </ListCell>
            <ListCell>
              <Dropdown :options="rowActions(item)" align="end">
                <Button variant="ghost" theme="gray" icon="lucide-more-horizontal" :label="t('list.actions')" />
              </Dropdown>
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
      <ListFoot
        v-if="!empty"
        :total="store.total"
        :page="store.page"
        :per-page="store.perPage"
        @update:page="goToPage"
      />
    </div>

    <ErrorMessage v-if="store.error" :message="store.error" />
  </div>
</template>
