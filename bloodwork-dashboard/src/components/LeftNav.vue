<script setup lang="ts">
import { LayoutDashboard, History, SlidersHorizontal, Settings } from 'lucide-vue-next'

const navItems = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'History', path: '/history', icon: History },
  { label: 'Reference Ranges', path: '/reference', icon: SlidersHorizontal },
]
const settingsItem = { label: 'Settings', path: '/settings', icon: Settings }
</script>

<template>
  <nav class="left-nav" aria-label="Main">
    <div class="nav-logo">BW</div>

    <RouterLink
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      class="nav-icon"
      active-class="active"
      :aria-label="item.label"
    >
      <component :is="item.icon" :size="18" />
      <span class="tip">{{ item.label }}</span>
    </RouterLink>

    <div class="nav-spacer" />

    <RouterLink
      :to="settingsItem.path"
      class="nav-icon"
      active-class="active"
      :aria-label="settingsItem.label"
    >
      <component :is="settingsItem.icon" :size="18" />
      <span class="tip">{{ settingsItem.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped src="./LeftNav.css"></style>
