
import { useState, type FormEvent } from 'react'

const API_URL = 'http://localhost:8000'

type Recommendation = {
  id: string
  name: string
  building: string
  campus: string
  floor: string
  noise_level: string
  crowd_level: string | null
  is_open_now: boolean
  rank: number
  score: number
}

type RecommendationResponse = {
  count: number
  results: Recommendation[]
}

type Props = {
  onSelectSpot: (id: string) => void
}

export default function Recommendations({
  onSelectSpot,
}: Props) {
  const [campus, setCampus] = useState('')
  const [noise, setNoise] = useState('')
  const [crowd, setCrowd] = useState('moderate')
  const [openNow, setOpenNow] = useState(false)

  const [results, setResults] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setSearched(false)
    setResults([])

    try {
      const csrfResponse = await fetch(
        `${API_URL}/api/accounts/csrf/`,
        { credentials: 'include' }
      )

      if (!csrfResponse.ok) {
        throw new Error('Could not obtain CSRF token.')
      }

      const csrfData: { csrfToken: string } =
        await csrfResponse.json()

      const response = await fetch(
        `${API_URL}/api/recommendations/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrfToken,
          },
          body: JSON.stringify({
            campus,
            noise_level: noise,
            amenities: [],
            max_crowd: crowd,
            open_now: openNow,
          }),
        }
      )

      if (!response.ok) {
        throw new Error(
          `Recommendations failed (HTTP ${response.status})`
        )
      }

      const data: RecommendationResponse =
        await response.json()

      setResults(data.results)
      setSearched(true)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not load recommendations.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="recommendations-section">
      <h2>Find My Study Spot</h2>

      <p>
        Choose your preferences to get personalized
        study spot recommendations.
      </p>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="rec-campus">Campus</label>
          <select
            id="rec-campus"
            value={campus}
            onChange={(event) =>
              setCampus(event.target.value)
            }
          >
            <option value="">Any campus</option>
            <option value="MMC">MMC</option>
            <option value="EC">Engineering Center</option>
          </select>
        </div>

        <div>
          <label htmlFor="rec-noise">Noise level</label>
          <select
            id="rec-noise"
            value={noise}
            onChange={(event) =>
              setNoise(event.target.value)
            }
          >
            <option value="">Any noise level</option>
            <option value="silent">Silent</option>
            <option value="quiet">Quiet</option>
            <option value="moderate">Moderate</option>
          </select>
        </div>

        <div>
          <label htmlFor="rec-crowd">
            Maximum crowd level
          </label>
          <select
            id="rec-crowd"
            value={crowd}
            onChange={(event) =>
              setCrowd(event.target.value)
            }
          >
            <option value="empty">Empty</option>
            <option value="moderate">Moderate</option>
            <option value="packed">Any crowd level</option>
          </select>
        </div>

        <label>
          <input
            type="checkbox"
            checked={openNow}
            onChange={(event) =>
              setOpenNow(event.target.checked)
            }
          />
          Open now only
        </label>

        <button type="submit" disabled={loading}>
          {loading
            ? 'Finding spots...'
            : 'Find My Study Spot'}
        </button>
      </form>

      {error && (
        <p role="alert" className="error-message">
          {error}
        </p>
      )}

      {searched && (
        <div aria-live="polite">
          <h3>
            Recommended Study Spots ({results.length})
          </h3>

          {results.length === 0 && (
            <p>
              No locations matched your preferences.
              Try changing your filters.
            </p>
          )}

          {results.map((spot) => (
            <div
              className="recommendation-card"
              key={spot.id}
            >
              <h4>
                #{spot.rank} {spot.name}
              </h4>

              <p>
                {spot.campus} · {spot.building}
                {' · '}Floor {spot.floor}
              </p>

              <p>
                Noise: {spot.noise_level}
                {' · '}
                Crowd: {spot.crowd_level ?? 'Unknown'}
              </p>

              <p>
                Score: {spot.score}
              </p>

              <button
                type="button"
                onClick={() => onSelectSpot(spot.id)}
              >
                View Details
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

