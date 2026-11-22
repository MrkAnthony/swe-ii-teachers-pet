import './LocationMap.css'

type Props = {
  name: string
  latitude: string | number | null
  longitude: string | number | null
}

export default function LocationMap({
  name,
  latitude,
  longitude,
}: Props) {
  const lat = Number(latitude)
  const lng = Number(longitude)

  const hasCoordinates =
    latitude !== null &&
    longitude !== null &&
    Number.isFinite(lat) &&
    Number.isFinite(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180 &&
    !(lat === 0 && lng === 0)

  let destination = ''

  if (hasCoordinates) {
    destination = `${lat},${lng}`
  } else if (name.startsWith('Green Library')) {
    destination = 'Green Library, Florida International University, Miami, FL'
  } else if (name.startsWith('Graham Center')) {
    destination = 'Ernest R. Graham Center, Florida International University, Miami, FL'
  } else if (name.startsWith('Academic Health Center')) {
    destination = 'Academic Health Center 1, 1250 SW 108th Avenue, Miami, FL 33199'
  } else if (name.startsWith('Engineering Center')) {
    destination = 'FIU Engineering Center, Miami, FL'
  }

  if (!destination) {
    return (
      <section className="location-map">
        <h3>Map & Navigation</h3>
        <p>
          The exact building for this study area has not been confirmed yet.
        </p>
      </section>
    )
  }

  const encoded = encodeURIComponent(destination)

  const mapUrl =
    `https://maps.google.com/maps?q=${encoded}&z=17&output=embed`

  const directionsUrl =
    `https://www.google.com/maps/dir/?api=1&destination=${encoded}`

  return (
    <section className="location-map">
      <h3>Map & Navigation</h3>

      <p>
        View the building on the map or get directions.
        Check the location details for the correct floor.
      </p>

      <iframe
        title={`Map of ${name}`}
        src={mapUrl}
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
      />

      <a
        href={directionsUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="directions-button"
      >
        Get Directions
      </a>
    </section>
  )
}
