import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.locations.models import Location


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="jdoe001@fiu.edu", password="Panther#2026")


@pytest.fixture
def library(db):
    return Location.objects.create(
        name="GL 3rd Floor Quiet Study", building="Green Library", latitude=25.7561, longitude=-80.3737
    )
