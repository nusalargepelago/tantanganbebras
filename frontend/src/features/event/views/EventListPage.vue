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
  toast,
} from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { categoryLabel, categoryOptions } from '@/shared/labels'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import { useAuthStore } from '@/features/auth/store'
import { useEventStudentStore } from '@/features/event-student/store'
import { useEventStore, type AdminEvent } from '../store'

const router = useRouter()
const auth = useAuthStore()
const store = useEventStore()
const { t } = useI18n()
const eventStudent = useEventStudentStore()

const search = ref('')
const perPage = ref(20)
const category = ref('')
const published = ref('')
const empty = computed(() => !store.loading && store.items.length === 0)
const canStart = computed(() => !!auth.student)

const filteredItems = computed(() => {
  const term = search.value.trim().toLowerCase()
  if (!term) return store.items
  return store.items.filter((e) => e.eventName.toLowerCase().includes(term))
})

const categoryFilter = computed(() => categoryOptions(true))
const publishedFilter = computed(() => [
  { label: t('list.all'), value: '' },
  { label: t('event.published'), value: 'true' },
  { label: t('event.draft'), value: 'false' },
])

const columns = {
  // Below md only name, status, and actions stay: the five-column layout did
  // not fit a 360px screen and pushed the page sideways.
  base: ['minmax(0,1fr)', '6.5rem', '2.5rem'],
  md: ['minmax(0,1fr)', '5rem', '4rem', '7rem', '7rem', '5rem', '3rem'],
  lg: ['minmax(0,1fr)', '5rem', '4rem', '7rem', '7rem', '5rem', '3rem'],
}

function reload() {
  store.list({
    category: category.value || undefined,
    published: published.value === '' ? undefined : published.value === 'true',
    page: store.page,
    perPage: perPage.value,
  })
}

function goToPage(page: number) {
  store.page = page
  reload()
}

watch([category, published], () => {
  store.page = 1
  reload()
})

watch(perPage, () => {
  store.page = 1
  reload()
})

function openRow(item: AdminEvent) {
  router.push({ name: 'EventDetail', params: { name: item.name } })
}

function rowActions(item: AdminEvent) {
  const actions = [
    {
      label: t('list.edit'),
      icon: 'lucide-pencil',
      onClick: () => router.push({ name: 'EventEdit', params: { name: item.name } }),
    },
  ]
  if (canStart.value) {
    actions.unshift({
      label: t('event.play'),
      icon: 'lucide-play',
      onClick: () => onPlay(item),
    })
  }
  return actions
}

async function onPlay(item: AdminEvent) {
  const attempt = await eventStudent.make(item.name)
  if (!attempt) {
    toast.error(eventStudent.error || 'Failed to start the event')
    return
  }
  toast.success(t('eventStudent.startedToast'))
  await router.push({ name: 'EventStudentRunner', params: { name: attempt.name } })
}

onMounted(reload)
</script>

<template>
  <AppPageHeader>
    <template #actions>
      <Button
        variant="outline"
        theme="gray"
        icon-left="lucide-users"
        :label="t('event.openStudent')"
        :route="{ name: 'EventStudentList' }"
      />
      <Button
        variant="solid"
        icon-left="lucide-plus"
        :label="t('event.createEvent')"
        :route="{ name: 'EventNew' }"
        data-tour="admin-event-create"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-users"
        :label="t('event.openStudent')"
        :route="{ name: 'EventStudentList' }"
      />
      <Button
        variant="ghost"
        icon="lucide-plus"
        :label="t('event.createEvent')"
        :route="{ name: 'EventNew' }"
        data-tour="admin-event-create"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('event.searchPlaceholder')"
    >
      <Select v-model="category" :options="categoryFilter" class="w-32 max-sm:flex-1" />
      <Select v-model="published" :options="publishedFilter" class="w-36 max-sm:flex-1" />
    </ListToolbar>

    <div data-tour="admin-event-list">
      <div v-if="store.loading" class="space-y-2">
        <Skeleton v-for="i in 6" :key="i" class="h-9" />
      </div>

      <div v-else-if="empty" class="flex flex-col items-center gap-2 py-10 text-center">
        <span class="lucide-calendar-x size-8 text-ink-gray-4" aria-hidden="true" />
        <p class="text-p-sm text-ink-gray-5">
          {{
            category || published || search
              ? t('event.noMatch')
              : t('event.noData')
          }}
        </p>
        <Button
          v-if="!category && !published && !search"
          variant="outline"
          theme="gray"
          icon-left="lucide-plus"
          :label="t('event.createEvent')"
          :route="{ name: 'EventNew' }"
        />
      </div>

      <List v-else :row-height="40" :columns="columns" class="list-row-px-3">
        <ListHead>
          <ListHeaderCell>{{ t('list.name') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.category') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('event.duration') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('event.deadline') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.status') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('event.questions') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.actions') }}</ListHeaderCell>
        </ListHead>
        <ListRows :items="filteredItems" v-slot="{ item }">
          <ListRow :value="item.name" @click="openRow(item)">
            <ListCell>
              <span class="truncate text-base-medium text-ink-gray-8">
                {{ item.eventName }}
              </span>
            </ListCell>
            <ListCell class="max-md:hidden">
              <Badge :label="categoryLabel(item.category)" variant="subtle" />
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="text-p-sm text-ink-gray-5">
                {{ t('event.minutesShort', { n: item.timeLimit }) }}
              </span>
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="text-p-sm text-ink-gray-5">
                {{ new Date(item.eventDeadline).toLocaleString() }}
              </span>
            </ListCell>
            <ListCell>
              <Badge
                :label="item.published ? t('event.published') : t('event.draft')"
                :theme="item.published ? 'green' : 'gray'"
                variant="subtle"
              />
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="text-p-sm text-ink-gray-8">{{ item.questionCount }}</span>
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
