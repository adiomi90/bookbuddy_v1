from app.database.database import SessionLocal
from app.models.loan import Loan as LoanModel
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError


async def check_overdue_loans():
    try:
        async with SessionLocal() as db:
            now = datetime.now(timezone.utc)
            query = await db.execute(
                select(LoanModel)
                .where(
                    LoanModel.status == "borrowed",
                    LoanModel.due_date < now
                )
            )

            overdue_loans = query.scalars().all()

            for loan in overdue_loans:
                loan.status = "overdue"

            if overdue_loans:
                await db.commit()
                print(f"Scheduler: Marked {len(overdue_loans)} loans as overdue")
            else:
                print("Scheler: No overdue loans found.")
    except ProgrammingError as e:
        print(f"Database not ready or tables missing(Schehler will retry later)")
    except Exception as e:
        print(f"Unexcpted error in check_overdue_loans: {e}")
