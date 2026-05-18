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

// Skyscanner numeric entity IDs — required by the /flights/search seed endpoint
const ENTITY_ID_MAP = {
  SFO: '27544008',
  CDG: '27539654',
  JFK: '27537542',
  LAX: '27545003',
  LHR: '27544850',
  NRT: '27540932',
  HNL: '27539681',
  ORD: '27537581',
  MIA: '27537627',
  SEA: '27544830',
  BOS: '27537482',
  DXB: '27536633',
  SIN: '27536533',
  SYD: '27544734',
  ICN: '27539489',
  BKK: '27536408',
  FRA: '27537543',
  AMS: '27536490',
  YYZ: '27544835',
  YVR: '27545000',
  MAD: '27540584',
  FCO: '27537469',
}

export function toSkyId(iata) {
  const code = String(iata || '').trim().toUpperCase()
  return SKY_ID_MAP[code] || `${code}-sky`
}

function toEntityId(iata) {
  const code = String(iata || '').trim().toUpperCase()
  return ENTITY_ID_MAP[code] || null
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
  /**
   * Seeds price history by running a real flight search through Search-API.
   * Used as a fallback when price-calendar returns no data.
   * Returns the number of records saved (from the response if available).
   */
  async seedViaFlightSearch(originIata, destinationIata, departureDate) {
    const originEntityId = toEntityId(originIata)
    const destinationEntityId = toEntityId(destinationIata)
    if (!originEntityId || !destinationEntityId) {
      throw new Error(`No entity ID mapping for ${originIata} or ${destinationIata}. Cannot seed via flight search.`)
    }
    try {
      const response = await axios.get('/search-api/api/v1/flights/search', {
        params: {
          origin_sky_id: toSkyId(originIata),
          origin_entity_id: originEntityId,
          destination_sky_id: toSkyId(destinationIata),
          destination_entity_id: destinationEntityId,
          date: departureDate,
          adults: 1,
          currency: 'USD',
          market: 'en-US',
        },
        timeout: 30000,
      })
      return response.data
    } catch (error) {
      handleError(error, 'Flight search seed failed.')
    }
  },

  async fetchPriceComparison(originIata, destinationIata, departureDate, airlineCode) {
    try {
      const response = await axios.get(`${BASE}/price-comparison`, {
        params: {
          origin_sky_id: toSkyId(originIata),
          destination_sky_id: toSkyId(destinationIata),
          departure_date: departureDate,
          airline_code: airlineCode,
        },
      })
      return response.data
    } catch (error) {
      handleError(error, 'Failed to fetch price comparison.')
    }
  },
}
