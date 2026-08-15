from app.database.database import SessionLocal
from app.models.loan import Loan as LoanModel
from datetime import datetime
from sqlalchemy import select


async def check_overdue_loans():
    async with SessionLocal() as db:
        query = await db.execute(select(LoanModel)
                                 .where(LoanModel.status == "borrowed",
                                        LoanModel.due_date < datetime.now()))

        over_due_loans = query.scalars()
        for over_due_loan in over_due_loans:
            over_due_loan.status = "overdue"

        await db.commit()
