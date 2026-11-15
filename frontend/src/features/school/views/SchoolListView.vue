<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, Combobox, FormControl, Spinner, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import { cityOptions, fetchCities } from '@/shared/masters'
import { useSchoolStore, type School } from '../store'

const store = useSchoolStore()
const { t } = useI18n()

const search = ref('')
const page = ref(1)
const perPage = ref(20)
const gateReady = ref(false)
const creating = ref(false)
const newName = ref('')
const newCityId = ref<string | null>(null)
const saving = ref(false)
const renamingId = ref<string | null>(null)
const renameValue = ref('')
const renameCityId = ref<string | null>(null)
const renamingActive = ref(false)

const citySelect = ref<{ label: string; value: string }[]>([])

const columns = {
  base: ['minmax(0,1fr)', 'minmax(0,1fr)', '6rem', '8rem'],
  md: ['minmax(0,1fr)', 'minmax(0,1fr)', '7rem', '9rem'],
}

const empty = computed(() => !store.loading && store.items.length === 0)

const totalRows = computed(() => store.items.length)
const pagedItems = computed(() => {
  const start = (page.value - 1) * perPage.value
  return store.items.slice(start, start + perPage.value)
})

let searchTimer: number | null = null

async function reload() {
  await store.list({ search: search.value.trim() || undefined })
}

watch(search, () => {
  page.value = 1
  if (searchTimer !== null) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    searchTimer = null
    void reload()
  }, 300)
})

watch(perPage, () => {
  page.value = 1
})

watch(totalRows, (n) => {
  const maxPage = Math.max(1, Math.ceil(n / perPage.value))
  if (page.value > maxPage) page.value = maxPage
})

async function onCreate() {
  const name = newName.value.trim()
  if (!name || !newCityId.value || saving.value) return
  saving.value = true
  const created = await store.create({ name, cityId: newCityId.value })
  saving.value = false
  if (created) {
    newName.value = ''
    newCityId.value = null
    creating.value = false
    toast.success(t('schools.createdToast'))
  } else {
    toast.error(store.error || t('schools.saveFailed'))
  }
}

function startEdit(item: School) {
  renamingId.value = item.id
  renameValue.value = item.name
  renameCityId.value = item.cityId ?? item.city?.id ?? null
}

async function saveEdit() {
  const id = renamingId.value
  if (!id || renamingActive.value) return
  if (!renameValue.value.trim() || !renameCityId.value) return
  renamingActive.value = true
  const updated = await store.update(id, {
    name: renameValue.value.trim(),
    cityId: renameCityId.value,
  })
  renamingActive.value = false
  if (updated) {
    renamingId.value = null
    toast.success(t('schools.updatedToast'))
  } else {
    toast.error(store.error || t('schools.saveFailed'))
  }
}

async function toggleActive(item: School) {
  if (store.saving) return
  if (renamingId.value === item.id) return
  const updated = await store.update(item.id, { isActive: !item.isActive })
  if (updated) {
    toast.success(t(item.isActive ? 'schools.deactivatedToast' : 'schools.activatedToast'))
  } else {
    toast.error(store.error || t('schools.saveFailed'))
  }
}

onMounted(async () => {
  try {
    const cities = await fetchCities()
    citySelect.value = cityOptions(cities)
  } catch {
    citySelect.value = []
    toast.error(t('schools.citiesLoadFailed'))
  }
  try {
    await reload()
  } finally {
    gateReady.value = true
  }
})
</script>

<template>
  <AppPageHeader :title="t('nav.schools')">
    <template #actions>
      <Button variant="solid" theme="gray" icon-left="lucide-plus" :label="t('schools.add')" @click="creating = !creating" />
    </template>
    <template #mobile-actions>
      <Button variant="ghost" theme="gray" icon="lucide-plus" :label="t('schools.add')" @click="creating = !creating" />
    </template>
  </AppPageHeader>

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <form
      v-if="creating"
      class="flex flex-col gap-2 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-4 sm:flex-row sm:items-end"
      @submit.prevent="onCreate"
    >
      <FormControl v-model="newName" :label="t('schools.name')" :placeholder="t('schools.namePlaceholder')" required autofocus />
      <Combobox
        v-model="newCityId"
        class="min-w-56"
        :label="t('schools.city')"
        :options="citySelect"
        :placeholder="t('schools.cityPlaceholder')"
        :required="true"
      />
      <Button type="submit" variant="solid" theme="gray" icon-left="lucide-check" :label="t('shared.save')" :loading="saving" />
      <Button type="button" variant="outline" theme="gray" :label="t('shared.cancel')" @click="creating = false" />
    </form>

    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('schools.searchPlaceholder')"
    />

    <div>
      <ListState
        :loading="store.loading"
        :error="store.error"
        :empty="empty"
        icon="lucide-school"
        :empty-message="t('schools.noData')"
      >
        <template #action>
          <Button variant="outline" theme="gray" icon-left="lucide-plus" :label="t('schools.add')" @click="creating = true" />
        </template>
        <List :row-height="40" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>{{ t('schools.name') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('schools.city') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('list.status') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('list.actions') }}</ListHeaderCell>
          </ListHead>
          <ListRows :items="pagedItems" v-slot="{ item }">
            <ListRow :value="item.id">
              <ListCell>
                <form v-if="renamingId === item.id" class="flex items-center gap-1" @submit.prevent="saveEdit">
                  <FormControl v-model="renameValue" class="min-w-0 flex-1" autofocus />
                  <Button type="submit" variant="ghost" theme="gray" icon="lucide-check" :label="t('shared.save')" :loading="renamingActive" />
                  <Button type="button" variant="ghost" theme="gray" icon="lucide-x" :label="t('shared.cancel')" @click="renamingId = null" />
                </form>
                <span v-else class="truncate text-base-medium text-ink-gray-8">{{ item.name }}</span>
              </ListCell>
              <ListCell>
                <Combobox
                  v-if="renamingId === item.id"
                  v-model="renameCityId"
                  :options="citySelect"
                  :placeholder="t('schools.cityPlaceholder')"
                  :required="true"
                />
                <span v-else class="truncate text-p-sm text-ink-gray-6">{{ item.city?.name ?? '—' }}</span>
              </ListCell>
              <ListCell>
                <Badge :label="item.isActive ? t('status.active') : t('status.inactive')" :theme="item.isActive ? 'green' : 'gray'" variant="subtle" />
              </ListCell>
              <ListCell>
                <div class="flex items-center gap-1">
                  <Button variant="ghost" theme="gray" icon="lucide-pencil" :label="t('list.edit')" @click="startEdit(item)" />
                  <Button
                    variant="ghost"
                    :theme="item.isActive ? 'red' : 'green'"
                    :icon="item.isActive ? 'lucide-eye-off' : 'lucide-eye'"
                    :label="item.isActive ? t('schools.deactivate') : t('schools.activate')"
                    @click="toggleActive(item)"
                  />
                </div>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </ListState>

      <ListFoot
        v-if="!store.loading && !store.error && !empty"
        :total="totalRows"
        :page="page"
        :per-page="perPage"
        @update:page="page = $event"
      />
    </div>
  </div>
</template>
