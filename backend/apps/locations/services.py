"""
Location service layer (Application / Business Logic Layer, Deliverable 2 §2.1.10.3).

Views stay thin: they validate HTTP input, call into ``LocationService`` and
serialize the result. All query and business rules for FR-01 (search & filter)
and FR-02 (location details) live here, so they can be unit-tested and reused by
other services (e.g. RecommendationService) without going through HTTP.

This module does not import DRF on purpose.
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from django.conf import settings

from django.db.models import Exists, F, OuterRef, Prefetch, Q, QuerySet
from django.db.models.functions import Lower
from django.utils import timezone

from .models import Amenity, Location, LocationHours


class LocationNotFound(Exception):
    """Raised when a location does not exist or is not publicly visible."""


@dataclass(frozen=True)
class LocationFilters:
    """Validated search/filter options for FR-01 / UC-01 (all optional)."""

    q: str = ""
    noise_levels: tuple[str, ...] = ()
    campus: str = ""
    amenities: tuple[str, ...] = ()  # amenity slugs; a location must have ALL of them
    min_capacity: int | None = None
    open_at: dt.datetime | None = None  # "open now" = pass timezone.now()

    def is_empty(self) -> bool:
        return self == LocationFilters()


@dataclass(frozen=True)
class OpenStatus:
    is_open: bool
    closes_at: dt.time | None = None


def campus_tz() -> ZoneInfo:
    """
    Time zone that LocationHours are written in (wall-clock time on campus).

    Deliberately independent of Django's TIME_ZONE, which is often "UTC": an
    opening time of 07:00 means 7 AM in Miami, not 7 AM UTC.
    Override with LOCATIONS_TIME_ZONE in settings if ever needed.
    """
    return ZoneInfo(getattr(settings, "LOCATIONS_TIME_ZONE", "America/New_York"))


def _local(when: dt.datetime | None) -> dt.datetime:
    """Convert ``when`` to campus wall-clock time. Naive datetimes are assumed to be campus time."""
    when = when or timezone.now()
    if timezone.is_naive(when):
        return when.replace(tzinfo=campus_tz())
    return when.astimezone(campus_tz())


class LocationService:
    """Read-side operations on official study locations."""

    # ---- Querysets -------------------------------------------------------

    @staticmethod
    def public_queryset() -> QuerySet[Location]:
        """Locations a student/guest may see. Deactivated ones are hidden but kept."""
        return Location.objects.filter(is_active=True)

    @classmethod
    def _with_related(cls, qs: QuerySet[Location]) -> QuerySet[Location]:
        return qs.prefetch_related(
            Prefetch("amenities", queryset=Amenity.objects.order_by("name")),
            Prefetch("hours", queryset=LocationHours.objects.order_by("day_of_week")),
        )

    # ---- FR-01: search & filter -----------------------------------------

    @classmethod
    def search(cls, filters: LocationFilters | None = None) -> QuerySet[Location]:
        """
        Return active locations matching ``filters``, ordered by name.

        An empty result is a normal outcome (the UI shows MSG-01 "No Locations Found").
        """
        filters = filters or LocationFilters()
        qs = cls.public_queryset()

        if filters.q:
            qs = cls._apply_keyword(qs, filters.q)
        if filters.noise_levels:
            qs = qs.filter(noise_level__in=filters.noise_levels)
        if filters.campus:
            qs = qs.filter(campus__iexact=filters.campus)
        if filters.min_capacity is not None:
            qs = qs.filter(capacity__gte=filters.min_capacity)
        for slug in filters.amenities:
            # One EXISTS per amenity = "has all of these" without JOIN duplicates / DISTINCT.
            qs = qs.filter(
                Exists(
                    Location.amenities.through.objects.filter(
                        location=OuterRef("pk"), amenity__slug=slug
                    )
                )
            )
        if filters.open_at is not None:
            qs = qs.filter(cls._open_at_condition(filters.open_at))

        return cls._with_related(qs).order_by("name", "building")

    @staticmethod
    def _apply_keyword(qs: QuerySet[Location], term: str) -> QuerySet[Location]:
        """
        Case-insensitive substring match on name OR building.

        Filtering on ``Lower(col) LIKE '%term%'`` (rather than ``icontains``, which
        Postgres renders as ``UPPER(col) LIKE``) matches the expression used by the
        ``loc_name_trgm_idx`` / ``loc_building_trgm_idx`` GIN indexes, so they get used.
        ``__contains`` escapes ``%`` and ``_`` in user input.
        """
        term = term.strip().lower()
        if not term:
            return qs
        return qs.annotate(_name_lc=Lower("name"), _building_lc=Lower("building")).filter(
            Q(_name_lc__contains=term) | Q(_building_lc__contains=term)
        )

    # ---- Opening hours ---------------------------------------------------

    @staticmethod
    def _open_at_condition(when: dt.datetime) -> Exists:
        """
        SQL condition: location is open at ``when``.

        A LocationHours row (day D, opens O, closes C) covers:
          * normal day      (C > O): D at [O, C)
          * past midnight   (C <= O): D at [O, 24:00) and D+1 at [00:00, C)
            (C == O therefore means open 24h.)
        """
        local = _local(when)
        today, t = local.weekday(), local.time()
        yesterday = (today - 1) % 7

        same_day = Q(day_of_week=today, opens_at__lte=t) & (
                Q(closes_at__gt=t) | Q(closes_at__lte=F("opens_at"))
        )
        spill_over = Q(day_of_week=yesterday, closes_at__lte=F("opens_at"), closes_at__gt=t)

        return Exists(
            LocationHours.objects.filter(location=OuterRef("pk")).filter(same_day | spill_over)
        )

    @staticmethod
    def open_status(location: Location, when: dt.datetime | None = None) -> OpenStatus:
        """
        Python mirror of ``_open_at_condition`` for a single, already-loaded location.
        Uses ``location.hours.all()`` so it is free when hours were prefetched.
        """
        local = _local(when)
        today, t = local.weekday(), local.time()
        yesterday = (today - 1) % 7

        for h in location.hours.all():
            overnight = h.closes_at <= h.opens_at
            if h.day_of_week == today and h.opens_at <= t and (overnight or t < h.closes_at):
                return OpenStatus(True, h.closes_at)
            if h.day_of_week == yesterday and overnight and t < h.closes_at:
                return OpenStatus(True, h.closes_at)
        return OpenStatus(False)

    # ---- FR-02: details --------------------------------------------------

    @classmethod
    def get_location(cls, location_id: uuid.UUID | str) -> Location:
        """
        Fetch one active location with amenities and hours prefetched.
        Raises ``LocationNotFound`` for unknown, malformed or deactivated IDs.
        """
        try:
            location_id = uuid.UUID(str(location_id))
        except (TypeError, ValueError) as exc:
            raise LocationNotFound(location_id) from exc
        try:
            return cls._with_related(cls.public_queryset()).get(pk=location_id)
        except Location.DoesNotExist as exc:
            raise LocationNotFound(location_id) from exc

    # ---- Filter options for the SearchFilters component ------------------

    @classmethod
    def filter_options(cls) -> dict:
        """Values the frontend can offer as filters (only ones that will return results)."""
        active = cls.public_queryset()
        return {
            "campuses": list(active.order_by("campus").values_list("campus", flat=True).distinct()),
            "noise_levels": [
                {"value": v, "label": label}
                for v, label in Location._meta.get_field("noise_level").choices
            ],
            "amenities": list(
                Amenity.objects.filter(locations__is_active=True)
                .distinct()
                .order_by("name")
                .values("slug", "name")
            ),
        }