import axios from 'axios'

const BASE = '/search-api/api/v1/flights'

// Skyscanner city-level sky IDs used by the price-calendar endpoint.
// Multi-airport cities use a city code (LOND, NYCA, PARI) not the airport IATA code.
const SKY_ID_MAP = {
  SFO: 'SFO',
  CDG: 'PARI',  // Paris city (covers CDG + ORY)
  JFK: 'NYCA',  // New York City area (covers JFK, LGA, EWR)
  LAX: 'LAXA',  // Los Angeles area
  LHR: 'LOND',  // London city (covers LHR, LGW, STN)
  NRT: 'TYOA',  // Tokyo area
  HNL: 'HNL',
  ORD: 'CHIA',  // Chicago area
  MIA: 'MIA',
  SEA: 'SEA',
  BOS: 'BOS',
  DXB: 'DXB',
  SIN: 'SIN',
  SYD: 'SYDA',  // Sydney area
  ICN: 'SELA',  // Seoul area
  BKK: 'BKK',
  FRA: 'FRA',
  AMS: 'AMS',
  YYZ: 'TORA',  // Toronto area
  YVR: 'VANB',  // Vancouver area
  MAD: 'MAD',
  FCO: 'ROMA',  // Rome area
}

export function toSkyId(iata) {
  const code = String(iata || '').trim().toUpperCase()
  return SKY_ID_MAP[code] || `${code}-sky`
}

function handleError(error, fallback) {
  const detail = error?.response?.data?.detail
  const message = (typeof detail === 'string' ? detail : null)
    || error?.response?.data?.message
    || error?.message
    || fallback
  throw new Error(message)
}

export const priceHistoryService = {
  /**
   * Fetches the price calendar for a one-way route and auto-saves prices to
   * the Price_History DB. Call this to seed data before reading history.
   */
  async fetchPriceCalendar(originIata, destinationIata, fromDate, market = 'US', currency = 'USD') {
    // Use full month window: first → last day of the departure month
    const d = new Date(fromDate)
    const year = d.getFullYear()
    const month = d.getMonth() + 1
    const firstOfMonth = `${year}-${String(month).padStart(2, '0')}-01`
    const lastOfMonth = new Date(year, month, 0).toISOString().split('T')[0]
    try {
      const response = await axios.get(`${BASE}/price-calendar`, {
        params: {
          origin_sky_id: toSkyId(originIata),
          destination_sky_id: toSkyId(destinationIata),
          from_date: firstOfMonth,
          to_date: lastOfMonth,
          market,
          currency,
        },
      })
      return response.data
    } catch (error) {
      handleError(error, 'Failed to fetch price calendar.')
    }
  },

  /**
   * Returns all stored price snapshots for a route/date.
   * Each snapshot is { recorded_at, price, currency }.
   * Response shape: { origin, destination, departure_date, airline_code, snapshots[], data_points }
   */
  async fetchPriceHistory(originIata, destinationIata, options = {}) {
    const { airlineCode, fromRecorded, toRecorded } = options
    try {
      const params = {
        origin_sky_id: toSkyId(originIata),
        destination_sky_id: toSkyId(destinationIata),
      }
      if (airlineCode) params.airline_code = airlineCode
      if (fromRecorded) params.from_recorded = fromRecorded
      if (toRecorded) params.to_recorded = toRecorded

      const response = await axios.get(`${BASE}/price-history`, { params })
      return response.data
    } catch (error) {
      handleError(error, 'Failed to fetch price history.')
    }
  },

  /**
   * Returns the lowest and highest recorded prices for a route within an
   * optional time window. No departure_date filter — returns range across
   * all stored departure dates for the route.
   * Response shape: { min_price, max_price, min_recorded_at, max_recorded_at, ... }
   * Throws if no price data exists yet (404 from backend).
   */
  async fetchPriceRange(originIata, destinationIata, options = {}) {
    const { fromRecorded, toRecorded } = options
    try {
      const params = {
        origin_sky_id: toSkyId(originIata),
        destination_sky_id: toSkyId(destinationIata),
      }
      if (fromRecorded) params.from_recorded = fromRecorded
      if (toRecorded) params.to_recorded = toRecorded

      const response = await axios.get(`${BASE}/price-range`, { params })
      return response.data
    } catch (error) {
      if (error?.response?.status === 404) {
        throw new Error('No price data recorded yet for this route. Try viewing the price calendar first.')
      }
      handleError(error, 'Failed to fetch price range.')
    }
  },

  /**
   * Compares the most recent recorded price for a specific airline against its
   * historical average on a route.
   * Response shape (enough data):
   *   { current_price, average_price, percentage_difference, data_points, ... }
   * Response shape (too little data):
   *   { message: "Insufficient data for this time period", data_points: N }
   */
  async fetchPriceComparison(originIata, destinationIata, departureDate, airlineCode) {
    try {
      const params = {
        origin_sky_id: toSkyId(originIata),
        destination_sky_id: toSkyId(destinationIata),
      }
      if (departureDate) params.departure_date = departureDate
      if (airlineCode) params.airline_code = airlineCode
      const response = await axios.get(`${BASE}/price-comparison`, { params })
      return response.data
    } catch (error) {
      handleError(error, 'Failed to fetch price comparison.')
    }
  },
}
