from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reservation import Reservation as ReservationModel
from app.database.database import SessionLocal


async def expire_old_reservations():
    async with SessionLocal() as db:
        now = datetime.now(timezone.utc)

        query = select(ReservationModel).where(
            ReservationModel.status == "ready",
            ReservationModel.expires_at < now
        )

        result = await db.execute(query)
        expired_reservations = result.scalars().all()

        for reservation in expired_reservations:
            reservation.status = "expired"

        if expired_reservations:
            await db.commit()
            print(f"Background Task: Expired {len(expired_reservations)} reservations.")
        else:
            print("Background Task: No reservation to expire")
