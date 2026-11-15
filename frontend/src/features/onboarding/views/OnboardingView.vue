<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Alert, Button, Combobox, ErrorMessage, FormControl, Select, Spinner } from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import { api, getErrorMessage } from '@/shared/api'
import { categoryOptions } from '@/shared/labels'
import {
  fetchSchools,
  invalidateMasters,
  schoolOptions,
  type SchoolItem,
} from '@/shared/masters'
import { masterListEmpty } from '@/shared/pickerFilter'
import AddSchoolDialog from './AddSchoolDialog.vue'

type Role = 'student' | 'teacher'

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()

const gateReady = ref(false)
const pick = ref<Role | null>(null)
const submitting = ref(false)
const error = ref('')

const splitName = (() => {
  const parts = (auth.user?.fullName ?? '').trim().split(/\s+/).filter(Boolean)
  return { first: parts[0] ?? '', last: parts.slice(1).join(' ') }
})()

const studentForm = reactive({
  firstName: splitName.first,
  lastName: splitName.last,
  category: 'cub',
  schoolId: null as string | null,
})
const teacherForm = reactive({
  firstName: splitName.first,
  lastName: splitName.last,
  schoolId: null as string | null,
})
const schools = ref<SchoolItem[]>([])
const schoolSelect = ref<{ label: string; value: string }[]>([])
const addSchoolOpen = ref(false)
const addSchoolInitialName = ref('')

const categorySelect = computed(() => categoryOptions())
const studentSchool = computed(() => schools.value.find((s) => s.id === studentForm.schoolId))
const teacherSchool = computed(() => schools.value.find((s) => s.id === teacherForm.schoolId))
const pickedSchool = computed(() =>
  pick.value === 'student' ? studentSchool.value : teacherSchool.value,
)
// The "Add school" row is visible only when the picker would render nothing:
// the master is empty, or the typed query matches no school (predicate
// mirrored from frappe-ui's `matchesByLabelOrValue`).
const schoolPickerOptions = computed(() => [
  ...schoolSelect.value,
  {
    type: 'custom' as const,
    key: 'add-school',
    label: t('schools.add'),
    icon: 'lucide-plus',
    condition: ({ query }: { query: string }) =>
      masterListEmpty(schoolSelect.value, query),
    onClick: ({ query }: { query: string }) => openAddSchool(query.trim()),
  },
])
const studentDisabled = computed(
  () =>
    submitting.value ||
    !studentForm.firstName.trim() ||
    !studentForm.lastName.trim() ||
    !studentForm.schoolId,
)
const teacherDisabled = computed(
  () =>
    submitting.value ||
    !teacherForm.firstName.trim() ||
    !teacherForm.lastName.trim() ||
    !teacherForm.schoolId,
)

function choose(role: Role) {
  pick.value = role
  error.value = ''
}

onMounted(async () => {
  if (!auth.checked) await auth.fetchMe()
  if (auth.isAdmin) {
    await router.replace('/')
    return
  }
  if (auth.classification === null) await auth.fetchClassification()
  if (auth.classification !== null && auth.classification !== 'none') {
    await router.replace('/')
    return
  }
  try {
    schools.value = await fetchSchools()
    schoolSelect.value = schoolOptions(schools.value)
  } catch {
    error.value = t('onboarding.schoolsLoadFailed')
  } finally {
    gateReady.value = true
  }
})

function openAddSchool(name: string) {
  addSchoolInitialName.value = name
  addSchoolOpen.value = true
}

async function onSchoolCreated(school: SchoolItem) {
  invalidateMasters()
  try {
    schools.value = await fetchSchools()
    schoolSelect.value = schoolOptions(schools.value)
  } catch {
    error.value = t('onboarding.schoolsLoadFailed')
  }
  if (pick.value === 'student') studentForm.schoolId = school.id
  else teacherForm.schoolId = school.id
}

async function onSubmit(role: Role) {
  const isStudent = role === 'student'
  const form = isStudent ? studentForm : teacherForm
  if (isStudent ? studentDisabled.value : teacherDisabled.value) return

  submitting.value = true
  error.value = ''
  try {
    const { data } = await api.post<{ classification: Role }>(
      isStudent ? '/onboarding/student' : '/onboarding/teacher',
      isStudent
        ? {
            firstName: studentForm.firstName.trim(),
            lastName: studentForm.lastName.trim(),
            category: studentForm.category,
            schoolId: studentForm.schoolId,
          }
        : {
            firstName: teacherForm.firstName.trim(),
            lastName: teacherForm.lastName.trim(),
            schoolId: teacherForm.schoolId,
          },
    )
    auth.classification = data.classification
    await auth.fetchMe()
    await router.replace('/')
  } catch (e: any) {
    error.value = getErrorMessage(e, t('onboarding.failure'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-surface-base p-4 text-ink-gray-8">
    <Spinner v-if="!gateReady" />
    <div v-else class="w-full max-w-md rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6">
      <div class="flex flex-col items-center gap-1.5 text-center">
        <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
          <span class="lucide-user-round size-6" aria-hidden="true" />
        </div>
        <h1 class="text-2xl-semibold text-ink-gray-8">{{ t('onboarding.title') }}</h1>
        <p class="text-p-sm text-ink-gray-5">{{ t('onboarding.subtitle') }}</p>
      </div>

      <ErrorMessage v-if="error" class="mt-4" :message="error" />

      <template v-if="!pick">
        <div class="mt-6 grid gap-3">
          <button
            type="button"
            class="flex items-center gap-3 rounded-6 border border-outline-gray-1 bg-surface-base p-4 text-left transition hover:border-outline-gray-2"
            @click="choose('student')"
          >
            <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-5">
              <span class="lucide-graduation-cap size-5" aria-hidden="true" />
            </span>
            <span>
              <span class="block text-base-semibold text-ink-gray-8">{{ t('onboarding.student') }}</span>
              <span class="block text-p-sm text-ink-gray-5">{{ t('onboarding.studentHint') }}</span>
            </span>
          </button>

          <button
            type="button"
            class="flex items-center gap-3 rounded-6 border border-outline-gray-1 bg-surface-base p-4 text-left transition hover:border-outline-gray-2"
            @click="choose('teacher')"
          >
            <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-5">
              <span class="lucide-presentation size-5" aria-hidden="true" />
            </span>
            <span>
              <span class="block text-base-semibold text-ink-gray-8">{{ t('onboarding.teacher') }}</span>
              <span class="block text-p-sm text-ink-gray-5">{{ t('onboarding.teacherHint') }}</span>
            </span>
          </button>
        </div>
      </template>

      <template v-else>
        <button
          type="button"
          class="mt-4 inline-flex items-center gap-1.5 text-p-sm text-ink-gray-5 transition hover:text-ink-gray-7"
          @click="pick = null"
        >
          <span class="lucide-arrow-left size-4" aria-hidden="true" />
          {{ t('onboarding.back') }}
        </button>

        <form class="mt-4 space-y-4" @submit.prevent="onSubmit(pick)">
          <Alert v-if="pick === 'student'" theme="amber" icon="lucide-info" :title="t('onboarding.adminActivate')" />

          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-if="pick === 'student'"
              v-model="studentForm.firstName"
              :label="t('onboarding.firstName')"
              placeholder="Budi"
              required
            />
            <FormControl
              v-else
              v-model="teacherForm.firstName"
              :label="t('onboarding.firstName')"
              placeholder="Budi"
              required
            />
            <FormControl
              v-if="pick === 'student'"
              v-model="studentForm.lastName"
              :label="t('onboarding.lastName')"
              placeholder="Santoso"
              required
            />
            <FormControl
              v-else
              v-model="teacherForm.lastName"
              :label="t('onboarding.lastName')"
              placeholder="Santoso"
              required
            />
          </div>

          <Select
            v-if="pick === 'student'"
            v-model="studentForm.category"
            :label="t('onboarding.category')"
            :options="categorySelect"
          />

          <div class="space-y-3">
            <Combobox
              v-if="pick === 'student'"
              v-model="studentForm.schoolId"
              :label="t('onboarding.school')"
              :options="schoolPickerOptions"
              :placeholder="t('onboarding.schoolPlaceholder')"
              :required="true"
            />
            <Combobox
              v-else-if="pick === 'teacher'"
              v-model="teacherForm.schoolId"
              :label="t('onboarding.school')"
              :options="schoolPickerOptions"
              :placeholder="t('onboarding.schoolPlaceholder')"
              :required="true"
            />

            <dl
              v-if="pickedSchool"
              class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-base px-3 py-2 text-p-sm"
            >
              <div class="flex items-center justify-between gap-3">
                <dt class="text-ink-gray-5">{{ t('onboarding.city') }}</dt>
                <dd class="truncate text-ink-gray-8">
                  {{ pickedSchool?.city?.name ?? t('shared.selectSchoolFirst') }}
                </dd>
              </div>
              <div class="flex items-center justify-between gap-3">
                <dt class="text-ink-gray-5">{{ t('onboarding.country') }}</dt>
                <dd class="text-ink-gray-8">Indonesia</dd>
              </div>
            </dl>
          </div>

          <Button
            type="submit"
            variant="solid"
            theme="gray"
            :icon-left="pick === 'student' ? 'lucide-graduation-cap' : 'lucide-presentation'"
            :label="pick === 'student' ? t('onboarding.submitStudent') : t('onboarding.submitTeacher')"
            :loading="submitting"
            :disabled="pick === 'student' ? studentDisabled : teacherDisabled"
          />
        </form>
      </template>

      <AddSchoolDialog
        v-model:open="addSchoolOpen"
        :initial-name="addSchoolInitialName"
        @created="onSchoolCreated"
      />
    </div>
  </div>
</template>
