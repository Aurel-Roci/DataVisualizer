<script setup lang="ts">
import { computed, ref } from "vue";
import { useBloodworkStore } from "../stores/bloodwork";

const store = useBloodworkStore();

const open = ref<Set<string>>(new Set());

function toggleOpen(name: string) {
  const next = new Set(open.value);
  if (!next.delete(name)) next.add(name);
  open.value = next;
}

const selected = computed(() => new Set(store.draft.selected));
const totalMarkers = computed(() => store.markers.length);

function selectedIn(group: { markers: { test_name: string }[] }) {
  return group.markers.filter((m) => selected.value.has(m.test_name)).length;
}
</script>

<template>
  <aside class="right-sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">Markers</div>
      <div class="sidebar-meta">{{ selected.size }} of {{ totalMarkers }} markers active</div>
    </div>

    <div class="sidebar-body">
      <div
        v-for="group in store.groups"
        :key="group.name"
        class="group-block"
        :class="{ open: open.has(group.name) }"
      >
        <button
          type="button"
          class="group-header"
          :aria-expanded="open.has(group.name)"
          @click="toggleOpen(group.name)"
        >
          <span class="chevron">▶</span>
          <span class="group-name">{{ group.name }}</span>
          <span class="group-count">{{ selectedIn(group) }} / {{ group.markers.length }}</span>
        </button>

        <div v-if="open.has(group.name)" class="group-body">
          <label class="group-option">
            <input
              type="checkbox"
              class="toggle"
              :checked="store.draft.groupInOne[group.name] ?? false"
              @change="store.setGroupInOne(group.name, ($event.target as HTMLInputElement).checked)"
            />
            Group in one chart
          </label>

          <label v-for="m in group.markers" :key="m.test_name" class="marker-row">
            <input
              type="checkbox"
              class="cb"
              :checked="selected.has(m.test_name)"
              @change="store.toggleMarker(m.test_name)"
            />
            <span class="marker-name">{{ m.test_name }}</span>
            <span class="marker-unit">{{ m.unit }}</span>
          </label>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="sidebar-stat">
        <span>Panels shown</span><span>{{ store.panels.length }}</span>
      </div>
      <div class="sidebar-stat">
        <span>Markers active</span><span>{{ selected.size }}</span>
      </div>
      <button type="button" class="btn-apply" @click="store.applyLayout()">Apply Layout</button>
    </div>
  </aside>
</template>

<style scoped>
.right-sidebar {
  width: var(--right-panel-w);
  background: var(--surface);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 15px 16px 13px;
  border-bottom: 1px solid var(--border);
}
.sidebar-title {
  font-family: var(--font-serif);
  font-size: 15px;
}
.sidebar-meta {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin-top: 2px;
}

.sidebar-body {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0;
}
.sidebar-body::-webkit-scrollbar {
  width: 3px;
}
.sidebar-body::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}

.group-block {
  border-bottom: 1px solid var(--border-light);
}
.group-header {
  width: 100%;
  background: none;
  border: none;
  font: inherit;
  text-align: left;
  padding: 9px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s;
}
.group-header:hover {
  background: var(--surface-alt);
}
.chevron {
  font-size: 9px;
  color: var(--text-muted);
  transition: transform 0.18s;
  flex-shrink: 0;
}
.group-block.open .chevron {
  transform: rotate(90deg);
}
.group-name {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.7px;
  text-transform: uppercase;
  color: var(--text-secondary);
  flex: 1;
}
.group-count {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}

.group-option {
  padding: 5px 14px 7px 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
  cursor: pointer;
  user-select: none;
}

.marker-row {
  padding: 5px 14px 5px 32px;
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  transition: background 0.1s;
}
.marker-row:hover {
  background: var(--surface-alt);
}
.marker-name {
  flex: 1;
  font-size: 13px;
}
.marker-unit {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}

/* checkbox */
.cb {
  appearance: none;
  width: 15px;
  height: 15px;
  border-radius: 4px;
  border: 1.5px solid var(--border);
  background: var(--surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  cursor: pointer;
  transition: all 0.12s;
}
.cb:checked {
  background: var(--accent);
  border-color: var(--accent);
}
.cb:checked::after {
  content: "";
  width: 4px;
  height: 7px;
  border: 1.5px solid #fff;
  border-top: none;
  border-left: none;
  transform: rotate(42deg) translateY(-1px);
}
.cb:focus-visible,
.toggle:focus-visible {
  outline: 2px solid var(--accent-mid);
  outline-offset: 2px;
}

/* toggle */
.toggle {
  appearance: none;
  width: 28px;
  height: 15px;
  border-radius: 8px;
  background: var(--border);
  position: relative;
  cursor: pointer;
  transition: background 0.15s;
  flex-shrink: 0;
}
.toggle:checked {
  background: var(--accent);
}
.toggle::after {
  content: "";
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: #fff;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: left 0.15s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
.toggle:checked::after {
  left: 15px;
}

.sidebar-footer {
  padding: 12px 14px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sidebar-stat {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
.sidebar-stat span:last-child {
  color: var(--accent);
  font-weight: 500;
}
.btn-apply {
  background: var(--accent);
  color: #fff;
  border: none;
  width: 100%;
  padding: 9px;
  border-radius: 7px;
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  letter-spacing: 0.2px;
}
.btn-apply:hover {
  background: var(--accent-hover);
}
</style>
