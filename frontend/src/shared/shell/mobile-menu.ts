import { ref } from 'vue'

export const mobileMenuOpen = ref(false)

export function openMobileMenu(): void {
  mobileMenuOpen.value = true
}
