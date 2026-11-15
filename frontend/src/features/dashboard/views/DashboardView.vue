<script setup lang="ts">
import { computed } from 'vue'
import { Spinner } from 'frappe-ui'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import { useAuthStore } from '@/features/auth/store'
import AdminSchoolsDashboardView from './AdminSchoolsDashboardView.vue'
import StudentDashboardView from './StudentDashboardView.vue'
import TeacherDashboardView from './TeacherDashboardView.vue'

const auth = useAuthStore()

const gateReady = computed(() => auth.checked)
const sector = computed(() => {
  if (auth.isAdmin) return 'admin'
  if (auth.isTeacher) return 'teacher'
  return 'student'
})
</script>

<template>
  <AppPageHeader />

  <Spinner v-if="!gateReady" />

  <AdminSchoolsDashboardView v-else-if="sector === 'admin'" />
  <TeacherDashboardView v-else-if="sector === 'teacher'" />
  <StudentDashboardView v-else />
</template>
