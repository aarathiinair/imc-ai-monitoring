
# test_backup_email_fetch.py
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from imc_categorization_consumer.adapter.outlook_adapter import fetch_imc_emails

print("Testing Backup Email Fetch")
print("="*80)

# Test 1: Fetch emails from 00:30 to 00:35 (should catch the 00:33 backup)
print("\nTest 1: Fetching emails between 00:30 and 00:35")
print("-"*80)

emails = fetch_imc_emails(
    limit=50,
    start_date="2026-02-11 00:30:00",
    end_date="2026-02-11 00:35:00"
)

print(f"Found {len(emails)} emails")
for idx, email in enumerate(emails, 1):
    subject = email.subject.replace('\r', '').replace('\n', '')[:80]
    print(f"{idx}. {subject}")
    if "backup" in subject.lower():
        print(f"   ✓ BACKUP EMAIL FOUND!")
        print(f"   Body preview: {email.body[:200]}")

# Test 2: Fetch with buffer (end_date = now + 1 minute)
print("\n\nTest 2: Fetching with 1-minute buffer")
print("-"*80)

now = datetime.now()
emails_with_buffer = fetch_imc_emails(
    limit=50,
    start_date="2026-02-11 00:30:00",
    end_date=(now + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
)

print(f"Found {len(emails_with_buffer)} emails")
for idx, email in enumerate(emails_with_buffer, 1):
    subject = email.subject.replace('\r', '').replace('\n', '')[:80]
    print(f"{idx}. {subject}")

# Test 3: Fetch without end_date (should get everything after 00:30)
print("\n\nTest 3: Fetching without end_date restriction")
print("-"*80)

emails_no_end = fetch_imc_emails(
    limit=50,
    start_date="2026-02-11 00:30:00",
    end_date=None
)

print(f"Found {len(emails_no_end)} emails")
for idx, email in enumerate(emails_no_end, 1):
    subject = email.subject.replace('\r', '').replace('\n', '')[:80]
    print(f"{idx}. {subject}")

print("\n" + "="*80)
print("Test Complete")