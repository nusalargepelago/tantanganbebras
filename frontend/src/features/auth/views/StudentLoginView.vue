<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, ErrorMessage, FormControl, Skeleton } from 'frappe-ui'

import { api } from '@/shared/api'
import { useAuthStore } from '../store'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { t } = useI18n()

const branding = ref<{ title?: string; subtitle?: string }>({})
const username = ref('')
const password = ref('')
const submitting = ref(false)

const disabled = computed(() => submitting.value || !username.value.trim() || !password.value)

async function loadBranding() {
  try {
    const { data } = await api.get('/student/auth/login')
    branding.value = data
  } catch {
    // Branding is cosmetic; the form still works without it.
  }
}

async function onSubmit() {
  if (disabled.value) return
  submitting.value = true
  const ok = await auth.studentLogin(username.value.trim(), password.value)
  submitting.value = false
  if (ok) {
    const next = (route.query.redirect as string) || '/'
    await router.replace(next.startsWith('/') ? next : '/')
  }
}

onMounted(loadBranding)
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-surface-base p-4 text-ink-gray-8">
    <div class="w-full max-w-sm rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6">
      <form class="space-y-4" @submit.prevent="onSubmit">
        <div class="flex flex-col items-center gap-1.5 text-center">
          <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
            <span class="lucide-graduation-cap size-6" aria-hidden="true" />
          </div>
          <h1 class="text-2xl-semibold text-ink-gray-8">
            {{ branding.subtitle || t('auth.studentLogin.title') }}
          </h1>
          <p class="text-p-sm text-ink-gray-5">{{ branding.title || 'Tantangan Bebras' }}</p>
        </div>

        <ErrorMessage v-if="auth.error" :message="auth.error" />

        <FormControl
          v-model="username"
          :label="t('auth.field.username')"
          placeholder="budi"
          autocomplete="username"
          required
        />
        <FormControl
          v-model="password"
          type="password"
          :label="t('auth.field.password')"
          placeholder="••••••••"
          autocomplete="current-password"
          required
        />

        <Button
          type="submit"
          variant="solid"
          theme="gray"
          icon-left="lucide-log-in"
          :label="t('auth.studentLogin.button')"
          :loading="submitting"
          :disabled="disabled"
        />

        <p class="text-center text-p-sm text-ink-gray-5">
          {{ t('auth.studentLogin.noAccount') }}
          <router-link :to="{ name: 'StudentRegister' }" class="text-ink-blue-link">
            {{ t('auth.studentLogin.register') }}
          </router-link>
        </p>
      </form>
    </div>
  </div>
</template>
