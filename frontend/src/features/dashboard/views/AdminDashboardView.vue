<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, ErrorMessage, Skeleton } from 'frappe-ui'
import { BarChart, DonutChart, NumberCard } from 'frappe-ui/charts'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { categoryLabel, statusLabel } from '@/shared/labels'

import { useDashboardStore, type SchoolCount } from '../store'

const router = useRouter()
const store = useDashboardStore()
const { t } = useI18n()

const TOP_SCHOOLS = 10

const flatChartOptions = { animation: false }

const cards = computed(() => {
  const c = store.admin?.counts
  if (!c) return []
  return [
    { label: t('dash.admin.attempts24'), value: c.eventStudentToday },
    { label: t('dash.admin.activeEvents'), value: c.eventActive },
    { label: t('dash.admin.activeStudents'), value: c.studentActive },
    { label: t('dash.admin.inactiveStudents'), value: c.studentInactive },
  ]
})

const schoolRows = computed<SchoolCount[]>(() => {
  const rows = store.stats?.schools ?? []
  if (rows.length <= TOP_SCHOOLS) return rows
  const rest = rows.slice(TOP_SCHOOLS).reduce((sum, row) => sum + row.count, 0)
  return [...rows.slice(0, TOP_SCHOOLS), { school: t('dash.admin.others'), count: rest }]
})

const categoryStats = computed(() =>
  (store.stats?.categories ?? []).map((row) => ({
    ...row,
    category: categoryLabel(row.category),
  })),
)

const registrationRows = computed(() =>
  (store.stats?.registrations ?? []).map((row) => ({
    ...row,
    year: String(row.year),
  })),
)

onMounted(() => {
  store.fetchAdmin()
  store.fetchStats()
})
</script>

<template>
  <AppPageHeader :title="t('nav.dashboard')" />

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ErrorMessage v-if="store.error" :message="store.error" />

    <div v-if="store.loading" class="grid gap-4 md:grid-cols-2">
      <Skeleton v-for="i in 2" :key="i" class="h-40" />
    </div>

    <template v-else-if="store.admin">
      <div class="grid gap-4 md:grid-cols-2" data-tour="admin-recent">
        <section class="min-w-0 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
          <h2 class="text-xl-semibold text-ink-gray-8">{{ t('dash.admin.recentEvents') }}</h2>
          <p v-if="!store.admin.recentEvents.length" class="mt-2 text-p-sm text-ink-gray-5">
            {{ t('dash.admin.noEvents') }}
          </p>
          <ul v-else class="mt-2 space-y-2">
            <li
              v-for="event in store.admin.recentEvents"
              :key="event.name"
              class="flex cursor-pointer items-center justify-between gap-2 rounded-4 px-2 py-1 hover:bg-surface-gray-2"
              @click="router.push({ name: 'EventDetail', params: { name: event.name } })"
            >
              <span class="min-w-0 flex-1 truncate text-p-sm text-ink-gray-8">
                {{ event.eventName }}
              </span>
              <Badge :label="categoryLabel(event.category)" variant="subtle" class="shrink-0" />
            </li>
          </ul>
        </section>

        <section class="min-w-0 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
          <h2 class="text-xl-semibold text-ink-gray-8">{{ t('dash.admin.recentStudents') }}</h2>
          <p v-if="!store.admin.recentStudents.length" class="mt-2 text-p-sm text-ink-gray-5">
            {{ t('dash.admin.noStudents') }}
          </p>
          <ul v-else class="mt-2 space-y-2">
            <li
              v-for="student in store.admin.recentStudents"
              :key="student.userId"
              class="flex cursor-pointer items-center justify-between gap-2 rounded-4 px-2 py-1 hover:bg-surface-gray-2"
              @click="router.push({ name: 'StudentDetail', params: { userId: student.userId } })"
            >
              <div class="min-w-0 flex-1">
                <p class="truncate text-p-sm text-ink-gray-8">
                  {{ student.firstName }} {{ student.lastName }}
                </p>
                <p class="truncate text-p-xs text-ink-gray-5">{{ student.email }}</p>
              </div>
              <Badge
                :label="statusLabel(student.status)"
                :theme="student.status === 'Active' ? 'green' : 'amber'"
                variant="subtle"
                class="shrink-0"
              />
            </li>
          </ul>
        </section>
      </div>
    </template>

    <section class="space-y-4" data-tour="admin-stats">
      <h2 class="text-xl-semibold text-ink-gray-8">{{ t('dash.admin.statistics') }}</h2>

      <div v-if="cards.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="card in cards"
          :key="card.label"
          class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
        >
          <p class="text-p-xs text-ink-gray-5">{{ card.label }}</p>
          <p class="text-xl-semibold text-ink-gray-8">{{ card.value }}</p>
        </div>
      </div>

      <div class="grid gap-4 sm:grid-cols-2" data-tour="admin-totals">
        <NumberCard
          :title="t('dash.admin.totalStudents')"
          :value="store.stats?.totals.students ?? null"
          :loading="store.statsLoading"
          :error="store.statsError || null"
        />
        <NumberCard
          :title="t('dash.admin.totalSchools')"
          :value="store.stats?.totals.schools ?? null"
          :loading="store.statsLoading"
          :error="store.statsError || null"
        />
      </div>

      <div class="grid gap-4 md:grid-cols-2" data-tour="admin-charts">
        <div class="h-64 min-w-0">
          <BarChart
            :title="t('dash.admin.studentsBySchool')"
            :subtitle="t('dash.admin.studentsBySchoolSub')"
            :data="schoolRows"
            x="school"
            y="count"
            :series-config="{ count: { label: t('dash.admin.seriesStudents') } }"
            :echart-options="flatChartOptions"
            :loading="store.statsLoading"
            :error="store.statsError || null"
          />
        </div>
        <div class="h-64 min-w-0">
          <DonutChart
            :title="t('dash.admin.studentsByCategory')"
            :data="categoryStats"
            category="category"
            value="count"
            :center-label="t('dash.admin.seriesStudents')"
            :echart-options="flatChartOptions"
            :loading="store.statsLoading"
            :error="store.statsError || null"
          />
        </div>
      </div>

      <div class="h-72 min-w-0">
        <BarChart
          :title="t('dash.admin.registrationsByYear')"
          :subtitle="t('dash.admin.registrationsByYearSub')"
          :data="registrationRows"
          x="year"
          y="count"
          :series-config="{ count: { label: t('dash.admin.seriesRegistrations') } }"
          :echart-options="flatChartOptions"
          :loading="store.statsLoading"
          :error="store.statsError || null"
        />
      </div>
    </section>
  </div>
</template>
