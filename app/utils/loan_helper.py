from datetime import datetime, timezone
from app.models.loan import Loan as LoanModel


def calculate_loan_fine(loan):
    now = datetime.now(timezone.utc)

    if loan.due_date >= now:
        return 0, 0.0

    days_overdue = (now - loan.due_date).days
    days_after_grace_period = max(0, days_overdue - 3)

    fine = days_after_grace_period * 0.50
    final_fine = min(10, fine)

    return days_overdue, final_fine


def loan_with_fine(loan: LoanModel):
    days_overdue, fine_amount = calculate_loan_fine(loan)
    return {
        "id": loan.id,
        "user": loan.user,
        "book": loan.book,
        "status": loan.status,
        "due_date": loan.due_date,
        "returned_date": loan.returned_date,
        "borrowed_date": loan.borrowed_date,
        "renewal_count": loan.renewal_count,
        "days_overdue": days_overdue,
        "fine_amount": fine_amount,
        "created_at": loan.created_at,
        "updated_at": loan.updated_at
    }
