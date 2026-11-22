<script setup lang="ts">
defineProps<{
  title: string;
  subtitle: string;
  rangeLabel: string;
}>();
</script>

<template>
  <header class="topbar">
    <div class="topbar-left">
      <div class="topbar-title">{{ title }}</div>
      <div class="topbar-sub">{{ subtitle }}</div>
    </div>

    <div class="topbar-right">
      <div v-if="rangeLabel" class="date-range">📅 {{ rangeLabel }}</div>
      <button class="btn-primary">+ Add Result</button>
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
  font-family: var(--font-mono);
  font-size: 11px;
  color: #4a5568;
  background: #eef1f5;
  border: 1px solid #dde2ea;
  padding: 5px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition:
    border-color 0.15s,
    color 0.15s;
}
.date-range:hover {
  border-color: #006d77;
  color: #006d77;
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
