from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduled_task.check_overdue import check_overdue_loans
from app.scheduled_task.reservation_tasks import expire_old_reservations
from datetime import datetime, timezone

scheduler = AsyncIOScheduler()

scheduler.add_job(check_overdue_loans,
                  trigger="interval",
                  hours=24,
                  next_run_time=datetime.now(timezone.utc))

scheduler.add_job(expire_old_reservations,
                  trigger="interval",
                  hours=1,
                  next_run_time=datetime.now(timezone.utc))
