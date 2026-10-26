<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Dropdown,
  ErrorMessage,
  Skeleton,
  dialog,
  toast,
} from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { useListControls } from '@/shared/composables/useListControls'
import { statusLabel } from '@/shared/labels'

import { useUsersStore, type AdminUser } from '../store'

const router = useRouter()
const store = useUsersStore()
const { t } = useI18n()

const empty = computed(() => !store.loading && store.items.length === 0)

const columns = {
  base: ['minmax(0,1fr)', '6rem', '6rem'],
  md: ['minmax(0,1fr)', 'minmax(0,1fr)', '5rem', '6rem', '6rem'],
  lg: ['minmax(0,1fr)', 'minmax(0,1fr)', '5rem', '5rem', '6rem', '6rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  setPage: (page) => {
    store.page = page
  },
  fetch: (query) => {
    store.list({ q: query.search || undefined, page: store.page, perPage: query.perPage })
  },
})

function rowActions(item: AdminUser) {
  return [
    {
      label: t('list.edit'),
      icon: 'lucide-pencil',
      onClick: () => router.push({ name: 'UserEdit', params: { id: item.id } }),
    },
    { label: t('list.delete'), icon: 'lucide-trash-2', onClick: () => onDelete(item) },
  ]
}

function openRow(item: AdminUser) {
  router.push({ name: 'UserDetail', params: { id: item.id } })
}

async function onDelete(item: AdminUser) {
  dialog.danger({
    title: t('users.deleteTitle'),
    message: t('users.deleteMessage', { name: item.fullName }),
    onConfirm: async () => {
      const ok = await store.remove(item.id)
      if (!ok) throw new Error(store.error || t('users.deleteFailed'))
      toast.success(t('users.deletedToast'))
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
        variant="solid"
        icon-left="lucide-plus"
        :label="t('users.addUser')"
        :route="{ name: 'UserNew' }"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-plus"
        :label="t('users.addUser')"
        :route="{ name: 'UserNew' }"
      />
    </template>
  </AppPageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('users.searchPlaceholder')"
    />

    <div>
      <div v-if="store.loading" class="space-y-2">
        <Skeleton v-for="i in 6" :key="i" class="h-9" />
      </div>

      <div v-else-if="empty" class="flex flex-col items-center gap-2 py-10 text-center">
        <span class="lucide-users size-8 text-ink-gray-4" aria-hidden="true" />
        <p class="text-p-sm text-ink-gray-5">{{ t('users.noData') }}</p>
        <Button
          variant="outline"
          theme="gray"
          icon-left="lucide-plus"
          :label="t('users.addUser')"
          :route="{ name: 'UserNew' }"
        />
      </div>

      <List v-else :row-height="40" :columns="columns" class="list-row-px-3">
        <ListHead>
          <ListHeaderCell>{{ t('list.name') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.email') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('users.role') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.status') }}</ListHeaderCell>
          <ListHeaderCell class="max-lg:hidden">{{ t('users.created') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.actions') }}</ListHeaderCell>
        </ListHead>
        <ListRows :items="store.items" v-slot="{ item }">
          <ListRow :value="item.id" @click="openRow(item)">
            <ListCell>
              <span class="truncate text-base-medium text-ink-gray-8">{{ item.fullName }}</span>
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="truncate text-p-sm text-ink-gray-5">{{ item.email }}</span>
            </ListCell>
            <ListCell>
              <Badge :label="item.appRole" variant="subtle" />
            </ListCell>
            <ListCell class="max-md:hidden">
              <Badge
                :label="statusLabel(item.isActive ? 'Active' : 'Inactive')"
                :theme="item.isActive ? 'green' : 'gray'"
                variant="subtle"
              />
            </ListCell>
            <ListCell class="max-lg:hidden">
              <span class="text-p-sm text-ink-gray-5">
                {{ item.createdOn ? new Date(item.createdOn).toLocaleDateString() : '—' }}
              </span>
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
