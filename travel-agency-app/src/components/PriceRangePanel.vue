<script setup>
import { ref, watch } from 'vue'
import { priceHistoryService } from '../services/priceHistoryService.js'

const props = defineProps({
  origin: { type: String, required: true },
  destination: { type: String, required: true },
  fromRecorded: { type: String, default: null },
  toRecorded: { type: String, default: null },
})

const loading = ref(false)
const error = ref(null)
const rangeData = ref(null)

async function load() {
  if (!props.origin || !props.destination) return
  loading.value = true
  error.value = null
  rangeData.value = null
  try {
    rangeData.value = await priceHistoryService.fetchPriceRange(
      props.origin,
      props.destination,
      { fromRecorded: props.fromRecorded, toRecorded: props.toRecorded },
    )
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.origin, props.destination, props.fromRecorded, props.toRecorded],
  load,
  { immediate: true },
)

function formatDate(raw) {
  if (!raw) return '—'
  const parts = String(raw).split('-').map(Number)
  const d = parts.length === 3 ? new Date(parts[0], parts[1] - 1, parts[2]) : new Date(raw)
  return Number.isNaN(d.getTime()) ? String(raw) : d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

function fmt(price) {
  return price != null ? `$${Number(price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'
}
</script>

<template>
  <div class="range-panel">
    <h4 class="panel-title">Price Range</h4>

    <div v-if="loading" class="panel-loading">
      <div class="skel skel--tall" />
      <div class="skel skel--tall" />
    </div>

    <div v-else-if="error" class="panel-empty">
      <span>📭</span>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="rangeData" class="range-rows">
      <div class="range-row range-row--best">
        <div class="range-badge badge--green">Best time to fly</div>
        <div class="range-price">{{ fmt(rangeData.min_price) }}</div>
        <div class="range-date">Depart {{ formatDate(rangeData.min_departure_date) }}</div>
      </div>
      <div class="range-row range-row--worst">
        <div class="range-badge badge--red">Most expensive day</div>
        <div class="range-price">{{ fmt(rangeData.max_price) }}</div>
        <div class="range-date">Depart {{ formatDate(rangeData.max_departure_date) }}</div>
      </div>
    </div>

    <div v-else class="panel-empty">
      <span>📭</span>
      <p>No range data yet.</p>
    </div>
  </div>
</template>

<style scoped>
.range-panel {
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
  gap: 0.6rem;
}

.skel {
  border-radius: 8px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.skel--tall { height: 60px; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 1rem 0;
  color: var(--color-text-muted);
  font-size: 0.82rem;
  text-align: center;
}

.panel-empty span { font-size: 1.5rem; }

.range-rows {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.range-row {
  border-radius: 8px;
  padding: 0.65rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.range-row--best { background: #f0fdf4; border: 1px solid #bbf7d0; }
.range-row--worst { background: #fff5f5; border: 1px solid #fecaca; }

.range-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  width: fit-content;
}

.badge--green { background: #dcfce7; color: #15803d; }
.badge--red { background: #fee2e2; color: #dc2626; }

.range-price {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
}

.range-date {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}
</style>
