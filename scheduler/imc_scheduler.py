import time
import logging
import re
from datetime import datetime, timedelta
from imc_categorization_consumer.adapter.outlook_adapter import fetch_imc_emails
from producer.imc_producer import publish_email
from common.config.settings import EMAIL_FETCH_LIMIT
from scheduler.state_manager import get_last_processed_timestamp, update_last_processed_timestamp
from scheduler.aged_incident_detector import check_aged_incidents

def _extract_trap_time(body):
    match = re.search(r'Trap Time:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', body, re.IGNORECASE)
    if match: return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    return datetime.max

def run_imc_scheduler(cycle_num=1):
    start_time = get_last_processed_timestamp()
    end_time = start_time + timedelta(minutes=15)
    
    start_str = start_time.strftime("%H:%M")
    end_str = end_time.strftime("%H:%M")
    print(f"\n[SCHEDULER] --- Cycle {cycle_num} Started ({start_str} to {end_str}) ---")
    
    processed_ids = set()
    
    while datetime.now() < end_time:
        emails = fetch_imc_emails(
            limit=EMAIL_FETCH_LIMIT,
            start_date=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        new_emails = [e for e in emails if e.message_id not in processed_ids]
        
        if new_emails:
            new_emails.sort(key=lambda e: _extract_trap_time(e.body))
            print(f"[SCHEDULER] Processing {len(new_emails)} new emails:")
            for idx, email in enumerate(new_emails, 1):
                arrival_time = datetime.now().strftime("%H:%M:%S")
                subject_clean = email.subject.replace('\r', '').replace('\n', '')[:80]
                print(f"[SCHEDULER] {idx}. [{arrival_time}] {subject_clean}...")
                publish_email(email)
                processed_ids.add(email.message_id)
        
        # RESTORED: Scheduler checks for aged incidents (The Stable Way)
        check_aged_incidents()
        
        time_left = (end_time - datetime.now()).total_seconds()
        if time_left > 30:
            time.sleep(30)
        else:
            break

    update_last_processed_timestamp(end_time)
    print(f"[SCHEDULER] --- Cycle {cycle_num} Complete ---\n")