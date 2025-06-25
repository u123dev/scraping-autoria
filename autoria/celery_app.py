import os
from celery import Celery
from celery.schedules import crontab


app = Celery("autoria",
             broker=os.getenv("CELERY_BROKER_URL"),
             backend=os.getenv("CELERY_RESULT_BACKEND"),
             include=["autoria.tasks"])

app.conf.beat_schedule = {
    "run-scrapy-spider-daily": {
        "task": "autoria.tasks.run_scrapy_spider",
        "schedule": crontab(hour=12, minute=00),
        "args": ("usedcars",)
    },
    "run-db-backup-daily": {
        "task": "autoria.tasks.run_db_backup",
        "schedule": crontab(hour=12, minute=00),
    },
}
app.conf.timezone = os.getenv("TZ", "UTC")
app.conf.broker_connection_retry_on_startup = True
