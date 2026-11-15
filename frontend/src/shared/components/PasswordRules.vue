<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { checkPassword, passwordRules } from '@/features/auth/validation'

const props = defineProps<{
  password: string
}>()

const { t } = useI18n()
const checks = computed(() => checkPassword(props.password))
</script>

<template>
  <ul v-if="password.length" class="space-y-1">
    <li
      v-for="rule in passwordRules"
      :key="rule.key"
      class="flex items-center gap-1.5 text-p-xs"
      :class="checks[rule.key] ? 'text-ink-green-6' : 'text-ink-gray-5'"
    >
      <span
        :class="checks[rule.key] ? 'lucide-check' : 'lucide-minus'"
        class="size-3"
        aria-hidden="true"
      />
      {{ t(rule.label) }}
    </li>
  </ul>
</template>
