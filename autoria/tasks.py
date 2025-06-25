import os
from autoria.celery_app import app
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import subprocess
from datetime import datetime


@app.task(queue="scrapy_tasks")
def run_scrapy_spider(spider_name):
    project_root = "/app"

    cmd = [
        "scrapy",
        "crawl",
        spider_name
    ]

    scrapy_env = os.environ.copy()
    scrapy_env['SCRAPY_SETTINGS_MODULE'] = 'autoria.settings'
    scrapy_env['PYTHONPATH'] = project_root + ":" + scrapy_env.get('PYTHONPATH', '')  # add '/app' to PYTHONPATH

    print(f"Starting Scrapy spider '{spider_name}' via subprocess...")
    try:
        result = subprocess.run(cmd, cwd=project_root, env=scrapy_env, check=True, capture_output=True, text=True)
        print(f"Scrapy spider '{spider_name}' finished successfully.")
        if result.stdout:
            print("Scrapy stdout:\n", result.stdout)
        if result.stderr:
            print("Scrapy stderr:\n", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Scrapy spider '{spider_name}' failed!", flush=True)
        print(f"Error output:\n{e.stderr}", flush=True)
        raise # to Celery
    except Exception as e:
        print(f"An unexpected error occurred while running Scrapy: {e}", flush=True)
        raise # to Celery

# single task
@app.task(queue="scrapy_tasks")
def run_scrapy_spider_solo(spider_name):
    print(f"Starting Scrapy spider '{spider_name}'...")
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(spider_name)
    process.start()
    print(f"Scrapy spider '{spider_name}' finished.")

@app.task(queue="backup_tasks")
def run_db_backup():
    db_name = os.getenv('POSTGRES_DB')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    db_host = os.getenv('POSTGRES_HOST')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/app/backups/db_backup_{timestamp}.sql"

    os.environ['PGPASSWORD'] = db_password # set PGPASSWORD for pg_dump

    cmd = [
        "pg_dump",
        "-h", db_host,
        "-U", db_user,
        "-d", db_name,
        # "-Fc", # Compressed format
        "-Fp",  # Plain format
        "-v",
        "-f", backup_file
    ]

    try:
        print(f"Starting PostgreSQL backup to {backup_file}...")
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Backup successful: {backup_file}")

        # clean dumps older than 7days
        subprocess.run(["find", "/app/backups", "-type", "f", "-name", "*.sql", "-mtime", "+7", "-delete"], check=False)
        print("Old backups cleaned up.")
    except subprocess.CalledProcessError as e:
        print(f"Backup failed! Error: {e.stderr.decode()}", flush=True)
    except Exception as e:
        print(f"An unexpected error occurred during backup: {e}", flush=True)
    finally:
        del os.environ['PGPASSWORD'] # unset PGPASSWORD
