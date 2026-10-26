<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
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
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { useListControls } from '@/shared/composables/useListControls'
import { useI18n } from 'vue-i18n'

import { useStudentStore, type Student } from '../store'
import { categoryLabel, categoryOptions, statusLabel, statusOptions } from '@/shared/labels'

const router = useRouter()
const store = useStudentStore()
const { t } = useI18n()

const category = ref('')
const status = ref('')
const includeDisabled = ref(false)

const empty = computed(() => !store.loading && store.items.length === 0)
const categoryFilter = computed(() => categoryOptions(true))
const statusFilter = computed(() => statusOptions(true))

const columns = {
  base: ['minmax(0,1fr)', '5.5rem', '2.5rem'],
  md: ['minmax(0,1fr)', 'minmax(0,1fr)', '5rem', '5rem', '5rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  setPage: (page) => {
    store.page = page
  },
  fetch: (query) => {
    store.list({
      q: query.search || undefined,
      category: category.value || undefined,
      status: status.value || undefined,
      includeDisabled: includeDisabled.value,
      page: store.page,
      perPage: query.perPage,
    })
  },
})

watch([category, status, includeDisabled], () => {
  store.page = 1
  refresh()
})

function rowActions(item: Student) {
  const actions = [
    {
      label: t('list.edit'),
      icon: 'lucide-pencil',
      onClick: () => router.push({ name: 'StudentEdit', params: { userId: item.userId } }),
    },
  ]
  if (item.status === 'Inactive' && !item.disabled) {
    actions.unshift({
      label: t('list.activate'),
      icon: 'lucide-circle-check',
      onClick: () => onActivate(item),
    })
  }
  if (item.disabled) {
    actions.push({ label: t('list.restore'), icon: 'lucide-rotate-ccw', onClick: () => onRestore(item) })
    actions.push({ label: t('list.purge'), icon: 'lucide-trash-2', onClick: () => onPurge(item) })
  } else {
    actions.push({ label: t('list.delete'), icon: 'lucide-trash-2', onClick: () => onDelete(item) })
  }
  return actions
}

function openRow(item: Student) {
  router.push({ name: 'StudentDetail', params: { userId: item.userId } })
}

async function onActivate(item: Student) {
  const updated = await store.activate(item.userId)
  if (!updated) {
    toast.error(store.error || t('student.activateFailed'))
    return
  }
  toast.success(t('student.activatedToast'))
  refresh()
}

async function onDelete(item: Student) {
  dialog.danger({
    title: t('student.deleteTitle'),
    message: t('student.deleteMessage', { name: `${item.firstName} ${item.lastName}` }),
    onConfirm: async () => {
      const ok = await store.softDelete(item.userId)
      if (!ok) throw new Error(store.error || t('student.deleteFailed'))
      toast.success(t('student.deletedToast'))
      refresh()
    },
  })
}

async function onRestore(item: Student) {
  const updated = await store.restore(item.userId)
  if (!updated) {
    toast.error(store.error || t('student.restoreFailed'))
    return
  }
  toast.success(t('student.restoreToast'))
  refresh()
}

async function onPurge(item: Student) {
  dialog.danger({
    title: t('student.purgeTitle'),
    message: t('student.purgeMessage', { name: `${item.firstName} ${item.lastName}` }),
    onConfirm: async () => {
      const ok = await store.purge(item.userId)
      if (!ok) throw new Error(store.error || t('student.purgeFailed'))
      toast.success(t('student.purgedToast'))
      refresh()
    },
  })
}

onMounted(refresh)
</script>

<template>
  <AppPageHeader>
    <template #actions>
      <Button
        variant="outline"
        theme="gray"
        icon-left="lucide-upload"
        :label="t('student.import')"
        :route="{ name: 'StudentImport' }"
      />
      <Button
        variant="solid"
        icon-left="lucide-plus"
        :label="t('student.addStudent')"
        :route="{ name: 'StudentNew' }"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-upload"
        :label="t('student.import')"
        :route="{ name: 'StudentImport' }"
      />
      <Button
        variant="ghost"
        icon="lucide-plus"
        :label="t('student.addStudent')"
        :route="{ name: 'StudentNew' }"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('student.searchPlaceholder')"
    >
      <Select v-model="category" :options="categoryFilter" class="w-32 max-sm:flex-1 sm:flex-1 sm:min-w-[5rem]" />
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

      <div v-else-if="empty" class="flex flex-col items-center gap-2 py-10 text-center">
        <span class="lucide-users size-8 text-ink-gray-4" aria-hidden="true" />
        <p class="text-p-sm text-ink-gray-5">
          {{
            search || category || status
              ? t('student.noMatch')
              : t('student.noData')
          }}
        </p>
        <Button
          v-if="!search && !category && !status"
          variant="outline"
          theme="gray"
          icon-left="lucide-plus"
          :label="t('student.addStudent')"
          :route="{ name: 'StudentNew' }"
        />
      </div>

      <List v-else :row-height="40" :columns="columns" class="list-row-px-3">
        <ListHead>
          <ListHeaderCell>{{ t('list.name') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.school') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.category') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.status') }}</ListHeaderCell>
          <ListHeaderCell>
            <span class="max-md:hidden">{{ t('list.actions') }}</span>
          </ListHeaderCell>
        </ListHead>
        <ListRows :items="store.items" v-slot="{ item }">
          <ListRow :value="item.userId" @click="openRow(item)">
            <ListCell>
              <div class="flex min-w-0 flex-col">
                <span class="truncate text-base-medium text-ink-gray-8">
                  {{ item.firstName }} {{ item.lastName }}
                </span>
                <span class="truncate text-p-xs text-ink-gray-5">{{ item.username }}</span>
              </div>
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="truncate text-p-sm text-ink-gray-5">{{ item.school || '—' }}</span>
            </ListCell>
            <ListCell>
              <Badge :label="categoryLabel(item.category)" variant="subtle" />
            </ListCell>
            <ListCell class="max-md:hidden">
              <Badge
                v-if="item.disabled"
                :label="t('list.deleted')"
                theme="red"
                variant="subtle"
              />
              <Badge
                v-else
                :label="statusLabel(item.status)"
                :theme="item.status === 'Active' ? 'green' : 'amber'"
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
