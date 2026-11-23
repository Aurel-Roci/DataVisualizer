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

<style scoped src="./App.css"></style>
