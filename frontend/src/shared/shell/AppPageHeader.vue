<script setup lang="ts">
import { computed, useSlots } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, PageHeader, PageHeaderMobile } from 'frappe-ui'

import { breadcrumbMap } from '@/app/breadcrumbs'
import { brand } from '@/shared/brand'
import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'
import { useMediaQuery } from '@/shared/composables/useMediaQuery'

import { openMobileMenu } from './mobile-menu'

const props = defineProps<{
  /** Overrides the last breadcrumb (desktop) and the centered title (mobile). */
  title?: string
}>()

const route = useRoute()
const { t, te } = useI18n()
const slots = useSlots()
const isDesktop = useMediaQuery('(min-width: 640px)')

const mobileTitle = computed(() => {
  if (props.title) return props.title
  const name = String(route.name ?? '')
  const titleKey = `route.${name}.title`
  if (name && te(titleKey)) return t(titleKey)
  const entry = name ? breadcrumbMap[name] : undefined
  if (entry) return t(entry.label)
  return typeof route.meta.title === 'string' ? route.meta.title : brand.name
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
    <slot v-else />
  </PageHeader>

  <PageHeaderMobile v-else :title="mobileTitle">
    <template #prefix>
      <Button
        variant="ghost"
        icon="lucide-panel-left"
        :label="t('menu.menu')"
        @click="openMobileMenu()"
      />
    </template>
    <template v-if="slots['mobile-actions']" #suffix>
      <slot name="mobile-actions" />
    </template>
    <template v-else-if="slots.suffix" #suffix>
      <slot name="suffix" />
    </template>
  </PageHeaderMobile>
</template>
