import { ref } from 'vue'

export const mobileMenuOpen = ref(false)

export function openMobileMenu(): void {
  mobileMenuOpen.value = true
}

export function closeMobileMenu(): void {
  mobileMenuOpen.value = false
}
