import pytest

from apps.locations.models import Location
from apps.reviews.models import Review

pytestmark = pytest.mark.django_db

URL = "/api/reviews/"


def make_student(django_user_model, n):
    return django_user_model.objects.create_user(email=f"student{n}@fiu.edu", password="Panther#2026")


def test_get_reviews_for_location(client, django_user_model, library):
    Review.objects.create(user=make_student(django_user_model, 1), location=library, rating=5, comment="Super quiet")
    Review.objects.create(user=make_student(django_user_model, 2), location=library, rating=3, comment="Not many outlets")
    Review.objects.create(user=make_student(django_user_model, 3), location=library, rating=1, comment="spam", is_visible=False)

    res = client.get(URL, {"location": library.id})
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 2  # hidden review not shown
    assert data["average_rating"] == 4.0
    assert data["results"][0]["comment"] == "Not many outlets"  # newest first


def test_get_reviews_no_reviews_yet(client, library):
    data = client.get(URL, {"location": library.id}).json()
    assert data == {"count": 0, "average_rating": None, "results": []}


@pytest.mark.parametrize("param", [{}, {"location": "abc"}])
def test_get_reviews_bad_location(client, param):
    assert client.get(URL, param).status_code == 400


def test_post_review(client, student, library):
    client.force_authenticate(student)
    res = client.post(URL, {"location": library.id, "rating": 4, "comment": "Good wifi"}, format="json")
    assert res.status_code == 201
    assert res.json()["rating"] == 4
    assert "user" not in res.json()
    assert Review.objects.get().user == student


def test_post_review_needs_login(client, library):
    res = client.post(URL, {"location": library.id, "rating": 4}, format="json")
    assert res.status_code in (401, 403)
    assert Review.objects.count() == 0


@pytest.mark.parametrize("rating", [0, 6, "", "five"])
def test_post_review_bad_rating(client, student, library, rating):
    client.force_authenticate(student)
    res = client.post(URL, {"location": library.id, "rating": rating}, format="json")
    assert res.status_code == 400
    assert Review.objects.count() == 0


def test_one_review_per_location(client, student, library):
    client.force_authenticate(student)
    client.post(URL, {"location": library.id, "rating": 4}, format="json")
    res = client.post(URL, {"location": library.id, "rating": 2}, format="json")
    assert res.status_code == 400
    assert Review.objects.count() == 1


def test_review_inactive_location(client, student):
    closed = Location.objects.create(
        name="PG6 Lounge", building="PG6", latitude=25.7570, longitude=-80.3720, is_active=False
    )
    client.force_authenticate(student)
    res = client.post(URL, {"location": closed.id, "rating": 4}, format="json")
    assert res.status_code == 400
