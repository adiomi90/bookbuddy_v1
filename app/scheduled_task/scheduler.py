from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduled_task.check_overdue import check_overdue_loans
from datetime import datetime

scheduler = AsyncIOScheduler()

scheduler.add_job(check_overdue_loans,
                  trigger="interval",
                  hours=24,
                  next_run_time=datetime.now())
