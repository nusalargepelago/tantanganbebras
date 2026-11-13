<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Spinner } from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import AdminDashboardView from './AdminDashboardView.vue'
import StudentDashboardView from './StudentDashboardView.vue'

const auth = useAuthStore()

const gateReady = computed(() => auth.checked)
const isAdmin = computed(() => auth.isAdmin || auth.isStaff)

onMounted(async () => {
  if (!auth.checked) await auth.fetchMe()
})
</script>

<template>
  <Spinner v-if="!gateReady" />

  <AdminDashboardView v-else-if="isAdmin" />
  <StudentDashboardView v-else />
</template>
