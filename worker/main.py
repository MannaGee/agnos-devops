import json
import os
import time
from datetime import datetime, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
import structlog

# --- Structured JSON logger setup (same as API) ---
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

ENV = os.getenv("APP_ENV", "dev")
DATA_FILE = "/tmp/records.json"


def load_records():
    """Load today's records from the JSON file, or create them if missing."""
    if not os.path.exists(DATA_FILE):
        # Simulate 3 records that exist for today
        return [
            {"id": 1, "date": str(datetime.now(timezone.utc).date()), "last_updated": None},
            {"id": 2, "date": str(datetime.now(timezone.utc).date()), "last_updated": None},
            {"id": 3, "date": str(datetime.now(timezone.utc).date()), "last_updated": None},
        ]
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def update_today_timestamps():
    """
    Core worker job:
    Find all records where date == today, update their last_updated timestamp.
    This simulates what a real worker would do against a database.
    """
    logger.info("worker_job_start", env=ENV)
    today = str(datetime.now(timezone.utc).date())
    records = load_records()

    updated_count = 0
    for record in records:
        if record.get("date") == today:
            record["last_updated"] = datetime.now(timezone.utc).isoformat()
            updated_count += 1

    # Persist back to file
    with open(DATA_FILE, "w") as f:
        json.dump(records, f, indent=2)

    logger.info("worker_job_done", updated_records=updated_count, env=ENV)


if __name__ == "__main__":
    logger.info("worker_startup", env=ENV)

    # Run once immediately on startup
    update_today_timestamps()

    # Then schedule to run every 60 seconds
    scheduler = BlockingScheduler()
    scheduler.add_job(update_today_timestamps, "interval", seconds=60)
    scheduler.start()
