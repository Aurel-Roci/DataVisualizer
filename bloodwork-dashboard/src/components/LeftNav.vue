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

<style scoped>
.left-nav {
  width: 64px;
  background: #0f1923;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  gap: 8px;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.nav-logo {
  font-family: var(--font-serif);
  font-size: 22px;
  color: #83c5be;
  margin-bottom: 16px;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  letter-spacing: 1px;
  user-select: none;
}

.nav-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #8a95a3;
  position: relative;
  transition:
    background 0.15s,
    color 0.15s;
}
.nav-icon:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}
.nav-icon.active {
  background: #006d77;
  color: #fff;
}

.tip {
  position: absolute;
  left: calc(100% + 10px);
  background: #1a2633;
  color: #fff;
  font-size: 11px;
  padding: 4px 9px;
  border-radius: 5px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.nav-icon:hover .tip {
  opacity: 1;
}

.nav-spacer {
  flex: 1;
}
</style>
