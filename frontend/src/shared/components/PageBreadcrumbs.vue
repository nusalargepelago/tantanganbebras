<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Breadcrumbs, Button } from 'frappe-ui'

import { breadcrumbMap, type BreadcrumbItem, HOME } from '@/app/breadcrumbs'

const props = defineProps<{
  title?: string
}>()

const route = useRoute()
const { t } = useI18n()

const crumbs = computed<BreadcrumbItem[]>(() => {
  const entry = breadcrumbMap[route.name as string]
  if (!entry) return []
  if (route.name === 'Dashboard') return []
  return [
    ...(entry.parent ? [{ ...entry.parent, label: t(entry.parent.label) }] : []),
    { label: props.title || t(entry.label) },
  ]
})
</script>

<template>
  <nav aria-label="Breadcrumb" class="min-w-0">
    <div class="flex min-w-0 items-center">
      <Button
        variant="ghost"
        icon="lucide-home"
        :label="t('crumb.dashboard')"
        :route="HOME.route"
        :tooltip="t('crumb.dashboard')"
        class="-ml-1.5"
      />
      <span
        v-if="crumbs.length"
        class="mx-0.5 text-base text-ink-gray-4"
        aria-hidden="true"
      >
        /
      </span>
      <Breadcrumbs v-if="crumbs.length" :items="crumbs" />
    </div>
  </nav>
</template>
