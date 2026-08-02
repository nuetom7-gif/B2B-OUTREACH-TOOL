try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover - keeps the app/test bootstrap working without APScheduler installed
    BackgroundScheduler = None  # type: ignore[assignment]

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.discovery.engine import run_discovery_cycle

settings = get_settings()
scheduler = BackgroundScheduler(timezone="UTC", job_defaults={"coalesce": True, "max_instances": 1}) if BackgroundScheduler else None


def _run_discovery_job():
    db = SessionLocal()
    try:
        run_discovery_cycle(db)
    finally:
        db.close()


def start_scheduler():
    if scheduler is None:
        return None
    if not settings.enable_automation_scheduler:
        return None
    if scheduler.running:
        return scheduler
    scheduler.add_job(
        _run_discovery_job,
        "cron",
        hour=settings.discovery_schedule_hour_utc,
        minute=settings.discovery_schedule_minute_utc,
        id="discovery-cycle",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    # APScheduler is the lighter single-server option, which fits Phase 1/4 better than Celery for now.
    scheduler.start()
    return scheduler


def stop_scheduler():
    if scheduler is None:
        return None
    if scheduler.running:
        scheduler.shutdown(wait=False)
    return scheduler
