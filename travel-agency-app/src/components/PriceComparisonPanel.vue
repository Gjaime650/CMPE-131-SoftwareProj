<script setup>
import { ref, watch } from 'vue'
import { priceHistoryService } from '../services/priceHistoryService.js'

const props = defineProps({
  origin: { type: String, required: true },
  destination: { type: String, required: true },
  departureDate: { type: String, required: true },
  airlineCode: { type: String, required: true },
})

const loading = ref(false)
const error = ref(null)
const result = ref(null)

async function load() {
  if (!props.origin || !props.destination) return
  loading.value = true
  error.value = null
  result.value = null
  try {
    result.value = await priceHistoryService.fetchPriceComparison(
      props.origin,
      props.destination,
      null,
      null,
    )
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.origin, props.destination, props.departureDate, props.airlineCode],
  load,
  { immediate: true },
)

function fmt(price) {
  return price != null ? `$${Number(price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'
}

function fmtPct(pct) {
  if (pct == null) return '—'
  const n = Number(pct)
  const sign = n > 0 ? '+' : ''
  return `${sign}${n.toFixed(1)}%`
}

function pctClass(pct) {
  if (pct == null) return ''
  return Number(pct) > 0 ? 'pct--above' : 'pct--below'
}

function pctLabel(pct) {
  if (pct == null) return ''
  return Number(pct) > 0 ? 'above average' : 'below average'
}

const isInsufficient = (r) => r && r.message != null
</script>

<template>
  <div class="comparison-panel">
    <h4 class="panel-title">vs. Historical Average</h4>

    <div v-if="loading" class="panel-loading">
      <div class="skel skel--row" />
      <div class="skel skel--row" />
      <div class="skel skel--short" />
    </div>

    <div v-else-if="error" class="panel-empty">
      <span>⚠️</span>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="result && isInsufficient(result)" class="panel-insufficient">
      <span>📊</span>
      <p>{{ result.message }}</p>
      <span class="data-points">{{ result.data_points }} snapshot{{ result.data_points === 1 ? '' : 's' }} recorded — need at least 2.</span>
    </div>

    <div v-else-if="result" class="comparison-rows">
      <div class="cmp-row">
        <span class="cmp-label">Current price</span>
        <span class="cmp-value">{{ fmt(result.current_price) }}</span>
      </div>
      <div class="cmp-row">
        <span class="cmp-label">Historical average</span>
        <span class="cmp-value">{{ fmt(result.historical_average) }}</span>
      </div>
      <div class="cmp-divider" />
      <div class="cmp-pct" :class="pctClass(result.difference_pct)">
        <span class="cmp-pct-number">{{ fmtPct(result.difference_pct) }}</span>
        <span class="cmp-pct-label">{{ pctLabel(result.difference_pct) }}</span>
      </div>
      <div class="cmp-footer">{{ result.data_points }} price point{{ result.data_points === 1 ? '' : 's' }} for {{ airlineCode }}</div>
    </div>

    <div v-else class="panel-empty">
      <span>📊</span>
      <p>No comparison data yet.</p>
    </div>
  </div>
</template>

<style scoped>
.comparison-panel {
  background: #fff;
  border: 1.5px solid var(--color-border);
  border-radius: 12px;
  padding: 1rem;
  flex: 1;
  min-width: 0;
}

.panel-title {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  margin-bottom: 0.85rem;
}

.panel-loading {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skel {
  border-radius: 6px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.skel--row { height: 24px; }
.skel--short { height: 14px; width: 60%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.panel-empty,
.panel-insufficient {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 1rem 0;
  color: var(--color-text-muted);
  font-size: 0.82rem;
  text-align: center;
}

.panel-insufficient span:first-child { font-size: 1.5rem; }

.data-points {
  font-size: 0.72rem;
  color: var(--color-text-muted);
}

.comparison-rows {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.cmp-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cmp-label {
  font-size: 0.82rem;
  color: var(--color-text-muted);
}

.cmp-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
}

.cmp-divider {
  height: 1px;
  background: var(--color-border);
  margin: 0.25rem 0;
}

.cmp-pct {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
}

.cmp-pct--above {
  background: #fff5f5;
}

.cmp-pct--below {
  background: #f0fdf4;
}

.cmp-pct-number {
  font-size: 1.3rem;
  font-weight: 700;
}

.pct--above .cmp-pct-number { color: #dc2626; }
.pct--below .cmp-pct-number { color: #15803d; }

.cmp-pct-label {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.cmp-footer {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  margin-top: 0.25rem;
}
</style>
