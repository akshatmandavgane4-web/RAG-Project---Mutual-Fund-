import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Ensure project root is in python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Setup logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "scheduler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DailyScheduler")

# Stream logs to console as well
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

def run_ingestion():
    logger.info("Triggering ingestion pipeline run...")
    start_time = datetime.now()
    
    # Import locally to prevent early module loading issues before model/db are initialized
    try:
        from ingestion.run import main as run_pipeline
        run_pipeline()
        duration = datetime.now() - start_time
        logger.info(f"Ingestion pipeline completed successfully in {duration.total_seconds():.2f} seconds.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        # Retry once after a brief delay
        logger.info("Attempting retry in 30 seconds...")
        time.sleep(30)
        try:
            from ingestion.run import main as run_pipeline
            run_pipeline()
            duration = datetime.now() - start_time
            logger.info(f"Ingestion pipeline completed successfully on retry in {duration.total_seconds():.2f} seconds.")
        except Exception as retry_err:
            logger.critical(f"Ingestion pipeline retry failed critically: {retry_err}")

def get_seconds_until_target(target_hour: int = 10, target_minute: int = 0) -> float:
    # Calculate seconds until the next occurrence of target_hour:target_minute in IST timezone
    ist_tz = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(ist_tz)
    
    target_time_ist = now_ist.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if target_time_ist <= now_ist:
        target_time_ist += timedelta(days=1)
    
    delta = target_time_ist - now_ist
    return delta.total_seconds()

def main():
    logger.info("Daily Ingestion Scheduler started.")
    
    # Run once on startup to verify pipeline integration
    logger.info("Performing initial startup pipeline execution verification...")
    run_ingestion()
    
    # Schedule runs once per day at target hour (10:00 AM IST)
    target_hour = 10
    target_minute = 0
    
    logger.info(f"Scheduling daily runs for {target_hour:02d}:{target_minute:02d} IST.")
    
    while True:
        try:
            sleep_secs = get_seconds_until_target(target_hour, target_minute)
            logger.info(f"Sleeping for {sleep_secs:.1f} seconds (approx. {sleep_secs / 3600:.2f} hours) until next scheduled run.")
            time.sleep(sleep_secs)
            run_ingestion()
        except KeyboardInterrupt:
            logger.info("Scheduler received shutdown signal. Exiting.")
            break
        except Exception as e:
            logger.error(f"Scheduler loop encountered error: {e}. Re-entering loop in 60 seconds.")
            time.sleep(60)

if __name__ == "__main__":
    main()
