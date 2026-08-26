import pytest


@pytest.mark.asyncio
async def test_register_new_user(async_client):
    payload = {
        "first_name": "Max",
        "last_name": "Ink",
        "email": "user@example.com",
        "password": "string"
    }

    response = await async_client.post("/auth/registration",
                                       json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "user@example.com"
    assert data["first_name"] == "Max"

    assert "password" not in data
    assert "password_hash" not in data
    assert "token" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client, test_user):
    payload = {
        "first_name": "Max",
        "last_name": "Ink",
        "email": "user@test.com",
        "password": "string"
    }

    response = await async_client.post("/auth/registration",
                                       json=payload)

    assert response.status_code == 409

    data = response.json()
    assert "email" in data["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(async_client, test_user):
    login_data = {
        "username": test_user.email,
        "password": "test-password"
    }

    response = await async_client.post("/auth/login",
                                       data=login_data)

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_unathenticated_access_denied(async_client):
    response = await async_client.get("/loans/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_access_allowed(async_client, test_user):
    login_data = {
        "username": test_user.email,
        "password": "test-password"
    }

    login_response = await async_client.post("/auth/login",
                                             data=login_data)

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = await async_client.get("/loans/me", headers=headers)

    assert response.status_code == 200

