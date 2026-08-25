import pytest
from sqlalchemy import select
from app.models.book import Book as BookModel


@pytest.mark.asyncio
async def test_admin_can_create_loan(
        async_client,
        test_user,
        test_admin,
        sample_book,
        test_session_factory):
    login_data = {
        "username": test_admin.email,
        "password": "admin-password"
    }

    login_response = await async_client.post("/auth/login",
                                             data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    loan_data = {
        "book_id": sample_book.id,
        "duration": 7
    }

    response = await async_client.post(
        f"/loans/{test_user.id}",
        json=loan_data,
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "borrowed"
    assert data["user"]["id"] == test_user.id
    assert data["book"]["id"] == sample_book.id

    async with test_session_factory() as db:
        result = await db.execute(
            select(BookModel).where(BookModel.id == sample_book.id)
        )

        updated_book = result.scalar_one()

        assert updated_book.quantity == 2


@pytest.mark.asyncio
async def test_reject_out_of_stock(
        async_client,
        test_user,
        test_admin,
        out_of_stock_book,
        test_session_factory):
    login_data = {
        "username": test_admin.email,
        "password": "admin-password"
    }

    login_response = await async_client.post("/auth/login",
                                             data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    loan_data = {
        "book_id": out_of_stock_book.id,
        "duration": 7
    }

    response = await async_client.post(
        f"/loans/{test_user.id}",
        json=loan_data,
        headers=headers
    )

    assert response.status_code == 409
