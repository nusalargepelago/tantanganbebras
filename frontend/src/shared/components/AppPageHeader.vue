<script setup lang="ts">
import { computed, useSlots } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, PageHeader, PageHeaderMobile } from 'frappe-ui'

import { breadcrumbMap } from '@/app/breadcrumbs'
import { openMobileMenu } from '@/app/mobile-menu'
import { useMediaQuery } from '@/app/useMediaQuery'

import PageBreadcrumbs from './PageBreadcrumbs.vue'

const props = defineProps<{
  /** Overrides the last breadcrumb (desktop) and the centered title (mobile). */
  title?: string
}>()

const route = useRoute()
const { t } = useI18n()
const slots = useSlots()

const isDesktop = useMediaQuery('(min-width: 640px)')

const mobileTitle = computed(() => {
  if (props.title) return props.title
  const entry = breadcrumbMap[route.name as string]
  if (entry) return t(entry.label)
  return typeof route.meta.title === 'string' ? route.meta.title : ''
})
</script>

<template>
  <PageHeader v-if="isDesktop">
    <div class="flex min-w-0 items-center gap-2">
      <PageBreadcrumbs :title="title" />
      <slot name="leading" />
    </div>
    <div v-if="slots.actions" class="ml-auto flex items-center gap-2">
      <slot name="actions" />
    </div>
  </PageHeader>

  <PageHeaderMobile v-else :title="mobileTitle">
    <template #prefix>
      <Button
        variant="ghost"
        icon="lucide-panel-left"
        :label="t('menu.open')"
        @click="openMobileMenu()"
      />
    </template>
    <template v-if="slots['mobile-actions']" #suffix>
      <slot name="mobile-actions" />
    </template>
  </PageHeaderMobile>
</template>
