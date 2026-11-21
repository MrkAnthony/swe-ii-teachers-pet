import datetime as dt
import uuid
from zoneinfo import ZoneInfo

import pytest
from django.urls import include, path, reverse
from rest_framework.test import APIClient

from apps.locations.models import Amenity, Location, LocationAmenity, LocationHours
from apps.locations.services import LocationFilters, LocationNotFound, LocationService

ET = ZoneInfo("America/New_York")

# The API tests load the location URLs through this module (see @pytest.mark.urls
# below), so they don't depend on how config/urls.py is set up.
urlpatterns = [path("api/", include(("apps.locations.urls", "locations")))]


@pytest.fixture(params=["UTC", "America/New_York"], autouse=True)
def django_time_zone(request, settings):
    """Run every test under both a UTC and a local Django TIME_ZONE.

    Opening hours are campus wall-clock times, so results must not change with TIME_ZONE.
    """
    settings.TIME_ZONE = request.param
    return request.param
# 2026-11-16 is a Monday (weekday 0).
MON = dt.date(2026, 11, 16)


def at(day_offset, hh, mm=0):
    return dt.datetime.combine(MON + dt.timedelta(days=day_offset), dt.time(hh, mm), tzinfo=ET)


def make_loc(name, building="GL", **kw):
    kw.setdefault("latitude", 25.756)
    kw.setdefault("longitude", -80.374)
    return Location.objects.create(name=name, building=building, **kw)


@pytest.fixture
def data(db):
    wifi = Amenity.objects.create(name="Wi-Fi", slug="wifi")
    outlets = Amenity.objects.create(name="Outlets", slug="outlets")
    library = make_loc("Green Library 3rd Floor", "Green Library", noise_level="silent", capacity=80)
    lounge = make_loc("Student Lounge", "GC", noise_level="loud", capacity=20, campus="BBC")
    hidden = make_loc("Old Room", "PG5", is_active=False)
    for loc, am in [(library, wifi), (library, outlets), (lounge, wifi), (hidden, wifi)]:
        LocationAmenity.objects.create(location=loc, amenity=am)
    # Library: Mon 07:00 -> Tue 02:00 (overnight). Lounge: Mon 09:00-17:00.
    LocationHours.objects.create(location=library, day_of_week=0, opens_at=dt.time(7), closes_at=dt.time(2))
    LocationHours.objects.create(location=lounge, day_of_week=0, opens_at=dt.time(9), closes_at=dt.time(17))
    return {"library": library, "lounge": lounge, "hidden": hidden}


def names(qs):
    return [loc.name for loc in qs]


def test_search_hides_inactive(data):
    assert names(LocationService.search()) == ["Green Library 3rd Floor", "Student Lounge"]


@pytest.mark.parametrize("q", ["green", "LIBRARY", "  gc "])
def test_keyword_matches_name_or_building_case_insensitive(data, q):
    assert len(LocationService.search(LocationFilters(q=q))) == 1


def test_keyword_escapes_wildcards(data):
    assert names(LocationService.search(LocationFilters(q="%"))) == []


def test_amenities_must_all_match(data):
    assert names(LocationService.search(LocationFilters(amenities=("wifi",)))) == [
        "Green Library 3rd Floor", "Student Lounge",
    ]
    assert names(LocationService.search(LocationFilters(amenities=("wifi", "outlets")))) == [
        "Green Library 3rd Floor"
    ]


def test_noise_campus_capacity(data):
    assert names(LocationService.search(LocationFilters(noise_levels=("silent", "quiet")))) == [
        "Green Library 3rd Floor"
    ]
    assert names(LocationService.search(LocationFilters(campus="bbc"))) == ["Student Lounge"]
    assert names(LocationService.search(LocationFilters(min_capacity=50))) == ["Green Library 3rd Floor"]


@pytest.mark.parametrize(
    "when, expected",
    [
        (at(0, 6, 59), []),                                            # Mon before opening
        (at(0, 10), ["Green Library 3rd Floor", "Student Lounge"]),    # Mon mid-day
        (at(0, 17), ["Green Library 3rd Floor"]),                      # lounge closes at 17:00 (exclusive)
        (at(1, 1, 30), ["Green Library 3rd Floor"]),                   # Tue 01:30 spill-over
        (at(1, 2), []),                                                # Tue 02:00 closed
        (at(6, 10), []),                                               # Sunday: no rows = closed
    ],
)
def test_open_at_sql_and_python_agree(data, when, expected):
    assert names(LocationService.search(LocationFilters(open_at=when))) == expected
    for loc in LocationService.search():
        assert LocationService.open_status(loc, when).is_open == (loc.name in expected)


def test_open_24h_when_opens_equals_closes(db):
    loc = make_loc("24h Lab")
    LocationHours.objects.create(location=loc, day_of_week=0, opens_at=dt.time(0), closes_at=dt.time(0))
    assert names(LocationService.search(LocationFilters(open_at=at(0, 23, 59)))) == ["24h Lab"]
    assert names(LocationService.search(LocationFilters(open_at=at(1, 0)))) == []


def test_open_at_uses_local_time(data):
    # 15:30 UTC on Monday = 10:30 ET -> both open.
    utc = dt.datetime(2026, 11, 16, 15, 30, tzinfo=dt.timezone.utc)
    assert len(LocationService.search(LocationFilters(open_at=utc))) == 2


def test_get_location(data):
    loc = LocationService.get_location(str(data["library"].pk))
    assert [a.slug for a in loc.amenities.all()] == ["outlets", "wifi"]
    for bad in [data["hidden"].pk, uuid.uuid4(), "not-a-uuid"]:
        with pytest.raises(LocationNotFound):
            LocationService.get_location(bad)


def test_search_query_count(data, django_assert_num_queries):
    with django_assert_num_queries(3):  # locations + amenities + hours
        for loc in LocationService.search(LocationFilters(q="g", amenities=("wifi",))):
            list(loc.amenities.all()), list(loc.hours.all())


def test_filter_options(data):
    opts = LocationService.filter_options()
    assert opts["campuses"] == ["BBC", "MMC"]
    assert [a["slug"] for a in opts["amenities"]] == ["outlets", "wifi"]


def test_naive_datetime_is_campus_time(data):
    naive_7_30am = dt.datetime(2026, 11, 16, 7, 30)
    assert names(LocationService.search(LocationFilters(open_at=naive_7_30am))) == [
        "Green Library 3rd Floor"
    ]


# ---- API wiring ---------------------------------------------------------

@pytest.mark.urls(__name__)
def test_open_at_query_param_without_offset_is_campus_time(data):
    r = APIClient().get(reverse("locations:location-list"), {"open_at": "2026-11-16T07:30:00"})
    assert r.status_code == 200
    assert [x["name"] for x in r.data["results"]] == ["Green Library 3rd Floor"]


@pytest.mark.urls(__name__)
def test_list_endpoint(data):
    c = APIClient()
    r = c.get(reverse("locations:location-list"), {"amenities": "wifi,outlets", "q": "green"})
    assert r.status_code == 200
    assert [x["name"] for x in r.data["results"]] == ["Green Library 3rd Floor"]

    r = c.get(reverse("locations:location-list"), {"noise_level": "deafening"})
    assert r.status_code == 400 and "noise_level" in r.data


@pytest.mark.urls(__name__)
def test_list_endpoint_pagination(db):
    for i in range(3):
        make_loc(f"Room {i}")
    r = APIClient().get(reverse("locations:location-list"), {"page_size": 2})
    assert r.status_code == 200
    assert r.data["count"] == 3
    assert len(r.data["results"]) == 2
    assert r.data["next"] is not None


@pytest.mark.urls(__name__)
def test_detail_endpoint(data):
    c = APIClient()
    r = c.get(reverse("locations:location-detail", args=[data["library"].pk]))
    assert r.status_code == 200
    assert r.data["hours"][0]["day"] == "Monday"
    assert c.get(reverse("locations:location-detail", args=[data["hidden"].pk])).status_code == 404