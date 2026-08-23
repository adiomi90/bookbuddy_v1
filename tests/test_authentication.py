async def test_unauthenticated_user_is_rejected(async_client):
    response =  await async_client.get("/users/db-test")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}



async def test_user_can_login(async_client, test_user):
    response = await async_client.post(
        "/auth/login",
        data={
            "username": test_user.email,
            "password": "test-password"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
