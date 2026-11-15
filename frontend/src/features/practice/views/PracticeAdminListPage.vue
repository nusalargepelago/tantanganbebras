<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Select,
  Spinner,
  Skeleton,
  toast,
  type DialogAction,
} from 'frappe-ui'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import { categoryLabel, categoryOptions } from '@/shared/labels'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import { useAuthStore } from '@/features/auth/store'
import { usePracticeStore, type Practice } from '../store'

const router = useRouter()
const store = usePracticeStore()
const { t } = useI18n()
const auth = useAuthStore()

const category = ref('')
const search = ref('')
const perPage = ref(20)
const settingsOpen = ref(false)
const minDraft = ref<number | string>(10)
const savingSettings = ref(false)
const empty = computed(() => !store.loading && store.adminItems.length === 0)
const gateReady = ref(false)

const columns = {
  base: ['minmax(0,1fr)', '5rem', '6rem'],
  md: ['minmax(0,1fr)', 'minmax(0,1fr)', '5rem', '5rem', '6rem'],
  lg: ['minmax(0,1fr)', 'minmax(0,1fr)', '5rem', '5rem', '5rem', '6rem'],
}

const categoryFilter = computed(() => categoryOptions(true))

// Search filters the current page client-side (the /practice endpoint has no
// query param); same approach as EventListPage.
const filteredItems = computed(() => {
  const term = search.value.trim().toLowerCase()
  if (!term) return store.adminItems
  return store.adminItems.filter((item) =>
    [item.studentName, item.studentEmail, item.studentSchool]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(term)),
  )
})

function reload() {
  return store.listAdmin({
    category: category.value || undefined,
    page: store.adminPage,
    perPage: perPage.value,
  })
}

function goToPage(page: number) {
  store.adminPage = page
  reload()
}

function openRow(item: Practice) {
  router.push({ name: 'PracticeAdminDetail', params: { name: item.name } })
}

function shortId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}…` : id
}

async function loadSettings() {
  const ok = await store.fetchSettings()
  if (ok && store.settings) minDraft.value = store.settings.minQuestions
}

async function onSave(close: () => void) {
  if (!store.settings || savingSettings.value || store.settingsLoading) return
  const value = Number(minDraft.value)
  if (!Number.isInteger(value) || value < 1) {
    toast.error(t('practice.settingsInvalid'))
    return
  }
  savingSettings.value = true
  const saved = await store.updateSettings(value)
  savingSettings.value = false
  if (!saved) {
    toast.error(store.settingsError || t('practice.settingsFailed'))
    return
  }
  toast.success(t('practice.settingsSaved'))
  close()
}

function submitSettings() {
  onSave(() => (settingsOpen.value = false))
}

const settingsActions = computed<DialogAction[]>(() => {
  const list: DialogAction[] = [
    { label: t('shared.cancel'), variant: 'outline', theme: 'gray', onClick: ({ close }: { close: () => void }) => close() },
  ]
  if (auth.isAdmin) {
    list.push({
      label: t('shared.save'),
      variant: 'solid',
      theme: 'gray',
      disabled: savingSettings.value || store.settingsLoading,
      onClick: ({ close }: { close: () => void }) => onSave(close),
    })
  }
  return list
})

watch(settingsOpen, (open) => {
  if (open) loadSettings()
})

watch(category, () => {
  store.adminPage = 1
  reload()
})

watch(perPage, () => {
  store.adminPage = 1
  reload()
})

onMounted(async () => {
  await reload()
  gateReady.value = true
})
</script>

<template>
  <AppPageHeader>
    <template #actions>
      <Button
        variant="outline"
        theme="gray"
        icon-left="lucide-users"
        :label="t('event.openStudent')"
        :route="{ name: 'StudentList' }"
      />
      <Button
        v-if="auth.isAdmin"
        variant="outline"
        theme="gray"
        icon-left="lucide-settings-2"
        :label="t('practice.settingsBtn')"
        data-tour="admin-practice-settings"
        @click="settingsOpen = true"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-users"
        :label="t('event.openStudent')"
        :route="{ name: 'StudentList' }"
      />
      <Button
        v-if="auth.isAdmin"
        variant="ghost"
        icon="lucide-settings-2"
        :label="t('practice.settingsBtn')"
        data-tour="admin-practice-settings"
        @click="settingsOpen = true"
      />
    </template>
  </AppPageHeader>

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('practice.searchPlaceholder')"
    >
      <Select v-model="category" :options="categoryFilter" class="w-32 max-sm:flex-1 sm:flex-1 sm:min-w-[5rem]" />
    </ListToolbar>

    <div data-tour="admin-practice-list">
      <ListState
        :loading="store.loading"
        :error="store.error"
        :empty="empty"
        icon="lucide-clipboard-list"
        :empty-message="category || search ? t('practice.noMatch') : t('practice.noData')"
      >
        <List :row-height="40" :columns="columns" class="list-row-px-3">
        <ListHead>
          <ListHeaderCell>{{ t('list.student') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.school') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.category') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.score') }}</ListHeaderCell>
          <ListHeaderCell class="max-lg:hidden">{{ t('list.date') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.status') }}</ListHeaderCell>
        </ListHead>
        <ListRows :items="filteredItems" v-slot="{ item }">
          <ListRow :value="item.name" @click="openRow(item)">
            <ListCell>
              <div class="flex min-w-0 flex-col">
                <span class="truncate text-base-medium text-ink-gray-8">
                  {{ item.studentName || shortId(item.studentId) }}
                </span>
                <span v-if="item.studentEmail" class="truncate text-p-xs text-ink-gray-5">
                  {{ item.studentEmail }}
                </span>
              </div>
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="truncate text-p-sm text-ink-gray-5">
                {{ item.studentSchool || '—' }}
              </span>
            </ListCell>
            <ListCell>
              <Badge :label="categoryLabel(item.category)" variant="subtle" />
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="text-p-sm text-ink-gray-8">{{ item.score ?? '—' }}</span>
            </ListCell>
            <ListCell class="max-lg:hidden">
              <span class="text-p-sm text-ink-gray-5">
                {{ item.createdAt ? new Date(item.createdAt).toLocaleDateString() : '—' }}
              </span>
            </ListCell>
            <ListCell>
              <Badge
                :label="item.finishedAt ? t('list.completed') : t('list.inProgress')"
                :theme="item.finishedAt ? 'green' : 'amber'"
                variant="subtle"
              />
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
      </ListState>
      <ListFoot
        v-if="!empty"
        :total="store.adminTotal"
        :page="store.adminPage"
        :per-page="perPage"
        @update:page="goToPage"
      />
    </div>

    <Dialog v-model:open="settingsOpen" :title="t('practice.settingsTitle')" size="sm" :actions="settingsActions">
      <div v-if="store.settingsLoading" class="space-y-3">
        <Skeleton class="h-10" />
        <Skeleton class="h-10" />
      </div>
      <div v-else class="space-y-4">
        <p class="text-p-sm text-ink-gray-5">
          {{ t('practice.settingsDesc') }}
        </p>
        <FormControl
          v-if="auth.isAdmin"
          v-model.number="minDraft"
          type="number"
          :min="1"
          :label="t('practice.questionsPerPractice')"
          required
          @keyup.enter="submitSettings"
        />
        <div v-else class="rounded-6 border border-outline-gray-1 bg-surface-gray-2 p-4">
          <div class="text-p-xs text-ink-gray-5">{{ t('practice.questionsPerPractice') }}</div>
          <div class="text-xl-semibold text-ink-gray-8">{{ store.settings?.minQuestions ?? '—' }}</div>
          <div class="mt-1 text-p-xs text-ink-gray-5">{{ t('practice.onlyAdmins') }}</div>
        </div>
        <ErrorMessage v-if="store.settingsError" :message="store.settingsError" />
      </div>
    </Dialog>
  </div>
</template>
