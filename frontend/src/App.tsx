import LocationMap from './LocationMap'
import Recommendations from './Recommendations'
import { useEffect, useState, type FormEvent } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'

type CrowdLevel = 'Empty' | 'Moderate' | 'Packed'
type CrowdDisplay = CrowdLevel | 'No recent reports'

type CrowdStatus = {
  level: 'empty' | 'moderate' | 'packed' | null
  level_label: string
  last_reported_at: string | null
  report_count: number
}

type StudySpot = {
  id: string
  name: string
  building: string
  campus: string
  crowd: CrowdDisplay
  reportCount: number
  lastReportedAt: string | null
  statusAvailable: boolean
}

type ApiLocation = {
  id: string
  name: string
  building: string
  campus: string
}

type LocationsResponse = {
  count: number
  next: string | null
  previous: string | null
  results: ApiLocation[]
}

type LocationDetail = {
  id: string
  name: string
  building: string
  floor: string
  room: string
  campus: string
  description: string
  noise_level: string
  capacity: number | null
  latitude: string | null
  longitude: string | null
  amenities: { slug: string; name: string }[]
  hours: {
    day_of_week: number
    day: string
    opens_at: string
    closes_at: string
  }[]
  is_open_now: boolean
  closes_at: string | null
}

type Review = {
  id: string
  location: string
  rating: number
  comment: string
  created_at: string
}

type ReviewsResponse = {
  count: number
  average_rating: number | null
  results: Review[]
}

function crowdLabel(
  level: CrowdStatus['level']
): CrowdDisplay {
  if (level === 'empty') return 'Empty'
  if (level === 'moderate') return 'Moderate'
  if (level === 'packed') return 'Packed'
  return 'No recent reports'
}

function crowdClass(level: CrowdDisplay): string {
  if (level === 'Empty') return 'empty'
  if (level === 'Moderate') return 'moderate'
  if (level === 'Packed') return 'packed'
  return 'unknown'
}

function stars(rating: number): string {
  const count = Math.max(
    0,
    Math.min(5, Math.round(rating))
  )

  return '★'.repeat(count) + '☆'.repeat(5 - count)
}

async function getCsrfToken(): Promise<string> {
  const response = await fetch(
    `${API_URL}/api/accounts/csrf/`,
    { credentials: 'include' }
  )

  if (!response.ok) {
    throw new Error('Could not get CSRF token.')
  }

  const data: { csrfToken: string } =
    await response.json()

  return data.csrfToken
}

async function fetchCrowdStatus(
  id: string
): Promise<CrowdStatus> {
  const response = await fetch(
    `${API_URL}/api/crowd-reports/status/${id}/`,
    { credentials: 'include' }
  )

  if (!response.ok) {
    throw new Error(
      `Crowd status failed: ${response.status}`
    )
  }

  return response.json()
}

async function getErrorMessage(
  response: Response
): Promise<string> {
  try {
    const data = await response.json()

    if (typeof data.detail === 'string') {
      return data.detail
    }

    if (typeof data.location === 'string') {
      return data.location
    }

    if (typeof data.level === 'string') {
      return data.level
    }

    if (Array.isArray(data.rating)) {
      return data.rating.join(' ')
    }

    if (Array.isArray(data.comment)) {
      return data.comment.join(' ')
    }

    if (Array.isArray(data.non_field_errors)) {
      return data.non_field_errors.join(' ')
    }

    return JSON.stringify(data)
  } catch {
    return `Request failed (HTTP ${response.status})`
  }
}

function App() {
  // Authentication

  const [isLoggedIn, setIsLoggedIn] =
    useState(false)

  const [checkingSession, setCheckingSession] =
    useState(true)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [authLoading, setAuthLoading] =
    useState(false)

  // Study locations

  const [spots, setSpots] =
    useState<StudySpot[]>([])

  const [loading, setLoading] = useState(true)
  const [apiError, setApiError] = useState('')

  const [search, setSearch] = useState('')
  const [campusFilter, setCampusFilter] =
    useState('All')

  const [crowdFilter, setCrowdFilter] =
    useState('All')

  const [selectedId, setSelectedId] =
    useState<string | null>(null)

  // Crowd reports

  const [message, setMessage] = useState('')
  const [messageError, setMessageError] =
    useState(false)

  const [reportLoading, setReportLoading] =
    useState(false)

  // FR-02: Location details

  const [locationDetail, setLocationDetail] =
    useState<LocationDetail | null>(null)

  const [detailLoading, setDetailLoading] =
    useState(false)

  const [detailError, setDetailError] =
    useState('')

  // FR-04: Student reviews

  const [reviews, setReviews] =
    useState<Review[]>([])

  const [reviewCount, setReviewCount] =
    useState(0)

  const [averageRating, setAverageRating] =
    useState<number | null>(null)

  const [reviewsLoading, setReviewsLoading] =
    useState(false)

  const [reviewsError, setReviewsError] =
    useState('')

  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')

  const [reviewSubmitting, setReviewSubmitting] =
    useState(false)

  const [reviewMessage, setReviewMessage] =
    useState('')

  const [reviewMessageError, setReviewMessageError] =
    useState(false)

  const [reviewRefresh, setReviewRefresh] =
    useState(0)

  // Check existing Django session

  useEffect(() => {
    const controller = new AbortController()

    async function checkSession() {
      try {
        const response = await fetch(
          `${API_URL}/api/accounts/me/`,
          {
            credentials: 'include',
            signal: controller.signal,
          }
        )

        if (!controller.signal.aborted) {
          setIsLoggedIn(response.ok)
        }
      } catch {
        if (!controller.signal.aborted) {
          setIsLoggedIn(false)
        }
      } finally {
        if (!controller.signal.aborted) {
          setCheckingSession(false)
        }
      }
    }

    void checkSession()

    return () => controller.abort()
  }, [])

  // Load study locations

  useEffect(() => {
    const controller = new AbortController()

    async function loadLocations() {
      setLoading(true)
      setApiError('')

      try {
        let url: string | null =
          `${API_URL}/api/locations/`

        const allLocations: ApiLocation[] = []
        const visited = new Set<string>()

        while (url && !controller.signal.aborted) {
          if (visited.has(url)) break

          visited.add(url)

          const response = await fetch(url, {
            credentials: 'include',
            signal: controller.signal,
          })

          if (!response.ok) {
            throw new Error(
              `Locations API: ${response.status}`
            )
          }

          const data: LocationsResponse =
            await response.json()

          allLocations.push(...data.results)

          url = data.next
            ? new URL(data.next, API_URL).toString()
            : null
        }

        const unique = Array.from(
          new Map(
            allLocations.map((item) => [
              item.id,
              item,
            ])
          ).values()
        )

        const locations: StudySpot[] =
          await Promise.all(
            unique.map(
              async (
                location
              ): Promise<StudySpot> => {
                try {
                  const status =
                    await fetchCrowdStatus(
                      location.id
                    )

                  return {
                    id: location.id,
                    name: location.name,
                    building: location.building,
                    campus: location.campus,
                    crowd: crowdLabel(status.level),
                    reportCount:
                      status.report_count,
                    lastReportedAt:
                      status.last_reported_at,
                    statusAvailable: true,
                  }
                } catch {
                  return {
                    id: location.id,
                    name: location.name,
                    building: location.building,
                    campus: location.campus,
                    crowd: 'No recent reports',
                    reportCount: 0,
                    lastReportedAt: null,
                    statusAvailable: false,
                  }
                }
              }
            )
          )

        if (!controller.signal.aborted) {
          setSpots(locations)
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error(error)

          setApiError(
            'Unable to load study locations from Django.'
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadLocations()

    return () => controller.abort()
  }, [])

  // Refresh crowd levels every 30 seconds

  useEffect(() => {
    if (!isLoggedIn || spots.length === 0) {
      return
    }

    let active = true
    let busy = false

    const interval = window.setInterval(
      async () => {
        if (busy) return

        busy = true

        try {
          const updates = await Promise.all(
            spots.map(async (spot) => {
              try {
                const status =
                  await fetchCrowdStatus(
                    spot.id
                  )

                return {
                  id: spot.id,
                  status,
                }
              } catch {
                return {
                  id: spot.id,
                  status: null,
                }
              }
            })
          )

          if (!active) return

          setSpots((current) =>
            current.map(
              (spot): StudySpot => {
                const update = updates.find(
                  (item) =>
                    item.id === spot.id
                )

                if (!update) return spot

                if (!update.status) {
                  return {
                    ...spot,
                    statusAvailable: false,
                  }
                }

                return {
                  ...spot,
                  crowd: crowdLabel(
                    update.status.level
                  ),
                  reportCount:
                    update.status.report_count,
                  lastReportedAt:
                    update.status.last_reported_at,
                  statusAvailable: true,
                }
              }
            )
          )
        } finally {
          busy = false
        }
      },
      30000
    )

    return () => {
      active = false
      window.clearInterval(interval)
    }
  }, [isLoggedIn, spots.length])

  // FR-02: Fetch location details

  useEffect(() => {
    if (!selectedId) {
      setLocationDetail(null)
      setDetailError('')
      return
    }

    const controller = new AbortController()

    async function loadDetails() {
      setLocationDetail(null)
      setDetailLoading(true)
      setDetailError('')

      try {
        const response = await fetch(
          `${API_URL}/api/locations/${selectedId}/`,
          {
            credentials: 'include',
            signal: controller.signal,
          }
        )

        if (!response.ok) {
          throw new Error(
            `Could not load location details (HTTP ${response.status}).`
          )
        }

        const data: LocationDetail =
          await response.json()

        if (!controller.signal.aborted) {
          setLocationDetail(data)
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setDetailError(
            error instanceof Error
              ? error.message
              : 'Could not load location details.'
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setDetailLoading(false)
        }
      }
    }

    void loadDetails()

    return () => controller.abort()
  }, [selectedId])

  // FR-04: Fetch reviews for selected location

  useEffect(() => {
    if (!selectedId) {
      setReviews([])
      setReviewCount(0)
      setAverageRating(null)
      setReviewsError('')
      return
    }

    const controller = new AbortController()

    async function loadReviews() {
      setReviews([])
      setReviewCount(0)
      setAverageRating(null)
      setReviewsLoading(true)
      setReviewsError('')

      try {
        const response = await fetch(
          `${API_URL}/api/reviews/?location=${encodeURIComponent(selectedId ?? '')}`,
          {
            credentials: 'include',
            signal: controller.signal,
          }
        )

        if (!response.ok) {
          throw new Error(
            await getErrorMessage(response)
          )
        }

        const data: ReviewsResponse =
          await response.json()

        if (!controller.signal.aborted) {
          setReviews(data.results)
          setReviewCount(data.count)
          setAverageRating(
            data.average_rating
          )
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setReviewsError(
            error instanceof Error
              ? error.message
              : 'Could not load reviews.'
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setReviewsLoading(false)
        }
      }
    }

    void loadReviews()

    return () => controller.abort()
  }, [selectedId, reviewRefresh])

  const selectedSpot = spots.find(
    (spot) => spot.id === selectedId
  )

  const campuses = [
    'All',
    ...Array.from(
      new Set(spots.map((spot) => spot.campus))
    ),
  ]

  const filteredSpots = spots.filter(
    (spot) => {
      const matchesSearch =
        `${spot.name} ${spot.building} ${spot.campus}`
          .toLowerCase()
          .includes(
            search.trim().toLowerCase()
          )

      const matchesCampus =
        campusFilter === 'All' ||
        spot.campus === campusFilter

      const matchesCrowd =
        crowdFilter === 'All' ||
        (
          spot.statusAvailable &&
          spot.crowd === crowdFilter
        )

      return (
        matchesSearch &&
        matchesCampus &&
        matchesCrowd
      )
    }
  )

  // Login

  async function handleLogin(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault()
    setLoginError('')

    if (
      !/^[^\s@]+@fiu\.edu$/i.test(
        email.trim()
      ) ||
      !password
    ) {
      setLoginError(
        'Enter a valid FIU email and password.'
      )
      return
    }

    setAuthLoading(true)

    try {
      const csrfToken =
        await getCsrfToken()

      const response = await fetch(
        `${API_URL}/api/accounts/login/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type':
              'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            email: email
              .trim()
              .toLowerCase(),
            password,
          }),
        }
      )

      if (!response.ok) {
        setLoginError(
          await getErrorMessage(response)
        )
        return
      }

      setPassword('')
      setIsLoggedIn(true)
    } catch {
      setLoginError(
        'Unable to connect to Django.'
      )
    } finally {
      setAuthLoading(false)
    }
  }

  // Logout

  async function handleLogout() {
    try {
      const csrfToken =
        await getCsrfToken()

      const response = await fetch(
        `${API_URL}/api/accounts/logout/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': csrfToken,
          },
        }
      )

      if (!response.ok) {
        throw new Error(
          await getErrorMessage(response)
        )
      }

      setIsLoggedIn(false)
      setEmail('')
      setPassword('')
      setSelectedId(null)
      setMessage('')
      setSearch('')
      setCampusFilter('All')
      setCrowdFilter('All')
      setReviewMessage('')
      setComment('')
      setRating(5)
    } catch (error) {
      setMessageError(true)

      setMessage(
        error instanceof Error
          ? error.message
          : 'Could not log out.'
      )
    }
  }

  // Submit crowd report

  async function submitReport(
    level: CrowdLevel
  ) {
    if (!selectedId || reportLoading) {
      return
    }

    const locationId = selectedId

    setReportLoading(true)
    setMessageError(false)
    setMessage('Submitting report...')

    let saved = false

    try {
      const csrfToken =
        await getCsrfToken()

      const response = await fetch(
        `${API_URL}/api/crowd-reports/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type':
              'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            location: locationId,
            level: level.toLowerCase(),
          }),
        }
      )

      if (!response.ok) {
        throw new Error(
          await getErrorMessage(response)
        )
      }

      saved = true

      const status =
        await fetchCrowdStatus(locationId)

      setSpots((current) =>
        current.map(
          (spot): StudySpot =>
            spot.id === locationId
              ? {
                  ...spot,
                  crowd: crowdLabel(
                    status.level
                  ),
                  reportCount:
                    status.report_count,
                  lastReportedAt:
                    status.last_reported_at,
                  statusAvailable: true,
                }
              : spot
        )
      )

      setMessage(
        `Report submitted successfully: ${level}`
      )
    } catch (error) {
      setMessageError(true)

      setMessage(
        saved
          ? 'Report saved, but the status could not be refreshed.'
          : error instanceof Error
            ? error.message
            : 'Could not submit report.'
      )
    } finally {
      setReportLoading(false)
    }
  }

  // FR-04: Submit a student review

  async function submitReview(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault()

    if (!selectedId || reviewSubmitting) {
      return
    }

    const locationId = selectedId

    setReviewMessage('')
    setReviewMessageError(false)

    if (
      !Number.isInteger(rating) ||
      rating < 1 ||
      rating > 5
    ) {
      setReviewMessageError(true)
      setReviewMessage(
        'Please select a rating from 1 to 5.'
      )
      return
    }

    if (comment.length > 1000) {
      setReviewMessageError(true)
      setReviewMessage(
        'Review comments must be 1000 characters or less.'
      )
      return
    }

    setReviewSubmitting(true)

    try {
      const csrfToken =
        await getCsrfToken()

      const response = await fetch(
        `${API_URL}/api/reviews/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type':
              'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            location: locationId,
            rating,
            comment: comment.trim(),
          }),
        }
      )

      if (!response.ok) {
        throw new Error(
          await getErrorMessage(response)
        )
      }

      setReviewMessage(
        'Your review was submitted successfully!'
      )

      setReviewMessageError(false)
      setComment('')
      setRating(5)

      // Reload reviews after successful submission

      setReviewRefresh(
        (current) => current + 1
      )
    } catch (error) {
      setReviewMessageError(true)

      setReviewMessage(
        error instanceof Error
          ? error.message
          : 'Could not submit review.'
      )
    } finally {
      setReviewSubmitting(false)
    }
  }

  // Check session screen

  if (checkingSession) {
    return (
      <main className="page">
        <div className="login-card">
          <h1>🐾 Teacher's Pet</h1>
          <p>
            Checking your login session...
          </p>
        </div>
      </main>
    )
  }

  // Login screen

  if (!isLoggedIn) {
    return (
      <main className="page login-page">
        <div className="login-card">
          <h1>🐾 Teacher's Pet</h1>

          <h2>
            Find Your Perfect Study Spot at FIU
          </h2>

          <p>
            Sign in to view study locations
            and crowd levels.
          </p>

          <form
            onSubmit={handleLogin}
            className="login-form"
          >
            <label htmlFor="email">
              FIU Email
            </label>

            <input
              id="email"
              type="email"
              placeholder="student@fiu.edu"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
            />

            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value
                )
              }
              required
            />

            {loginError && (
              <p
                className="error-message"
                role="alert"
              >
                {loginError}
              </p>
            )}

            <button
              type="submit"
              className="primary-button"
              disabled={authLoading}
            >
              {authLoading
                ? 'Signing in...'
                : 'Log In'}
            </button>
          </form>

          <p className="disclaimer">
            Student project, not FIU's
            official login. Do not use
            your university password.
          </p>
        </div>
      </main>
    )
  }

  // Main application

  return (
    <main className="page">
      <header className="header">
        <div>
          <h1>🐾 Teacher's Pet</h1>

          <h2>
            Find Your Perfect Study Spot at FIU
          </h2>

          <p>
            Search study locations and
            check their crowd levels.
          </p>
        </div>

        <button
          type="button"
          className="logout-button"
          onClick={handleLogout}
        >
          Log Out
        </button>
      </header>

      <div className="container">
        {!selectedSpot && (
          <Recommendations
            onSelectSpot={(id) => setSelectedId(id)}
          />
        )}
        {selectedSpot ? (
          <section className="details">
            <button
              type="button"
              className="back-button"
              onClick={() => {
                setSelectedId(null)
                setMessage('')
                setMessageError(false)
                setReviewMessage('')
                setComment('')
                setRating(5)
              }}
            >
              ← Back to Study Spots
            </button>

            <div className="details-card">
              <h2>
                {selectedSpot.name}
              </h2>

              <p>
                FIU {selectedSpot.campus}
                {' · '}
                {selectedSpot.building}
              </p>

              {/* FR-02: Location Details */}

              {locationDetail && (
                <LocationMap
                  name={locationDetail.name}
                  latitude={locationDetail.latitude}
                  longitude={locationDetail.longitude}
                />
              )}

              <h3>
                Location Information
              </h3>

              {detailLoading && (
                <p>
                  Loading location information...
                </p>
              )}

              {detailError && (
                <p
                  className="error-message"
                  role="alert"
                >
                  {detailError}
                </p>
              )}

              {locationDetail && (
                <div className="location-information">
                  <p>
                    <strong>Floor:</strong>{' '}
                    {locationDetail.floor ||
                      'Not available'}
                  </p>

                  <p>
                    <strong>Room:</strong>{' '}
                    {locationDetail.room ||
                      'Not available'}
                  </p>

                  <p>
                    <strong>Description:</strong>{' '}
                    {locationDetail.description ||
                      'Not available'}
                  </p>

                  <p>
                    <strong>Noise Level:</strong>{' '}
                    {locationDetail.noise_level
                      ? locationDetail.noise_level
                          .charAt(0)
                          .toUpperCase() +
                        locationDetail.noise_level
                          .slice(1)
                      : 'Not available'}
                  </p>

                  <p>
                    <strong>Capacity:</strong>{' '}
                    {locationDetail.capacity ??
                      'Not available'}
                  </p>

                  <p>
                    <strong>Amenities:</strong>{' '}
                    {locationDetail.amenities.length
                      ? locationDetail.amenities
                          .map(
                            (item) => item.name
                          )
                          .join(', ')
                      : 'Not available'}
                  </p>

                  <p>
                    <strong>Opening Hours:</strong>
                  </p>

                  {locationDetail.hours.length ? (
                    <ul>
                      {locationDetail.hours.map(
                        (hour) => (
                          <li
                            key={`${hour.day_of_week}-${hour.opens_at}-${hour.closes_at}`}
                          >
                            {hour.day}:
                            {' '}
                            {hour.opens_at.slice(0, 5)}
                            {' – '}
                            {hour.closes_at.slice(0, 5)}
                          </li>
                        )
                      )}
                    </ul>
                  ) : (
                    <p>Not available</p>
                  )}

                  <p>
                    <strong>Opening Status:</strong>{' '}
                    {locationDetail.hours.length === 0
                      ? 'Unknown (no hours recorded)'
                      : locationDetail.is_open_now
                        ? 'Open'
                        : 'Closed'}
                  </p>
                </div>
              )}

              {/* Current crowd level */}

              <h3>
                Current Crowd Level
              </h3>

              <span
                className={`crowd-badge ${crowdClass(
                  selectedSpot.crowd
                )}`}
              >
                {selectedSpot.statusAvailable
                  ? selectedSpot.crowd
                  : 'Status unavailable'}
              </span>

              <p className="report-count">
                Recent reports:{' '}
                {selectedSpot.statusAvailable
                  ? selectedSpot.reportCount
                  : 'Unavailable'}
              </p>

              {/* Submit crowd report */}

              <h3>
                Report Crowd Level
              </h3>

              <p>
                How crowded is this
                location right now?
              </p>

              <div className="report-buttons">
                {(
                  [
                    'Empty',
                    'Moderate',
                    'Packed',
                  ] as CrowdLevel[]
                ).map((level) => (
                  <button
                    type="button"
                    key={level}
                    className={`report-button ${crowdClass(
                      level
                    )}`}
                    disabled={reportLoading}
                    onClick={() =>
                      submitReport(level)
                    }
                  >
                    {level}
                  </button>
                ))}
              </div>

              {message && (
                <p
                  className={
                    messageError
                      ? 'error-message'
                      : 'success-message'
                  }
                  role="status"
                >
                  {message}
                </p>
              )}

              {/* FR-04: Student Reviews */}

              <div className="student-reviews">
                <h3>
                  Student Reviews & Ratings
                </h3>

                {reviewsLoading && (
                  <p>
                    Loading reviews...
                  </p>
                )}

                {reviewsError && (
                  <p
                    className="error-message"
                    role="alert"
                  >
                    {reviewsError}
                  </p>
                )}

                {!reviewsLoading &&
                  !reviewsError && (
                    <>
                      <p>
                        <strong>
                          Average Rating:
                        </strong>{' '}
                        {averageRating !== null
                          ? `${averageRating.toFixed(1)} / 5`
                          : 'Not rated yet'}
                      </p>

                      {averageRating !== null && (
                        <p>
                          {stars(averageRating)}
                        </p>
                      )}

                      <p>
                        <strong>
                          Total Reviews:
                        </strong>{' '}
                        {reviewCount}
                      </p>
                    </>
                  )}

                <h3>
                  Write a Review
                </h3>

                <p>
                  Rate this study location
                  and share your experience.
                </p>

                <form
                  onSubmit={submitReview}
                  className="login-form"
                >
                  <label htmlFor="review-rating">
                    Your Rating
                  </label>

                  <select
                    id="review-rating"
                    value={rating}
                    onChange={(event) =>
                      setRating(
                        Number(event.target.value)
                      )
                    }
                    disabled={reviewSubmitting}
                    required
                  >
                    <option value={5}>
                      ★★★★★ — 5 Stars
                    </option>

                    <option value={4}>
                      ★★★★☆ — 4 Stars
                    </option>

                    <option value={3}>
                      ★★★☆☆ — 3 Stars
                    </option>

                    <option value={2}>
                      ★★☆☆☆ — 2 Stars
                    </option>

                    <option value={1}>
                      ★☆☆☆☆ — 1 Star
                    </option>
                  </select>

                  <label htmlFor="review-comment">
                    Your Comment (Optional)
                  </label>

                  <textarea
                    id="review-comment"
                    value={comment}
                    onChange={(event) =>
                      setComment(
                        event.target.value
                      )
                    }
                    placeholder="Share your experience at this study location..."
                    maxLength={1000}
                    rows={4}
                    disabled={reviewSubmitting}
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      padding: '12px',
                      borderRadius: '8px',
                      border: '1px solid #ccc',
                      fontFamily: 'inherit',
                      fontSize: '14px',
                    }}
                  />

                  <p>
                    {comment.length} / 1000 characters
                  </p>

                  <button
                    type="submit"
                    className="primary-button"
                    disabled={reviewSubmitting}
                  >
                    {reviewSubmitting
                      ? 'Submitting Review...'
                      : 'Submit Review'}
                  </button>
                </form>

                {reviewMessage && (
                  <p
                    className={
                      reviewMessageError
                        ? 'error-message'
                        : 'success-message'
                    }
                    role="status"
                  >
                    {reviewMessage}
                  </p>
                )}

                <h3>
                  Reviews from Students
                </h3>

                {!reviewsLoading &&
                  !reviewsError &&
                  reviews.length === 0 && (
                    <p>
                      No reviews yet. Be the
                      first to review this
                      study location!
                    </p>
                  )}

                {reviews.map((review) => (
                  <div
                    key={review.id}
                    style={{
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      padding: '14px',
                      marginBottom: '12px',
                      backgroundColor: '#f9fafb',
                      color: '#111827',
                    }}
                  >
                    <p>
                      <strong>
                        {stars(review.rating)}
                      </strong>
                      {' '}
                      ({review.rating}/5)
                    </p>

                    {review.comment && (
                      <p>
                        {review.comment}
                      </p>
                    )}

                    <p
                      style={{
                        fontSize: '12px',
                        color: '#6b7280',
                      }}
                    >
                      {new Date(
                        review.created_at
                      ).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        ) : (
          <>
            {/* Search and filters */}

            <div className="filters">
              <div className="filter-group search-group">
                <label htmlFor="search">
                  Search Locations
                </label>

                <input
                  id="search"
                  type="search"
                  placeholder="Search by location or building..."
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value
                    )
                  }
                />
              </div>

              <div className="filter-group">
                <label htmlFor="campus">
                  Campus
                </label>

                <select
                  id="campus"
                  value={campusFilter}
                  onChange={(event) =>
                    setCampusFilter(
                      event.target.value
                    )
                  }
                >
                  {campuses.map(
                    (campus) => (
                      <option
                        key={campus}
                        value={campus}
                      >
                        {campus === 'All'
                          ? 'All Campuses'
                          : campus}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div className="filter-group">
                <label htmlFor="crowd">
                  Crowd Level
                </label>

                <select
                  id="crowd"
                  value={crowdFilter}
                  onChange={(event) =>
                    setCrowdFilter(
                      event.target.value
                    )
                  }
                >
                  <option value="All">
                    All Crowd Levels
                  </option>

                  <option value="Empty">
                    Empty
                  </option>

                  <option value="Moderate">
                    Moderate
                  </option>

                  <option value="Packed">
                    Packed
                  </option>

                  <option value="No recent reports">
                    No Recent Reports
                  </option>
                </select>
              </div>
            </div>

            <h2 className="section-title">
              Available Study Spots
            </h2>

            {loading && (
              <p>
                Loading study locations...
              </p>
            )}

            {apiError && (
              <p className="error-message">
                {apiError}
              </p>
            )}

            <div className="spots-grid">
              {filteredSpots.map(
                (spot) => (
                  <button
                    key={spot.id}
                    type="button"
                    className="spot-card"
                    onClick={() => {
                      setSelectedId(spot.id)
                      setMessage('')
                      setMessageError(false)
                      setReviewMessage('')
                      setComment('')
                      setRating(5)
                    }}
                  >
                    <h3>
                      {spot.name}
                    </h3>

                    <p className="spot-building">
                      FIU {spot.campus}
                      {' · '}
                      {spot.building}
                    </p>

                    <span
                      className={`crowd-badge ${crowdClass(
                        spot.crowd
                      )}`}
                    >
                      {spot.statusAvailable
                        ? spot.crowd
                        : 'Status unavailable'}
                    </span>
                  </button>
                )
              )}
            </div>

            {!loading &&
              !apiError &&
              filteredSpots.length === 0 && (
                <p className="no-results">
                  No study spots match
                  your filters.
                </p>
              )}

            <p className="footer-note">
              Study locations and crowd
              statuses are loaded from
              Django. Crowd levels refresh
              automatically every
              30 seconds.
            </p>
          </>
        )}
      </div>
    </main>
  )
}

export default App
