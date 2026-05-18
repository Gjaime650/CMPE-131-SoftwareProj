<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Tooltip,
  Filler,
} from 'chart.js'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, LineController, Tooltip, Filler)

const props = defineProps({
  snapshots: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
})

const canvasRef = ref(null)
let chart = null

// Parse YYYY-MM-DD as local midnight (avoids UTC-offset off-by-one)
function parseLocalDate(str) {
  const [y, m, d] = String(str || '').split('-').map(Number)
  return new Date(y, m - 1, d)
}

function formatDate(raw) {
  const d = parseLocalDate(raw)
  return Number.isNaN(d.getTime()) ? String(raw) : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function buildChart() {
  if (!canvasRef.value || !canvasRef.value.isConnected) return
  if (chart) { chart.destroy(); chart = null }
  if (!props.snapshots.length) return

  const sorted = [...props.snapshots].sort((a, b) => parseLocalDate(a.departure_date) - parseLocalDate(b.departure_date))
  const labels = sorted.map((s) => formatDate(s.departure_date))
  const data = sorted.map((s) => s.price)

  chart = new Chart(canvasRef.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Price (USD)',
          data,
          borderColor: '#1a365d',
          backgroundColor: 'rgba(26, 54, 93, 0.08)',
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 7,
          pointBackgroundColor: '#1a365d',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` $${ctx.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { font: { size: 11 }, color: '#718096', maxTicksLimit: 8 },
        },
        y: {
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: {
            font: { size: 11 },
            color: '#718096',
            callback: (val) => `$${val.toLocaleString()}`,
          },
        },
      },
    },
  })
}

onMounted(() => nextTick().then(buildChart))
watch(() => props.snapshots, buildChart, { deep: true, flush: 'post' })
onUnmounted(() => { chart?.destroy(); chart = null })
</script>

<template>
  <div class="chart-wrap">
    <!-- Canvas is always in DOM so Chart.js can measure it -->
    <canvas ref="canvasRef" class="chart-canvas" />
    <!-- Overlays cover the canvas when there is no real data -->
    <div v-if="loading" class="chart-overlay chart-skeleton" />
    <div v-else-if="error" class="chart-overlay chart-state chart-state--error">
      <span>⚠️</span> {{ error }}
    </div>
    <div v-else-if="!snapshots.length" class="chart-overlay chart-state">
      <span>📈</span>
      <p>No data for this range. Try <strong>3M</strong> or <strong>1Y</strong>, or click <strong>Load Price Data</strong>.</p>
    </div>
  </div>
</template>

<style scoped>
.chart-wrap {
  position: relative;
  width: 100%;
  height: 260px;
}

.chart-canvas {
  width: 100% !important;
  height: 100% !important;
  display: block;
}

/* Overlays sit on top of the canvas */
.chart-overlay {
  position: absolute;
  inset: 0;
  border-radius: 8px;
}

.chart-skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.chart-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--color-text-muted);
  font-size: 0.88rem;
  text-align: center;
  padding: 1rem;
}

.chart-state span {
  font-size: 2rem;
}

.chart-state--error {
  color: #c0392b;
}

.chart-state p {
  max-width: 300px;
  line-height: 1.5;
}
</style>
