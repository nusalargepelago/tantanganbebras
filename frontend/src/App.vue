<script setup lang="ts">
import { FrappeUIProvider } from 'frappe-ui'

import ProductTour from '@/app/tour/ProductTour.vue'
import TourCatalogDialog from '@/app/tour/TourCatalogDialog.vue'
</script>

<template>
  <FrappeUIProvider>
    <router-view />
    <ProductTour />
    <TourCatalogDialog />
  </FrappeUIProvider>
</template>
