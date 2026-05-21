<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { priceHistoryService } from '../services/priceHistoryService.js'
import PriceHistoryChart from './PriceHistoryChart.vue'
import PriceRangePanel from './PriceRangePanel.vue'
import PriceComparisonPanel from './PriceComparisonPanel.vue'

const props = defineProps({
  flight: { type: Object, default: null },
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

// ── State ─────────────────────────────────────────────────────────────────────
const range = ref('3M')
const allSnapshots = ref([])
const loading = ref(false)
const seeding = ref(false)
const error = ref(null)
const noApiData = ref(false)

const RANGES = [
  { key: '1M', label: '1M', days: 30 },
  { key: '3M', label: '3M', days: 90 },
  { key: '6M', label: '6M', days: 180 },
]

// ── Derived from flight prop ──────────────────────────────────────────────────
function extractAirlineCode(flightNumber) {
  const match = String(flightNumber || '').trim().toUpperCase().match(/^([A-Z]{2,3})\d/)
  return match ? match[1] : ''
}

const origin = computed(() => props.flight?.origin || '')
const destination = computed(() => props.flight?.destination || '')
const departureDate = computed(() => props.flight?.date || '')
const airlineCode = computed(() => extractAirlineCode(props.flight?.flightNumber))

// ── Time-range filtering ──────────────────────────────────────────────────────
// Tabs filter by departure_date going FORWARD from today
const maxDepartureDays = computed(() => RANGES.find((r) => r.key === range.value)?.days ?? 90)

function parseLocalDate(str) {
  const [y, m, d] = String(str || '').split('-').map(Number)
  return new Date(y, m - 1, d)
}

function snapshotsWithinDays(days) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const cutoff = new Date(today)
  cutoff.setDate(cutoff.getDate() + days)
  return allSnapshots.value.filter((s) => {
    if (!s.departure_date) return false
    const dep = parseLocalDate(s.departure_date)
    return !Number.isNaN(dep.getTime()) && dep >= today && dep <= cutoff
  })
}

const filteredSnapshots = computed(() => snapshotsWithinDays(maxDepartureDays.value))

// Price Range panel is hard-capped at 6 months regardless of the chart's
// selected range tab, so "Most expensive day" can't surface a date a year out.
const rangeWindowSnapshots = computed(() => snapshotsWithinDays(180))

// ── Data fetching ─────────────────────────────────────────────────────────────
async function fetchHistory() {
  if (!origin.value || !destination.value) return
  loading.value = true
  error.value = null
  try {
    const data = await priceHistoryService.fetchPriceHistory(origin.value, destination.value)
    allSnapshots.value = data.snapshots ?? []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function seedAndRefresh() {
  if (!origin.value || !destination.value) return
  seeding.value = true
  error.value = null
  noApiData.value = false
  try {
    await priceHistoryService.fetchPriceCalendar(origin.value, destination.value, departureDate.value)
    await fetchHistory()
    if (allSnapshots.value.length === 0) {
      noApiData.value = true
    }
  } catch (err) {
    error.value = err.message
  } finally {
    seeding.value = false
  }
}

// Suggest a date ~6 weeks out as a likely candidate for available pricing
const suggestedDate = computed(() => {
  const d = new Date()
  d.setDate(d.getDate() + 42)
  return d.toISOString().split('T')[0]
})

function handleEscape(e) {
  if (e.key === 'Escape' && props.show) emit('close')
}
onMounted(() => window.addEventListener('keydown', handleEscape))
onUnmounted(() => window.removeEventListener('keydown', handleEscape))

// Re-fetch whenever the panel opens or the flight changes
watch(
  () => [props.show, props.flight?.id],
  ([visible]) => {
    if (visible) {
      allSnapshots.value = []
      seedAndRefresh()
    }
  },
  { immediate: true },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="overlay" @click.self="emit('close')">
      <div class="modal" role="dialog" aria-modal="true" @click.stop>

        <!-- Header -->
        <div class="modal__header">
          <div class="modal__title-group">
            <span class="modal__icon">📈</span>
            <div>
              <h2 class="modal__title">Price Trends</h2>
              <p class="modal__sub">
                {{ origin }} → {{ destination }}
                <template v-if="departureDate"> · {{ departureDate }}</template>
                <template v-if="airlineCode"> · {{ airlineCode }}</template>
              </p>
            </div>
          </div>
          <button type="button" class="close-btn" aria-label="Close" @click="emit('close')">✕</button>
        </div>

        <!-- Toolbar: range selector + seed button -->
        <div class="modal__toolbar">
          <div class="range-tabs">
            <button
              v-for="r in RANGES"
              :key="r.key"
              class="range-btn"
              :class="{ 'range-btn--active': range === r.key }"
              @click="range = r.key"
            >
              {{ r.label }}
            </button>
          </div>
          <button type="button" class="seed-btn" :disabled="seeding || loading" @click="seedAndRefresh">
            <span v-if="seeding">Loading…</span>
            <span v-else>⟳ Load Price Data</span>
          </button>
        </div>

        <!-- Error banner -->
        <div v-if="error" class="error-banner">⚠️ {{ error }}</div>

        <!-- No API data warning -->
        <div v-if="noApiData && !error" class="warn-banner">
          ⚠️ Skyscanner returned no pricing data for this route and date. Flight prices are typically available
          <strong>1–3 months in advance</strong>. Try searching with a departure date closer to today
          (e.g., <strong>{{ suggestedDate }}</strong>).
        </div>

        <!-- Chart -->
        <div class="modal__chart">
          <PriceHistoryChart
            :snapshots="filteredSnapshots"
            :loading="loading || seeding"
            :error="null"
          />
        </div>

        <!-- Bottom panels -->
        <div class="modal__panels">
          <PriceRangePanel
            :origin="origin"
            :destination="destination"
            :snapshots="rangeWindowSnapshots"
          />
          <PriceComparisonPanel
            v-if="airlineCode"
            :origin="origin"
            :destination="destination"
            :departure-date="departureDate"
            :airline-code="airlineCode"
            :current-price="flight?.totalPrice ?? null"
          />
          <div v-else class="comparison-panel no-airline">
            <h4 class="panel-title">vs. Historical Average</h4>
            <div class="panel-empty">
              <span>✈️</span>
              <p>Airline code not available for this flight.</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 36, 68, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1.5rem;
  overflow-y: auto;
}

.modal {
  background: var(--color-bg);
  border-radius: 16px;
  width: 100%;
  max-width: 740px;
  box-shadow: 0 20px 60px rgba(15, 36, 68, 0.25);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Header */
.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem 1rem;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
}

.modal__title-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.modal__icon {
  font-size: 1.6rem;
}

.modal__title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.modal__sub {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  margin-top: 2px;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1.5px solid var(--color-border);
  background: #fff;
  color: var(--color-text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}

.close-btn:hover {
  background: var(--color-bg-subtle);
  color: var(--color-text);
}

/* Toolbar */
.modal__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  gap: 1rem;
}

.range-tabs {
  display: flex;
  gap: 0.25rem;
  background: var(--color-bg-subtle);
  padding: 3px;
  border-radius: 8px;
}

.range-btn {
  padding: 0.3rem 0.8rem;
  border-radius: 6px;
  border: none;
  background: none;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.range-btn:hover {
  color: var(--color-text);
}

.range-btn--active {
  background: #fff;
  color: var(--color-primary);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.seed-btn {
  padding: 0.35rem 0.9rem;
  border-radius: 8px;
  border: 1.5px solid var(--color-primary);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}

.seed-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: #fff;
}

.seed-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* Error banner */
.error-banner {
  background: #fff5f5;
  color: #c0392b;
  font-size: 0.82rem;
  padding: 0.6rem 1.5rem;
  border-bottom: 1px solid #fecaca;
}

.warn-banner {
  background: #fffbeb;
  color: #92400e;
  font-size: 0.82rem;
  padding: 0.6rem 1.5rem;
  border-bottom: 1px solid #fde68a;
  line-height: 1.5;
}

/* Chart area */
.modal__chart {
  padding: 1.25rem 1.5rem;
  background: #fff;
}

/* Bottom panels */
.modal__panels {
  display: flex;
  gap: 0.75rem;
  padding: 0 1.5rem 1.5rem;
}

.no-airline {
  background: #fff;
  border: 1.5px solid var(--color-border);
  border-radius: 12px;
  padding: 1rem;
  flex: 1;
}

.no-airline .panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 1rem 0;
  color: var(--color-text-muted);
  font-size: 0.82rem;
  text-align: center;
}

.no-airline .panel-empty span { font-size: 1.5rem; }
</style>
