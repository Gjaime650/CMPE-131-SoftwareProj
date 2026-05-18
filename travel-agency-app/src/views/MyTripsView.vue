<script setup>
import { computed, onMounted, ref } from 'vue'
import { tenantConfig } from '../config/tenantConfig.js'
import { bookingService } from '../services/bookingService.js'
import { useAuth } from '../composables/useAuth.js'

const { userId, userEmail } = useAuth()

const isLoading = ref(true)
const errorMessage = ref('')
const trips = ref([])

const editTarget = ref(null)
const isSaving = ref(false)
const saveError = ref('')

function stripSeconds(time) {
  return String(time || '').slice(0, 5)
}

function openEdit(type, bookingId, reservation) {
  saveError.value = ''
  if (type === 'flight') {
    editTarget.value = {
      type,
      bookingId,
      reservationNo: reservation.Reservation_No,
      form: {
        Departure_Date: reservation.Departure_Date || '',
        Departure_Time: stripSeconds(reservation.Departure_Time),
        Arrive_Date: reservation.Arrive_Date || '',
        Arrive_Time: stripSeconds(reservation.Arrive_Time),
      },
    }
  } else {
    editTarget.value = {
      type,
      bookingId,
      reservationNo: reservation.Reservation_No,
      form: {
        Check_In_Date: reservation.Check_In_Date || '',
        Check_In_Time: stripSeconds(reservation.Check_In_Time),
        Check_Out_Date: reservation.Check_Out_Date || '',
        Check_Out_Time: stripSeconds(reservation.Check_Out_Time),
      },
    }
  }
}

async function submitEdit() {
  if (!editTarget.value) return
  isSaving.value = true
  saveError.value = ''
  try {
    const { type, bookingId, reservationNo, form } = editTarget.value
    const payload = { ...form }
    if (type === 'flight') {
      if (payload.Departure_Time?.length === 5) payload.Departure_Time += ':00'
      if (payload.Arrive_Time?.length === 5) payload.Arrive_Time += ':00'
      await bookingService.updateFlightReservation(bookingId, reservationNo, payload)
    } else {
      if (payload.Check_In_Time?.length === 5) payload.Check_In_Time += ':00'
      if (payload.Check_Out_Time?.length === 5) payload.Check_Out_Time += ':00'
      await bookingService.updateHotelReservation(bookingId, reservationNo, payload)
    }
    editTarget.value = null
    await loadTrips()
  } catch (e) {
    saveError.value = e.message || 'Failed to save changes.'
  } finally {
    isSaving.value = false
  }
}

function formatDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value || 'N/A'
  return date.toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const tripCountLabel = computed(() => {
  const tripCount = trips.value.length
  return tripCount === 1 ? '1 saved trip' : `${tripCount} saved trips`
})

async function loadTrips() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    trips.value = await bookingService.listBookings({
      userId: userId.value,
      agentId: tenantConfig.agentId,
    })
  } catch (error) {
    errorMessage.value = error.message || 'Unable to load saved trips.'
    trips.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadTrips()
})
</script>

<template>
  <div class="my-trips-view">
    <div class="my-trips-view__hero">
      <div>
        <p class="my-trips-view__eyebrow">Agent {{ tenantConfig.agentId }}</p>
        <h1 class="my-trips-view__title">My Trips</h1>
        <p class="my-trips-view__sub">
          Saved trips for {{ userEmail || `User ${userId}` }} with {{ tenantConfig.brandName }}.
        </p>
      </div>
      <div class="my-trips-view__summary">{{ tripCountLabel }}</div>
    </div>

    <div v-if="isLoading" class="state-card">Loading saved trips...</div>
    <div v-else-if="errorMessage" class="state-card state-card--error">{{ errorMessage }}</div>
    <div v-else-if="trips.length === 0" class="state-card">No saved trips found for this user and agent.</div>

    <div v-else class="trips-list">
      <article v-for="trip in trips" :key="trip.bookingId" class="trip-card">
        <div class="trip-card__header">
          <div>
            <p class="trip-card__meta">Booking #{{ trip.bookingId }}</p>
            <h2 class="trip-card__title">{{ formatDate(trip.startDate) }} to {{ formatDate(trip.endDate) }}</h2>
          </div>
          <div class="trip-card__pill">{{ trip.flightReservations.length }} flights · {{ trip.hotelReservations.length }} hotels</div>
        </div>

        <section class="trip-section">
          <h3 class="trip-section__title">Flight Details</h3>
          <p v-if="trip.flightReservations.length === 0" class="trip-section__empty">No flights saved for this trip.</p>
          <div v-else class="reservation-grid">
            <div v-for="flight in trip.flightReservations" :key="`${trip.bookingId}-${flight.Reservation_No}`" class="reservation-card">
              <div class="reservation-card__title">Flight Reservation</div>
              <div><strong>Airline code:</strong> {{ flight.Airline_Code || 'N/A' }}</div>
              <div><strong>Flight number:</strong> {{ flight.Flight_Number || 'N/A' }}</div>
              <div>{{ flight.Origin_Airport_Code }} to {{ flight.Destination_Airport_Code }}</div>
              <div>Departure: {{ formatDate(flight.Departure_Date) }} {{ flight.Departure_Time }}</div>
              <div>Arrival: {{ formatDate(flight.Arrive_Date) }} {{ flight.Arrive_Time }}</div>
              <div>Rate: ${{ Number(flight.Rate || 0).toLocaleString() }}</div>
              <button class="edit-btn" @click="openEdit('flight', trip.bookingId, flight)">Edit</button>
            </div>
          </div>
        </section>

        <section class="trip-section">
          <h3 class="trip-section__title">Hotel Details</h3>
          <p v-if="trip.hotelReservations.length === 0" class="trip-section__empty">No hotel saved for this trip.</p>
          <div v-else class="reservation-grid">
            <div v-for="hotel in trip.hotelReservations" :key="`${trip.bookingId}-${hotel.Reservation_No}`" class="reservation-card">
              <div class="reservation-card__title">Hotel Reservation</div>
              <div><strong>Hotel Name:</strong> {{ hotel.Hotel_Name || 'Hotel name unavailable' }}</div>
              <div>Check in: {{ formatDate(hotel.Check_In_Date) }} {{ hotel.Check_In_Time }}</div>
              <div>Check out: {{ formatDate(hotel.Check_Out_Date) }} {{ hotel.Check_Out_Time }}</div>
              <div>Rate: ${{ Number(hotel.Rate || 0).toLocaleString() }}</div>
              <button class="edit-btn" @click="openEdit('hotel', trip.bookingId, hotel)">Edit</button>
            </div>
          </div>
        </section>
      </article>
    </div>

    <!-- Edit modal -->
    <Teleport to="body">
      <div v-if="editTarget" class="modal-backdrop" @click.self="editTarget = null">
        <div class="modal">
          <h2 class="modal__title">Edit {{ editTarget.type === 'flight' ? 'Flight' : 'Hotel' }} Reservation</h2>

          <div v-if="editTarget.type === 'flight'" class="modal__fields">
            <label class="field-group">
              <span>Departure Date</span>
              <input type="date" v-model="editTarget.form.Departure_Date" />
            </label>
            <label class="field-group">
              <span>Departure Time</span>
              <input type="time" v-model="editTarget.form.Departure_Time" />
            </label>
            <label class="field-group">
              <span>Arrival Date</span>
              <input type="date" v-model="editTarget.form.Arrive_Date" />
            </label>
            <label class="field-group">
              <span>Arrival Time</span>
              <input type="time" v-model="editTarget.form.Arrive_Time" />
            </label>
          </div>

          <div v-else class="modal__fields">
            <label class="field-group">
              <span>Check-in Date</span>
              <input type="date" v-model="editTarget.form.Check_In_Date" />
            </label>
            <label class="field-group">
              <span>Check-in Time</span>
              <input type="time" v-model="editTarget.form.Check_In_Time" />
            </label>
            <label class="field-group">
              <span>Check-out Date</span>
              <input type="date" v-model="editTarget.form.Check_Out_Date" />
            </label>
            <label class="field-group">
              <span>Check-out Time</span>
              <input type="time" v-model="editTarget.form.Check_Out_Time" />
            </label>
          </div>

          <p v-if="saveError" class="modal__error">{{ saveError }}</p>

          <div class="modal__actions">
            <button class="modal__btn modal__btn--cancel" :disabled="isSaving" @click="editTarget = null">Cancel</button>
            <button class="modal__btn modal__btn--save" :disabled="isSaving" @click="submitEdit">
              {{ isSaving ? 'Saving…' : 'Save Changes' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.my-trips-view {
  min-height: calc(100vh - 56px);
  background: var(--color-bg);
  padding: 2rem;
}

.my-trips-view__hero {
  max-width: 1200px;
  margin: 0 auto 1.5rem;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
}

.my-trips-view__eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-accent-dark);
}

.my-trips-view__title {
  margin: 0;
  font-size: 2rem;
  color: var(--color-primary-dark);
}

.my-trips-view__sub {
  margin: 0.5rem 0 0;
  color: var(--color-text-muted);
}

.my-trips-view__summary {
  padding: 0.6rem 0.9rem;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  font-weight: 700;
}

.state-card {
  max-width: 1200px;
  margin: 0 auto;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 2rem;
  color: var(--color-text-muted);
}

.state-card--error {
  color: #c0392b;
}

.trips-list {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.trip-card {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: 0 10px 24px rgba(26, 54, 93, 0.06);
}

.trip-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.trip-card__meta {
  margin: 0 0 0.35rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.trip-card__title {
  margin: 0;
  color: var(--color-primary-dark);
  font-size: 1.2rem;
}

.trip-card__pill {
  padding: 0.45rem 0.75rem;
  border-radius: 999px;
  background: var(--color-primary-bg);
  color: var(--color-primary-dark);
  font-size: 0.85rem;
  font-weight: 700;
  white-space: nowrap;
}

.trip-section + .trip-section {
  margin-top: 1.25rem;
}

.trip-section__title {
  margin: 0 0 0.75rem;
  color: var(--color-text);
  font-size: 1rem;
}

.trip-section__empty {
  margin: 0;
  color: var(--color-text-muted);
}

.reservation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.75rem;
}

.reservation-card {
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 1rem;
  background: #fcfdff;
  color: var(--color-text);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.reservation-card__title {
  font-weight: 700;
  color: var(--color-primary-dark);
}

.edit-btn {
  margin-top: 0.5rem;
  padding: 0.3rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-primary-dark);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  align-self: flex-start;
}

.edit-btn:hover {
  background: var(--color-primary-bg);
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #fff;
  border-radius: 18px;
  padding: 2rem;
  width: min(480px, 92vw);
  box-shadow: 0 20px 60px rgba(26, 54, 93, 0.18);
}

.modal__title {
  margin: 0 0 1.25rem;
  font-size: 1.2rem;
  color: var(--color-primary-dark);
}

.modal__fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--color-text);
  font-weight: 600;
}

.field-group input {
  padding: 0.45rem 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 0.88rem;
  color: var(--color-text);
  background: #f9fafb;
  outline: none;
}

.field-group input:focus {
  border-color: var(--color-primary-dark);
  background: #fff;
}

.modal__error {
  margin: 0.85rem 0 0;
  font-size: 0.85rem;
  color: #c0392b;
}

.modal__actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.modal__btn {
  padding: 0.55rem 1.2rem;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.modal__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal__btn--cancel {
  background: #f0f2f5;
  color: var(--color-text);
}

.modal__btn--save {
  background: var(--color-primary-dark);
  color: #fff;
}

.modal__btn--save:not(:disabled):hover {
  opacity: 0.88;
}

@media (max-width: 768px) {
  .my-trips-view {
    padding: 1rem;
  }

  .my-trips-view__hero,
  .trip-card__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .modal__fields {
    grid-template-columns: 1fr;
  }
}
</style>