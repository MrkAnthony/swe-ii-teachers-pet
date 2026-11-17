from datetime import timedelta

import pytest
from django.utils import timezone

from apps.crowd_reports.models import CrowdReport
from apps.locations.models import Location

pytestmark = pytest.mark.django_db

URL = "/api/crowd-reports/"
FAKE_ID = "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed"


def status_url(location):
    return f"/api/crowd-reports/status/{location.id}/"


def add_report(user, location, level, minutes_ago):
    report = CrowdReport.objects.create(user=user, location=location, level=level)
    report.reported_at = timezone.now() - timedelta(minutes=minutes_ago)
    report.save()
    return report


def other_student(django_user_model, n):
    return django_user_model.objects.create_user(email=f"student{n}@fiu.edu", password="Panther#2026")


# TC-01
def test_health_check(client):
    res = client.get("/api/health/")
    assert res.status_code == 200
    assert res.json() == {"database": "ok", "cache": "ok"}


# TC-02
def test_submit_report(client, student, library):
    client.force_authenticate(student)
    res = client.post(URL, {"location": library.id, "level": "packed"}, format="json")
    assert res.status_code == 201
    assert res.json()["level"] == "packed"
    assert CrowdReport.objects.get().user == student


# TC-03
def test_must_be_logged_in(client, library):
    res = client.post(URL, {"location": library.id, "level": "empty"}, format="json")
    assert res.status_code in (401, 403)
    assert CrowdReport.objects.count() == 0


# TC-04
@pytest.mark.parametrize("level", ["full", "", "PACKED", "3"])
def test_invalid_level(client, student, library, level):
    client.force_authenticate(student)
    res = client.post(URL, {"location": library.id, "level": level}, format="json")
    assert res.status_code == 400
    assert CrowdReport.objects.count() == 0


# TC-05
def test_unknown_or_inactive_location(client, student):
    closed = Location.objects.create(
        name="PG6 Lounge", building="PG6", latitude=25.7570, longitude=-80.3720, is_active=False
    )
    client.force_authenticate(student)
    assert client.post(URL, {"location": FAKE_ID, "level": "empty"}, format="json").status_code == 400
    assert client.post(URL, {"location": closed.id, "level": "empty"}, format="json").status_code == 400
    assert CrowdReport.objects.count() == 0


# TC-06
def test_cant_report_twice_in_10_minutes(client, student, library):
    client.force_authenticate(student)
    first = client.post(URL, {"location": library.id, "level": "moderate"}, format="json")
    second = client.post(URL, {"location": library.id, "level": "empty"}, format="json")
    assert first.status_code == 201
    assert second.status_code == 429
    assert CrowdReport.objects.count() == 1


# TC-07
def test_old_reports_ignored(client, django_user_model, library):
    add_report(other_student(django_user_model, 1), library, "packed", 50)
    add_report(other_student(django_user_model, 2), library, "moderate", 30)
    add_report(other_student(django_user_model, 3), library, "empty", 5)

    data = client.get(status_url(library)).json()
    assert data["level"] == "empty"
    assert data["report_count"] == 2


# TC-08
def test_no_recent_reports(client, library):
    data = client.get(status_url(library)).json()
    assert data["level"] is None
    assert data["level_label"] == "No recent reports"


# TC-09
def test_status_cached_and_updated(client, student, library, django_user_model, django_assert_num_queries):
    add_report(other_student(django_user_model, 1), library, "empty", 20)
    client.get(status_url(library))

    # second load: only the location lookup goes to postgres, the rest comes from redis
    with django_assert_num_queries(1):
        assert client.get(status_url(library)).json()["level"] == "empty"

    client.force_authenticate(student)
    client.post(URL, {"location": library.id, "level": "packed"}, format="json")
    assert client.get(status_url(library)).json()["level"] == "packed"


# TC-11
def test_reporter_not_shown(client, student, library):
    client.force_authenticate(student)
    res = client.post(URL, {"location": library.id, "level": "packed"}, format="json")
    assert "user" not in res.json()
    assert "user" not in client.get(status_url(library)).json()
