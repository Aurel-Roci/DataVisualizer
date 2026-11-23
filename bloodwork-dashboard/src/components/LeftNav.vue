<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { LayoutDashboard, History, SlidersHorizontal, Settings } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

const navItems = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'History', path: '/history', icon: History },
  { label: 'Reference Ranges', path: '/reference', icon: SlidersHorizontal },
]

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <nav class="left-nav">
    <div class="nav-logo">BW</div>

    <div
      v-for="item in navItems"
      :key="item.path"
      class="nav-icon"
      :class="{ active: route.path === item.path }"
      @click="navigate(item.path)"
    >
      <component :is="item.icon" :size="18" />
      <span class="tip">{{ item.label }}</span>
    </div>

    <div class="nav-spacer" />

    <div class="nav-icon" @click="navigate('/settings')">
      <Settings :size="18" />
      <span class="tip">Settings</span>
    </div>
  </nav>
</template>

<style scoped src="./LeftNav.css"></style>
