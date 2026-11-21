import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()

REGISTER = "/api/accounts/register/"
LOGIN = "/api/accounts/login/"
LOGOUT = "/api/accounts/logout/"
ME = "/api/accounts/me/"
GOOD_PASSWORD = "Panther#2026"


def test_register_with_fiu_email(client):
    res = client.post(REGISTER, {"email": "MBrown045@fiu.edu", "password": GOOD_PASSWORD}, format="json")
    assert res.status_code == 201
    assert res.json()["email"] == "mbrown045@fiu.edu"
    assert res.json()["role"] == "student"
    assert "password" not in res.json()

    user = User.objects.get()
    assert user.check_password(GOOD_PASSWORD)  # saved hashed, not plain text


def test_register_needs_fiu_email(client):
    res = client.post(REGISTER, {"email": "mbrown@gmail.com", "password": GOOD_PASSWORD}, format="json")
    assert res.status_code == 400
    assert "email" in res.json()


def test_register_same_email_twice(client, student):
    res = client.post(REGISTER, {"email": "JDOE001@fiu.edu", "password": GOOD_PASSWORD}, format="json")
    assert res.status_code == 400


def test_register_weak_password(client):
    res = client.post(REGISTER, {"email": "mbrown045@fiu.edu", "password": "12345"}, format="json")
    assert res.status_code == 400
    assert "password" in res.json()


def test_cant_make_yourself_admin(client):
    res = client.post(REGISTER, {"email": "mbrown045@fiu.edu", "password": GOOD_PASSWORD, "role": "it"}, format="json")
    assert res.status_code == 201
    assert User.objects.get().role == "student"


def test_login_and_me(client, student):
    res = client.post(LOGIN, {"email": "jdoe001@fiu.edu", "password": "Panther#2026"}, format="json")
    assert res.status_code == 200
    assert res.json()["email"] == "jdoe001@fiu.edu"

    me = client.get(ME)
    assert me.status_code == 200
    assert me.json()["email"] == "jdoe001@fiu.edu"


def test_login_wrong_password(client, student):
    res = client.post(LOGIN, {"email": "jdoe001@fiu.edu", "password": "wrong"}, format="json")
    assert res.status_code == 400
    assert client.get(ME).status_code in (401, 403)


def test_me_needs_login(client):
    assert client.get(ME).status_code in (401, 403)


def test_logout(client, student):
    client.post(LOGIN, {"email": "jdoe001@fiu.edu", "password": "Panther#2026"}, format="json")
    assert client.post(LOGOUT).status_code == 204
    assert client.get(ME).status_code in (401, 403)
