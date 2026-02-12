import time
import logging
from scheduler.imc_scheduler import run_imc_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def start_scheduler():
    logging.info("Starting IMC Scheduler (Continuous Forward Blocks)")
    cycle_counter = 1
    while True:
        try:
            run_imc_scheduler(cycle_num=cycle_counter)
            cycle_counter += 1
        except Exception:
            logging.exception("Scheduler crashed")
            time.sleep(5)

if __name__ == "__main__":
    start_scheduler()