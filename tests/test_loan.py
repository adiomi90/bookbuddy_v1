async def test_db_connection(async_client):
    response = await async_client.get("/loans/db-test")

    assert response.status_code == 200
    assert response.json() == {"database": "connected"}


async def test_user_fixture(test_user):
    assert test_user.first_name == "Test"
    assert test_user.last_name == "User"
    assert test_user.email == "user@test.com"
    assert test_user.is_admin is False

