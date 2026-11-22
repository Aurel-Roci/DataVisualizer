<script setup lang="ts">
import { computed, onMounted } from "vue";
import TopBar from "../components/TopBar.vue";
import ChartCard from "../components/ChartCard.vue";
import RightSidebar from "../components/RightSidebar.vue";
import { useBloodworkStore } from "../stores/bloodwork";

const store = useBloodworkStore();

function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

// default window: the last two years
onMounted(() => {
  const end = new Date();
  const start = new Date(end);
  start.setFullYear(end.getFullYear() - 2);
  store.fetchResults(`${isoDate(start)}T00:00:00`, `${isoDate(end)}T23:59:59`);
});

function formatMonth(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

const rangeLabel = computed(() =>
  store.startDate ? `${formatMonth(store.startDate)} – ${formatMonth(store.endDate)}` : "",
);
const subtitle = computed(() =>
  store.startDate
    ? `${store.startDate.slice(0, 7)} → ${store.endDate.slice(0, 7)}`
    : "loading…",
);
</script>

<template>
  <div class="dashboard">
    <TopBar title="Bloodwork Dashboard" :subtitle="subtitle" :range-label="rangeLabel" />

    <div class="content">
      <p v-if="store.loading" class="state">Loading…</p>
      <p v-else-if="store.error" class="state error">Error: {{ store.error }}</p>
      <p v-else-if="store.markers.length === 0" class="state">
        No results in this date range.
      </p>
      <p v-else-if="store.panels.length === 0" class="state">
        No markers selected. Pick some in the sidebar and press Apply Layout.
      </p>
      <ChartCard
        v-for="panel in store.panels"
        :key="panel.id"
        :title="panel.title"
        :series="panel.series"
      />
    </div>

    <RightSidebar />
  </div>
</template>

<style scoped>
.dashboard {
  margin-right: var(--right-panel-w);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.content {
  padding: 24px 28px 48px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.state {
  font-size: 13px;
  color: var(--text-secondary);
}
.state.error {
  color: var(--danger);
}
</style>
