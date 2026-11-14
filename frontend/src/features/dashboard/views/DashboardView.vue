<script setup lang="ts">
import { computed } from 'vue'
import { Spinner } from 'frappe-ui'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import AdminDashboardView from './AdminDashboardView.vue'
import UserDashboardView from './UserDashboardView.vue'
import { useAuthStore } from '@/features/auth/store'

const auth = useAuthStore()

const gateReady = computed(() => auth.checked)
const isAdmin = computed(() => auth.user?.appRole === 'admin')
</script>

<template>
  <AppPageHeader />

  <Spinner v-if="!gateReady" />

  <AdminDashboardView v-else-if="isAdmin" />
  <UserDashboardView v-else />
</template>
