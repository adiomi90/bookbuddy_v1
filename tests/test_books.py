import pytest
from app.models.book import Book


@pytest.mark.asyncio
async def test_admin_can_create_book(
        async_client,
        test_user,
        test_admin,
        sample_book,
        test_session_factory):
    login_data = {
        "username": test_admin.email,
        "password": "admin-password"
    }

    login_response = await async_client.post("/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    book = {
        "title": "Test Book",
        "author": "Author",
        "isbn": "isbn-copy",
        "publisher": "Publisher",
        "publisher_year": 2020,
        "summary": "Test Another book"
    }

    response = await async_client.post(
        "/books/",
        json=book,
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Author"
    assert data["isbn"] == "isbn-copy"
    assert data["publisher"] == "Publisher"
    assert data["publisher_year"] == 2020
    assert data["summary"] == "Test Another book"
    assert data["quantity"] == 0
