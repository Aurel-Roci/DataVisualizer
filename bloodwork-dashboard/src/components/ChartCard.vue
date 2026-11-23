<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import type { Marker } from '../types/bloodwork'
import { parseRange, statusFor, worstStatus } from '../utils/range'
import {
  buildChartData,
  buildChartOptions,
  formatDay,
  latestPoint,
  latestTime,
  referenceBandPlugin,
  seriesColors,
} from '../utils/chart'

const props = defineProps<{
  title: string
  series: Marker[]
  hidden: string[] // names of series greyed out by the user
}>()

const emit = defineEmits<{ (e: 'toggle', testName: string): void }>()

const isSingle = computed(() => props.series.length === 1)

const isVisible = (m: Marker) => !props.hidden.includes(m.test_name)

// worst status among the latest values of all series
const status = computed(() =>
  worstStatus(
    props.series.map((m) => {
      const last = latestPoint(m)
      return last ? statusFor(last.value, parseRange(m.reference_range)) : 'none'
    }),
  ),
)

const colors = computed(() => seriesColors(props.series, status.value))

const latestDate = computed(() => {
  const time = latestTime(props.series)
  return time ? formatDay(time) : ''
})

const legend = computed(() =>
  props.series.map((m, i) => ({
    name: m.test_name,
    color: colors.value[i]!,
    visible: isVisible(m),
    value: latestPoint(m)?.value ?? null,
    unit: m.unit,
  })),
)

// only the visible series are plotted; colours stay tied to each series' position
const visibleSeries = computed(() => props.series.filter(isVisible))
const visibleColors = computed(() => colors.value.filter((_, i) => isVisible(props.series[i]!)))

const chartData = computed(() =>
  buildChartData(visibleSeries.value, visibleColors.value, isSingle.value),
)
const chartOptions = computed(() => buildChartOptions(visibleSeries.value))

// the reference band only makes sense when the chart has a single series
const plugins = computed(() => {
  const range = isSingle.value ? parseRange(props.series[0]?.reference_range) : null
  return range ? [referenceBandPlugin(range)] : []
})
</script>

<template>
  <div class="chart-card">
    <div class="card-header">
      <div class="status-dot" :class="status" />
      <div class="card-title">{{ title }}</div>
      <div class="card-latest">latest · {{ latestDate }}</div>
    </div>

    <div class="card-legend">
      <button
        v-for="item in legend"
        :key="item.name"
        type="button"
        class="legend-item"
        :class="{ off: !item.visible }"
        :aria-pressed="item.visible"
        :title="item.visible ? `Hide ${item.name}` : `Show ${item.name}`"
        @click="emit('toggle', item.name)"
      >
        <span class="legend-line" :style="{ '--line': item.color }" />
        <span class="legend-name">{{ item.name }}</span>
        <span class="legend-value">{{ item.value }} {{ item.unit }}</span>
      </button>
    </div>

    <div class="chart-body" :class="{ single: isSingle }">
      <Line :data="chartData" :options="chartOptions" :plugins="plugins" />
    </div>
  </div>
</template>

<style scoped src="./ChartCard.css"></style>
