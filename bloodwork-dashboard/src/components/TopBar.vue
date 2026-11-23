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

<style scoped>
.topbar {
  background: #ffffff;
  border-bottom: 1px solid #dde2ea;
  padding: 0 28px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 50;
}

.topbar-title {
  font-family: var(--font-serif);
  font-size: 20px;
  letter-spacing: -0.3px;
}

.topbar-sub {
  font-family: var(--font-mono);
  font-weight: 300;
  font-size: 11px;
  color: #8a95a3;
  margin-top: 1px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: #4a5568;
}
.date-range input {
  font: inherit;
  color: inherit;
  background: #eef1f5;
  border: 1px solid #dde2ea;
  padding: 4px 8px;
  border-radius: 6px;
}
.date-range input:focus-visible {
  outline: 2px solid var(--accent-mid);
  border-color: #006d77;
}

.btn-primary {
  background: #006d77;
  color: #fff;
  border: none;
  padding: 7px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-primary:hover {
  background: #005a62;
}
</style>
