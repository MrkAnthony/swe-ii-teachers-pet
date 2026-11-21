
import { useState } from 'react'
import './App.css'

type CrowdLevel = 'Empty' | 'Moderate' | 'Packed'

type StudySpot = {
  id: number
  name: string
  building: string
  crowd: CrowdLevel
}

const initialSpots: StudySpot[] = [
  { id: 1, name: 'Green Library', building: 'GL', crowd: 'Empty' },
  { id: 2, name: 'Graham Center', building: 'GC', crowd: 'Moderate' },
  { id: 3, name: 'Parking Garage 6', building: 'PG6', crowd: 'Packed' },
]

function App() {
  // Login state
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  // Study spot state
  const [search, setSearch] = useState('')
  const [spots, setSpots] = useState<StudySpot[]>(initialSpots)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [message, setMessage] = useState('')

  const selectedSpot = spots.find(
    (spot) => spot.id === selectedId
  )

  const filteredSpots = spots.filter((spot) =>
    `${spot.name} ${spot.building}`
      .toLowerCase()
      .includes(search.toLowerCase())
  )

  // Demo login (not connected to backend)
  function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    if (
      !/^[^\s@]+@fiu\.edu$/i.test(email.trim()) ||
      password.length === 0
    ) {
      setLoginError('Enter a valid FIU email and password.')
      return
    }

    setLoginError('')
    setPassword('')
    setIsLoggedIn(true)
  }

  // Demo logout
  function handleLogout() {
    setIsLoggedIn(false)
    setEmail('')
    setPassword('')
    setSearch('')
    setSelectedId(null)
    setMessage('')
  }

  // Submit a demo crowd report
  function submitReport(level: CrowdLevel) {
    if (selectedId === null) return

    setSpots((current) =>
      current.map((spot) =>
        spot.id === selectedId
          ? { ...spot, crowd: level }
          : spot
      )
    )

    setMessage(`Demo report submitted successfully: ${level}`)
  }

  // LOGIN SCREEN
  if (!isLoggedIn) {
    return (
      <main className="login-page">
        <form className="login-card" onSubmit={handleLogin}>
          <h1>🐾 Teacher's Pet</h1>
          <h2>Welcome Back!</h2>

          <p>
            Sign in to find your perfect study spot at FIU.
          </p>

          <label htmlFor="email">FIU Email</label>
          <input
            id="email"
            type="email"
            placeholder="student@fiu.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="Enter a demo password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="off"
            required
          />

          {loginError && (
            <p className="login-error" role="alert">
              {loginError}
            </p>
          )}

          <button type="submit" className="login-button">
            Sign In
          </button>

          <p className="login-note">
            Demo login only. No real authentication is
            performed. Do not enter your actual FIU password.
          </p>
        </form>
      </main>
    )
  }

  // MAIN APPLICATION
  return (
    <main className="app">
      <header>
        <h1>🐾 Teacher's Pet</h1>
        <h2>Find Your Perfect Study Spot at FIU</h2>

        <p>
          Search study locations and check their crowd levels.
        </p>

        <button
          type="button"
          className="back-button"
          onClick={handleLogout}
        >
          Log Out
        </button>
      </header>

      {selectedSpot ? (
        // LOCATION DETAILS SCREEN
        <section className="details">
          <button
            type="button"
            className="back-button"
            onClick={() => {
              setSelectedId(null)
              setMessage('')
            }}
          >
            ← Back to Study Spots
          </button>

          <h2>{selectedSpot.name}</h2>
          <p>FIU MMC · {selectedSpot.building}</p>

          <h3>Current Crowd Level</h3>

          <span
            className={`crowd ${selectedSpot.crowd.toLowerCase()}`}
          >
            {selectedSpot.crowd}
          </span>

          <h3>How crowded is this location?</h3>

          <p>
            Select the current crowd level to submit a report.
          </p>

          <div className="report-buttons">
            {(
              ['Empty', 'Moderate', 'Packed'] as CrowdLevel[]
            ).map((level) => (
              <button
                type="button"
                key={level}
                className="report-button"
                onClick={() => submitReport(level)}
              >
                {level}
              </button>
            ))}
          </div>

          {message && (
            <p className="success-message" role="status">
              {message}
            </p>
          )}

          <p className="notice">
            Prototype demonstration only. Reports are stored
            temporarily in browser memory and are not sent
            to the Django backend.
          </p>
        </section>
      ) : (
        // STUDY SPOTS SCREEN
        <>
          <input
            className="search"
            type="text"
            placeholder="Search by building name or code..."
            aria-label="Search study locations"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <h2>Available Study Spots</h2>

          <div className="spots">
            {filteredSpots.map((spot) => (
              <button
                type="button"
                className="spot-card"
                key={spot.id}
                onClick={() => {
                  setSelectedId(spot.id)
                  setMessage('')
                }}
              >
                <div>
                  <h3>{spot.name}</h3>
                  <p>FIU MMC · {spot.building}</p>
                </div>

                <span
                  className={`crowd ${spot.crowd.toLowerCase()}`}
                >
                  {spot.crowd}
                </span>
              </button>
            ))}
          </div>

          {filteredSpots.length === 0 && (
            <p>No study spots found. Try another search.</p>
          )}

          <p className="notice">
            Prototype demonstration: crowd levels are sample
            data, not live reports.
          </p>
        </>
      )}
    </main>
  )
}

export default App
