<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import type { Marker } from '../types/bloodwork'
import { parseRange, statusFor, worstStatus } from '../utils/range'
import {
  buildChartData,
  buildChartOptions,
  formatMonth,
  latestPoint,
  latestTime,
  referenceBandPlugin,
  seriesColors,
} from '../utils/chart'

const props = defineProps<{
  title: string
  series: Marker[]
}>()

const isSingle = computed(() => props.series.length === 1)

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
  return time ? formatMonth(time) : ''
})

const legend = computed(() =>
  props.series.map((m, i) => ({
    name: m.test_name,
    color: colors.value[i]!,
    value: latestPoint(m)?.value ?? null,
    unit: m.unit,
  })),
)

const chartData = computed(() => buildChartData(props.series, colors.value))
const chartOptions = computed(() => buildChartOptions(props.series))

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
      <div v-for="item in legend" :key="item.name" class="legend-item">
        <div class="legend-line" :style="{ background: item.color }" />
        {{ item.name }}
        <span class="legend-value">{{ item.value }} {{ item.unit }}</span>
      </div>
    </div>

    <div class="chart-body" :class="{ single: isSingle }">
      <Line :data="chartData" :options="chartOptions" :plugins="plugins" />
    </div>
  </div>
</template>

<style scoped src="./ChartCard.css"></style>
