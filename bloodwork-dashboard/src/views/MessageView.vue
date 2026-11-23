<script setup lang="ts">
// Simple full-page message, used for not-yet-built pages and unknown URLs.
defineProps<{
  title: string
  text: string
}>()
</script>

<template>
  <div class="message-page">
    <h1>{{ title }}</h1>
    <p>{{ text }}</p>
    <RouterLink to="/">Back to dashboard</RouterLink>
  </div>
</template>

<style scoped src="./MessageView.css"></style>
