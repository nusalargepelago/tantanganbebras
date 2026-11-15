<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Checkbox,
  Dialog,
  FormControl,
  Select,
  Spinner,
  dialog as imperativeDialog,
  toast,
} from 'frappe-ui'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { useListControls } from '@/shared/composables/useListControls'

import { useTodosStore, type Todo } from '../store'

const store = useTodosStore()
const { t } = useI18n()

const completed = ref('')
const modalOpen = ref(false)
const editing = ref<Todo | null>(null)
const saving = ref(false)

const form = reactive({ title: '', description: '', completed: false, dueDate: '' })

const empty = computed(() => !store.loading && store.items.length === 0)
const gateReady = ref(false)

const completedFilter = computed(() => [
  { label: t('todos.allStatuses'), value: '' },
  { label: t('list.completed'), value: 'true' },
  { label: t('list.pending'), value: 'false' },
])

const columns = {
  base: ['minmax(0,1fr)', '6rem', '3rem'],
  md: ['minmax(0,1.5fr)', '6rem', '6rem', '7rem'],
  lg: ['minmax(0,1.5fr)', '6rem', '6rem', '7rem', '7rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  setPage: (page) => {
    store.page = page
  },
  fetch: (query) => {
    return store.list({
      search: query.search || undefined,
      completed: completed.value || undefined,
      page: store.page,
      perPage: query.perPage,
    })
  },
})

watch(completed, () => {
  store.page = 1
  refresh()
})

const canSave = computed(() => form.title.trim() !== '' && !saving.value)

function openCreate() {
  editing.value = null
  Object.assign(form, { title: '', description: '', completed: false, dueDate: '' })
  modalOpen.value = true
}

function openEdit(todo: Todo) {
  editing.value = todo
  Object.assign(form, {
    title: todo.title,
    description: todo.description ?? '',
    completed: todo.completed,
    dueDate: todo.dueDate ?? '',
  })
  modalOpen.value = true
}

async function onSave() {
  if (!canSave.value) return
  saving.value = true
  const payload = {
    title: form.title.trim(),
    description: form.description.trim() || null,
    completed: form.completed,
    dueDate: form.dueDate || null,
  }
  const saved = editing.value
    ? await store.update(editing.value.id, payload)
    : await store.create(payload)
  saving.value = false

  if (!saved) {
    toast.error(store.error || t('todos.saveFailed'))
    return
  }
  toast.success(
    editing.value
      ? t('todos.updatedToast', { title: payload.title })
      : t('todos.createdToast'),
  )
  modalOpen.value = false
  refresh()
}

async function onDelete(todo: Todo) {
  imperativeDialog.danger({
    title: t('todos.deleteTitle'),
    message: t('todos.deleteMessage', { title: todo.title }),
    onConfirm: async () => {
      const ok = await store.remove(todo.id)
      if (!ok) throw new Error(store.error || t('todos.deleteFailed'))
      toast.success(t('todos.deletedToast'))
      refresh()
    },
  })
}

onMounted(async () => {
  await refresh()
  gateReady.value = true
})
</script>

<template>
  <AppPageHeader>
    <template #actions>
      <Button
        variant="solid"
        icon-left="lucide-plus"
        :label="t('todos.add')"
        @click="openCreate"
      />
    </template>
    <template #mobile-actions>
      <Button
        variant="ghost"
        icon="lucide-plus"
        :label="t('todos.add')"
        @click="openCreate"
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
      :placeholder="t('todos.searchPlaceholder')"
    >
      <Select v-model="completed" :options="completedFilter" class="w-40 max-sm:flex-1" />
    </ListToolbar>

    <div>
      <ListState
        :loading="store.loading"
        :error="store.error"
        :empty="empty"
        icon="lucide-list-todo"
        :empty-message="t('todos.noData')"
      >
        <template #action>
          <Button variant="outline" theme="gray" icon-left="lucide-plus" :label="t('todos.add')" @click="openCreate" />
        </template>
        <List :row-height="40" :columns="columns" class="list-row-px-3">
        <ListHead>
          <ListHeaderCell>{{ t('list.title') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.status') }}</ListHeaderCell>
          <ListHeaderCell class="max-md:hidden">{{ t('list.dueDate') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('list.actions') }}</ListHeaderCell>
        </ListHead>
        <ListRows :items="store.items" v-slot="{ item }">
          <ListRow :value="item.id" @click="openEdit(item)">
            <ListCell>
              <span class="truncate text-base-medium text-ink-gray-8">{{ item.title }}</span>
            </ListCell>
            <ListCell>
              <Badge
                :label="item.completed ? t('list.completed') : t('list.pending')"
                :theme="item.completed ? 'green' : 'amber'"
                variant="subtle"
              />
            </ListCell>
            <ListCell class="max-md:hidden">
              <span class="text-p-sm text-ink-gray-5">
                {{ item.dueDate ? new Date(item.dueDate).toLocaleDateString() : '—' }}
              </span>
            </ListCell>
            <ListCell>
              <div class="flex items-center gap-1">
                <Button
                  variant="ghost"
                  theme="gray"
                  icon="lucide-pencil"
                  :label="t('list.edit')"
                  @click.stop="openEdit(item)"
                />
                <Button
                  variant="ghost"
                  theme="red"
                  icon="lucide-trash-2"
                  :label="t('list.delete')"
                  @click.stop="onDelete(item)"
                />
              </div>
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
      </ListState>
      <ListFoot
        v-if="!empty"
        :total="store.total"
        :page="store.page"
        :per-page="store.perPage"
        @update:page="goToPage"
      />
    </div>
  </div>

  <Dialog
    :open="modalOpen"
    :title="editing ? t('todos.editTitle') : t('todos.newTitle')"
    size="sm"
    :actions="[
      { label: t('shared.cancel'), variant: 'outline', theme: 'gray', onClick: ({ close }) => { close() } },
      { label: t('shared.save'), variant: 'solid', theme: 'gray', onClick: () => { onSave() } },
    ]"
    @update:open="modalOpen = $event"
  >
    <div class="space-y-4">
      <FormControl
        v-model="form.title"
        :label="t('list.title')"
        :placeholder="t('todos.titlePlaceholder')"
        required
      />
      <FormControl
        v-model="form.description"
        :label="t('todos.description')"
        :placeholder="t('todos.descPlaceholder')"
      />
      <Checkbox v-model="form.completed" :label="t('list.completed')" />
      <FormControl v-model="form.dueDate" type="date" :label="t('list.dueDate')" />
    </div>
  </Dialog>
</template>
