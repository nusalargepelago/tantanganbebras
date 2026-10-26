<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import AppPageHeader from '@/shared/components/AppPageHeader.vue'
import { useAuthStore } from '@/features/auth/store'

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()

const greeting = computed(
  () => auth.user?.fullName || auth.student?.firstName || t('dash.home.there'),
)

const staffCards = computed(() => [
  { name: 'AdminDashboard', title: t('dash.home.cards.admin.title'), desc: t('dash.home.cards.admin.desc'), icon: 'lucide-layout-dashboard' },
  { name: 'QuestionList', title: t('dash.home.cards.question.title'), desc: t('dash.home.cards.question.desc'), icon: 'lucide-library' },
  { name: 'EventList', title: t('dash.home.cards.event.title'), desc: t('dash.home.cards.event.desc'), icon: 'lucide-calendar' },
  { name: 'StudentList', title: t('dash.home.cards.student.title'), desc: t('dash.home.cards.student.desc'), icon: 'lucide-users' },
  { name: 'PracticeAdminList', title: t('dash.home.cards.practiceReview.title'), desc: t('dash.home.cards.practiceReview.desc'), icon: 'lucide-clipboard-check' },
])

const studentCards = computed(() => [
  { name: 'StudentDashboard', title: t('dash.home.cards.studentDash.title'), desc: t('dash.home.cards.studentDash.desc'), icon: 'lucide-layout-dashboard' },
  { name: 'PracticeList', title: t('dash.home.cards.practice.title'), desc: t('dash.home.cards.practice.desc'), icon: 'lucide-clipboard-list' },
  { name: 'EventStudentList', title: t('dash.home.cards.challenges.title'), desc: t('dash.home.cards.challenges.desc'), icon: 'lucide-calendar' },
])

const cards = computed(() => {
  if (auth.isStudent) return studentCards.value
  if (auth.isStaff) return staffCards.value
  return []
})

function open(name: string) {
  router.push({ name })
}
</script>

<template>
  <AppPageHeader />

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <div class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <p class="text-p-sm text-ink-gray-5">{{ t('dash.home.welcome') }}</p>
      <h1 class="text-2xl-semibold text-ink-gray-8">Tantangan Bebras — {{ greeting }}</h1>
    </div>

    <div
      v-if="cards.length"
      class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      data-tour="home-cards"
    >
      <div
        v-for="card in cards"
        :key="card.name"
        class="flex cursor-pointer flex-col gap-2 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 transition-colors hover:border-outline-gray-3"
        @click="open(card.name)"
      >
        <span :class="`${card.icon} size-6 text-ink-gray-5`" aria-hidden="true" />
        <span class="text-base-medium text-ink-gray-8">{{ card.title }}</span>
        <span class="text-p-sm text-ink-gray-5">{{ card.desc }}</span>
      </div>
    </div>
  </div>
</template>
