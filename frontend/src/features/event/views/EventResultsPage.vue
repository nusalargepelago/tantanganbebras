<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Skeleton } from 'frappe-ui'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import ListHead from '@/shared/components/ListHead.vue'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import { useEventStore } from '../store'

const route = useRoute()
const store = useEventStore()
const { t } = useI18n()

const name = computed(() => route.params.name as string)
const rows = computed(() => store.results)
const empty = computed(() => !store.loading && rows.value.length === 0)

function shortId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}…` : id
}

const columns = {
  base: ['3rem', 'minmax(0,1fr)', '5rem'],
  md: ['3rem', 'minmax(0,1fr)', '5rem', '5rem'],
  lg: ['3rem', 'minmax(0,1fr)', '5rem', '6rem', '7rem'],
}

onMounted(() => store.fetchResults(name.value))
</script>

<template>
  <AppPageHeader />

  <div class="mx-auto w-full max-w-2xl space-y-4 px-5 py-6">
    <Skeleton v-if="store.loading" class="h-32" />
    <ErrorMessage v-else-if="store.error" :message="store.error" />

    <template v-else>
      <div class="space-y-4" data-tour="admin-event-results-table">
        <h1 class="text-2xl-semibold text-ink-gray-8">
          {{ t('route.EventResults.title') }}
        </h1>

        <p
          v-if="empty"
          class="rounded-6 border border-outline-gray-1 py-10 text-center text-p-sm text-ink-gray-5"
        >
          {{ t('event.resultsEmpty') }}
        </p>

        <List v-else :row-height="40" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>#</ListHeaderCell>
            <ListHeaderCell>{{ t('list.student') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('list.score') }}</ListHeaderCell>
            <ListHeaderCell class="max-md:hidden">{{ t('event.duration') }}</ListHeaderCell>
            <ListHeaderCell class="max-lg:hidden">{{ t('event.submitTime') }}</ListHeaderCell>
          </ListHead>
          <ListRows :items="rows" v-slot="{ item, index }">
            <ListRow :value="item.name">
              <ListCell>
                <span class="text-p-sm text-ink-gray-5">{{ index + 1 }}</span>
              </ListCell>
              <ListCell>
                <span class="truncate text-p-sm text-ink-gray-8">{{ shortId(item.studentId) }}</span>
              </ListCell>
              <ListCell>
                <Badge
                  :label="item.score != null ? String(item.score) : '—'"
                  :theme="item.score != null ? 'green' : 'gray'"
                  variant="subtle"
                />
              </ListCell>
              <ListCell class="max-md:hidden">
                <span class="text-p-sm text-ink-gray-5">
                  {{ item.timeLimit != null ? t('event.secondsShort', { n: item.timeLimit }) : '-' }}
                </span>
              </ListCell>
              <ListCell class="max-lg:hidden">
                <span class="text-p-sm text-ink-gray-5">
                  {{ item.finishedAt ? new Date(item.finishedAt).toLocaleString() : '—' }}
                </span>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </div>
    </template>

    <div class="flex gap-2">
      <Button
        variant="outline"
        theme="gray"
        :label="t('event.backToEvent')"
        :route="{ name: 'EventDetail', params: { name } }"
      />
    </div>
  </div>
</template>
