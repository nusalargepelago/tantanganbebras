<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, PageHeader, PageHeaderMobile } from 'frappe-ui'

import { brand } from '@/shared/brand'
import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'
import { useMediaQuery } from '@/shared/composables/useMediaQuery'

import { openMobileMenu } from './mobile-menu'

const { t, te } = useI18n()
const route = useRoute()
const isDesktop = useMediaQuery('(min-width: 640px)')

const title = computed(() => {
  const name = String(route.name ?? '')
  const key = `route.${name}.title`
  if (name && te(key)) return t(key)
  const meta = route.meta.title
  return typeof meta === 'string' ? meta : brand.name
})
</script>

<template>
  <PageHeader v-if="isDesktop">
    <PageBreadcrumbs />
    <slot />
  </PageHeader>

  <PageHeaderMobile v-else :title="title">
    <template #prefix>
      <Button
        variant="ghost"
        icon="lucide-panel-left"
        :label="t('menu.menu')"
        @click="openMobileMenu()"
      />
    </template>
    <template v-if="$slots.suffix" #suffix>
      <slot name="suffix" />
    </template>
  </PageHeaderMobile>
</template>
