<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Spinner } from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import AdminSchoolsDashboardView from './AdminSchoolsDashboardView.vue'
import StudentDashboardView from './StudentDashboardView.vue'

const auth = useAuthStore()

const gateReady = computed(() => auth.checked)
const showAdmin = computed(() => auth.isAdmin || auth.isStaff)

onMounted(async () => {
  if (!auth.checked) await auth.fetchMe()
})
</script>

<template>
  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <template v-else>
    <AdminSchoolsDashboardView v-if="showAdmin" />
    <StudentDashboardView v-else />
  </template>
</template>
