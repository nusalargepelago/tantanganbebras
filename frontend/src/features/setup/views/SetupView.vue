<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Alert,
  Button,
  ErrorMessage,
  FormControl,
  Select,
  Spinner,
  toast,
  type SelectOptionValue,
} from 'frappe-ui'

import {
  checkPassword,
  isPasswordValid,
  passwordRules,
} from '@/features/auth/validation'
import { brand } from '@/shared/brand'

import { useSetupStore, type SetupResult } from '../store'

const setup = useSetupStore()
const { t, locale } = useI18n()

const step = ref(1)
const done = ref<SetupResult | null>(null)
const gateReady = computed(() => setup.status !== null || setup.statusFailed)

const engine = ref<string | number>('sqlite')
const path = ref('')
const host = ref('')
const port = ref('')
const database = ref('')
const dbUsername = ref('')
const dbPassword = ref('')
const testing = ref(false)
const testedUrl = ref<string | null>(null)

const lang = ref(locale.value)

const brandName = ref(brand.name)
const brandTagline = ref(brand.tagline)
const brandDescription = ref(brand.description)
const brandSiteUrl = ref(brand.siteUrl)

const email = ref('')
const fullName = ref('')
const username = ref('')
const adminPassword = ref('')
const submitting = ref(false)

const engineOptions = [
  { label: 'SQLite', value: 'sqlite' },
  { label: 'MariaDB', value: 'mariadb' },
  { label: 'PostgreSQL', value: 'postgresql' },
]

const langOptions = [
  { label: 'English', value: 'en' },
  { label: 'Bahasa Indonesia', value: 'id' },
]

const stepLabel = computed(
  () =>
    [
      t('setup.steps.database'),
      t('setup.steps.brand'),
      t('setup.steps.administrator'),
    ][step.value - 1] ?? '',
)

const isSqlite = computed(() => engine.value === 'sqlite')

const passwordChecks = computed(() => checkPassword(adminPassword.value))
const passwordValid = computed(() => isPasswordValid(adminPassword.value))

const brandDisabled = computed(() => !brandName.value.trim())

const dbSlug = computed(
  () =>
    brandName.value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '') || 'app',
)

const adminDisabled = computed(
  () =>
    submitting.value ||
    !email.value.trim() ||
    !fullName.value.trim() ||
    !passwordValid.value,
)

const reasonText = computed(() => {
  if (setup.status?.reason === 'no_users') return t('setup.reasonNoUsers')
  if (setup.status?.reason === 'no_schema') return t('setup.reasonNoSchema')
  return ''
})

function prettyUrl(raw: string): string {
  try {
    return decodeURIComponent(raw)
  } catch {
    return raw
  }
}

const activeUrl = computed(() =>
  setup.status ? prettyUrl(setup.status.activeUrl) : '',
)

const activeEngineLabel = computed(
  () =>
    engineOptions.find((o) => o.value === setup.status?.activeEngine)?.label ??
    setup.status?.activeEngine ??
    '',
)

const alertDescription = computed(() =>
  [activeUrl.value, reasonText.value].filter(Boolean).join(' · '),
)

function dbConfig() {
  if (isSqlite.value) {
    return { engine: 'sqlite', path: path.value.trim() || undefined }
  }
  return {
    engine: String(engine.value),
    host: host.value.trim() || undefined,
    port: port.value.trim() || undefined,
    database: database.value.trim() || undefined,
    username: dbUsername.value.trim() || undefined,
    password: dbPassword.value || undefined,
  }
}

function onLang(value: SelectOptionValue | null | undefined) {
  if (value !== 'en' && value !== 'id') return
  lang.value = value
  locale.value = value
}

async function onTest() {
  testing.value = true
  testedUrl.value = null
  const url = await setup.testDb(dbConfig())
  testing.value = false
  if (url) {
    testedUrl.value = url
    toast.success(t('setup.testSuccess'))
  }
}

function goStep(next: number) {
  setup.error = ''
  step.value = next
}

function goStepFromBrand() {
  // Enter submits the form even when the Continue button is disabled.
  if (!brandDisabled.value) goStep(3)
}

async function onSubmit() {
  if (adminDisabled.value) return
  submitting.value = true
  const result = await setup.run(
    dbConfig(),
    {
      name: brandName.value.trim(),
      tagline: brandTagline.value.trim(),
      description: brandDescription.value.trim(),
      siteUrl: brandSiteUrl.value.trim() || undefined,
    },
    {
      email: email.value.trim(),
      password: adminPassword.value,
      fullName: fullName.value.trim(),
      username: username.value.trim() || undefined,
    },
    lang.value,
  )
  submitting.value = false
  if (!result) return
  setup.markComplete()
  // The backend hot-swaps the engine, so there is nothing to restart and
  // nothing left to wait for. Land on the confirmation card either way.
  done.value = result
}

function goToLogin() {
  // Full reload: the server renders index.html with the freshly created
  // brand, so window.brand (and every title/label) updates in one shot.
  window.location.replace('/login')
}

onMounted(async () => {
  if (!setup.status) await setup.fetchStatus()
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-surface-base p-4 text-ink-gray-8">
    <Spinner v-if="!gateReady" />
    <div
      v-else
      class="w-full max-w-md rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6"
    >
      <div v-if="done" class="space-y-4 text-center">
        <div class="flex justify-center">
          <div class="rounded-full bg-surface-gray-2 p-3 text-ink-green-6">
            <span class="lucide-check size-6" aria-hidden="true" />
          </div>
        </div>
        <h1 class="text-2xl-semibold text-ink-gray-8">
          {{ t('setup.completeTitle') }}
        </h1>
        <p class="text-p-sm text-ink-gray-5 [overflow-wrap:anywhere]">
          {{ t('setup.signInAs', { email: done.email }) }}
        </p>
        <Button
          variant="solid"
          theme="gray"
          icon-left="lucide-log-in"
          :label="t('auth.signIn')"
          @click="goToLogin"
        />
      </div>

      <template v-else>
        <div class="flex flex-col items-center gap-1.5 text-center">
          <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
            <span class="lucide-rocket size-6" aria-hidden="true" />
          </div>
          <h1 class="text-2xl-semibold text-ink-gray-8">{{ t('setup.title') }}</h1>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('setup.stepOf', { step }) }} · {{ stepLabel }}
          </p>
        </div>

        <Alert
          v-if="step === 1 && setup.status"
          class="mt-4 [overflow-wrap:anywhere]"
          :title="t('setup.activeAlert', { engine: activeEngineLabel })"
          :description="alertDescription || undefined"
        />

        <ErrorMessage v-if="setup.error" :message="setup.error" class="mt-4" />

        <form v-if="step === 1" class="mt-4 space-y-4" @submit.prevent="onTest">
          <Select
            v-model="engine"
            :label="t('setup.dbEngine')"
            :options="engineOptions"
          />

          <template v-if="isSqlite">
            <FormControl
              v-model="path"
              :label="t('setup.dbPath')"
              :placeholder="t('setup.dbPathPlaceholder')"
            />
          </template>

          <template v-else>
            <FormControl
              v-model="host"
              :label="t('setup.host')"
              placeholder="127.0.0.1"
              required
            />
            <FormControl v-model="port" :label="t('setup.port')" placeholder="5432" />
            <FormControl
              v-model="database"
              :label="t('setup.database')"
              :placeholder="dbSlug"
              required
            />
            <FormControl
              v-model="dbUsername"
              :label="t('field.username')"
              :placeholder="dbSlug"
            />
            <FormControl
              v-model="dbPassword"
              type="password"
              :label="t('field.password')"
              placeholder="••••••••"
              autocomplete="new-password"
            />
          </template>

          <p v-if="testedUrl" class="text-p-sm text-ink-green-6 [overflow-wrap:anywhere]">
            {{ t('setup.connected', { url: prettyUrl(testedUrl) }) }}
          </p>

          <div class="flex gap-2">
            <Button
              type="submit"
              variant="subtle"
              icon-left="lucide-plug"
              :label="t('setup.testConnection')"
              :loading="testing"
            />
            <Button
              type="button"
              variant="solid"
              theme="gray"
              :label="t('setup.continue')"
              class="flex-1"
              :disabled="testing"
              @click="goStep(2)"
            />
          </div>
        </form>

        <form
          v-else-if="step === 2"
          class="mt-4 space-y-4"
          @submit.prevent="goStepFromBrand"
        >
          <FormControl
            v-model="brandName"
            :label="t('setup.brandName')"
            placeholder="Acme Inc."
            maxlength="64"
            required
          />
          <FormControl
            v-model="brandTagline"
            :label="t('setup.tagline')"
            :placeholder="t('setup.taglinePlaceholder')"
            maxlength="120"
          />
          <FormControl
            v-model="brandDescription"
            :label="t('field.description')"
            :placeholder="t('setup.descPlaceholder')"
            maxlength="300"
          />
          <FormControl
            v-model="brandSiteUrl"
            :label="t('setup.siteUrl')"
            :placeholder="t('setup.siteUrlPlaceholder')"
            maxlength="512"
          />
          <Select
            :model-value="lang"
            :label="t('setup.language')"
            :options="langOptions"
            @update:model-value="onLang"
          />

          <div class="flex gap-2">
            <Button
              type="button"
              variant="subtle"
              :label="t('setup.back')"
              @click="goStep(1)"
            />
            <Button
              type="submit"
              variant="solid"
              theme="gray"
              :label="t('setup.continue')"
              class="flex-1"
              :disabled="brandDisabled"
            />
          </div>
        </form>

        <form v-else class="mt-4 space-y-4" @submit.prevent="onSubmit">
          <FormControl
            v-model="fullName"
            :label="t('field.fullName')"
            placeholder="Abdullah"
            autocomplete="name"
            required
          />
          <FormControl
            v-model="username"
            :label="t('field.username')"
            :placeholder="t('setup.usernamePlaceholder')"
            autocomplete="username"
          />
          <FormControl
            v-model="email"
            type="email"
            :label="t('field.email')"
            placeholder="abdulah@example.com"
            autocomplete="email"
            required
          />
          <FormControl
            v-model="adminPassword"
            type="password"
            :label="t('field.password')"
            placeholder="••••••••"
            autocomplete="new-password"
            required
          />

          <ul v-if="adminPassword.length" class="space-y-1">
            <li
              v-for="rule in passwordRules"
              :key="rule.key"
              class="flex items-center gap-1.5 text-p-xs"
              :class="passwordChecks[rule.key] ? 'text-ink-green-6' : 'text-ink-gray-5'"
            >
              <span
                :class="passwordChecks[rule.key] ? 'lucide-check' : 'lucide-minus'"
                class="size-3"
                aria-hidden="true"
              />
              {{ t(rule.label) }}
            </li>
          </ul>

          <div class="flex gap-2">
            <Button
              type="button"
              variant="subtle"
              :label="t('setup.back')"
              @click="goStep(2)"
            />
            <Button
              type="submit"
              variant="solid"
              theme="gray"
              icon-left="lucide-check"
              :label="t('setup.complete')"
              class="flex-1"
              :loading="submitting"
              :disabled="adminDisabled"
            />
          </div>
        </form>
      </template>
    </div>
  </div>
</template>
