<script setup lang="ts">
import LeftNav from './components/LeftNav.vue'
</script>

<template>
  <div class="app-frame">
    <LeftNav />
    <main class="main-slot">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-frame {
  display: flex;
  min-height: 100vh;
}

.main-slot {
  margin-left: 64px;
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
