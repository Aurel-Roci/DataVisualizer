<script setup lang="ts">
defineProps<{
  title: string
  subtitle: string
}>()

// YYYY-MM-DD strings, bound to the date inputs
const from = defineModel<string>('from', { required: true })
const to = defineModel<string>('to', { required: true })

defineEmits<{ (e: 'add'): void }>()
</script>

<template>
  <header class="topbar">
    <div class="topbar-left">
      <div class="topbar-title">{{ title }}</div>
      <div class="topbar-sub">{{ subtitle }}</div>
    </div>

    <div class="topbar-right">
      <div class="date-range">
        <input v-model="from" type="date" :max="to" aria-label="From date" />
        <span>–</span>
        <input v-model="to" type="date" :min="from" aria-label="To date" />
      </div>
      <button type="button" class="btn-primary" @click="$emit('add')">+ Add Result</button>
    </div>
  </header>
</template>

<style scoped src="./TopBar.css"></style>
