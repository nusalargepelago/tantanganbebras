<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, Spinner } from 'frappe-ui'
import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import {
  List,
  ListCell,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'

import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { useListControls } from '@/shared/composables/useListControls'

import { useAuthStore } from '@/features/auth/store'
import { useAccountStore, type AdminUser } from '../store'
import UserFormDialog from './UserFormDialog.vue'

const store = useAccountStore()
const auth = useAuthStore()
const { t } = useI18n()

const gateReady = computed(() => auth.checked)

const empty = computed(
  () => !store.loading && store.items.length === 0,
)

const columns = {
  base: ['minmax(0,1fr)', '6rem', '6.5rem', '3rem'],
  md: ['minmax(0,2fr)', '6rem', 'minmax(0,1.5fr)', '6.5rem', '3rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  setPage: (page) => {
    store.page = page
  },
  fetch: (query) => {
    store.fetchUsers({
      search: query.search,
      page: store.page,
      perPage: query.perPage,
    })
  },
})

const editOpen = ref(false)
const editing = ref<AdminUser | null>(null)

function openEdit(user: AdminUser) {
  editing.value = user
  editOpen.value = true
}

function openCreate() {
  editing.value = null
  editOpen.value = true
}

onMounted(async () => {
  if (!auth.checked) await auth.fetchMe()
  refresh()
})
</script>

<template>
  <AppPageHeader>
    <template #default>
      <Button
        variant="solid"
        icon-left="lucide-user-plus"
        :label="t('account.addUser')"
        @click="openCreate"
      />
    </template>
    <template #suffix>
      <Button
        variant="ghost"
        theme="gray"
        icon="lucide-user-plus"
        :label="t('account.addUser')"
        @click="openCreate"
      />
    </template>
  </AppPageHeader>

  <Spinner v-if="!gateReady" />

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('account.searchUsers')"
    />

    <div>
      <ListState
        :loading="store.loading"
        :error="store.error"
        :empty="empty"
        icon="lucide-users"
        :empty-message="search ? t('account.noUsersFound') : t('account.noUsers')"
      >
        <List :row-height="32" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>{{ t('account.columns.user') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('account.columns.appRole') }}</ListHeaderCell>
            <ListHeaderCell class="max-md:hidden">
              {{ t('account.columns.roles') }}
            </ListHeaderCell>
            <ListHeaderCell>{{ t('account.columns.status') }}</ListHeaderCell>
            <ListHeaderCell class="sr-only">
              {{ t('account.columns.actions') }}
            </ListHeaderCell>
          </ListHead>

          <ListRows :items="store.items" v-slot="{ item }">
            <ListRow :value="item.id" @click="openEdit(item)">
              <ListCell>
                <div class="flex min-w-0 items-center gap-2">
                  <span class="truncate text-base-medium text-ink-gray-8">
                    {{ item.fullName || item.username }}
                  </span>
                  <span class="truncate text-p-sm text-ink-gray-5">
                    {{ item.email }}
                  </span>
                </div>
              </ListCell>
              <ListCell>
                <Badge
                  :label="item.appRole ?? 'â€”'"
                  :theme="item.appRole === 'admin' ? 'blue' : 'gray'"
                  variant="subtle"
                />
              </ListCell>
              <ListCell class="max-md:hidden">
                <span class="truncate text-p-sm text-ink-gray-5">
                  {{ item.roles.length ? item.roles.join(', ') : 'â€”' }}
                </span>
              </ListCell>
              <ListCell>
                <Badge
                  :label="item.isActive ? t('account.statusActive') : t('account.statusInactive')"
                  :theme="item.isActive ? 'green' : 'gray'"
                  variant="subtle"
                />
              </ListCell>
              <ListCell>
                <Button
                  variant="ghost"
                  theme="gray"
                  icon="lucide-pencil"
                  :label="t('account.editUser')"
                  @click="openEdit(item)"
                />
              </ListCell>
            </ListRow>
          </ListRows>
          </List>
      </ListState>

      <ListFoot
        v-if="!store.loading && !store.error && !empty"
        :total="store.total"
        :page="store.page"
        :per-page="store.perPage"
        @update:page="goToPage"
      />
    </div>
  </div>

  <UserFormDialog v-model:open="editOpen" :user="editing" @saved="refresh" />
</template>
