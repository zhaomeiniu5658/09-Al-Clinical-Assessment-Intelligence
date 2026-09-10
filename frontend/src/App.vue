<template>
  <PlatformTopbar v-if="showPlatformTopbar" />
  <RouterView />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PlatformTopbar from './components/PlatformTopbar.vue'

const route = useRoute()
const showPlatformTopbar = computed(() => Boolean(route.meta.platformShell))
</script>

