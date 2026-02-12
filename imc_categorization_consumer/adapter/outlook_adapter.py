"""
IMC Outlook Adapter - Fetches IMC emails with date filtering
"""
import win32com.client
from datetime import datetime, timedelta
from imc_categorization_consumer.models.model import OutlookEmail
from bs4 import BeautifulSoup
from common.config.settings import MAILBOX_NAME, IMC_SENDER


def fetch_imc_emails(limit=30, start_date=None, end_date=None, only_unread=False):
    """
    Fetch IMC emails from Monitoring.AI mailbox

    Args:
        limit: Max emails to fetch
        start_date: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM"
        end_date: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM" or None
        only_unread: If True, only fetch unread emails
    """
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")

    mailbox = namespace.Folders[MAILBOX_NAME]
    inbox = mailbox.Folders["Inbox"]

    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)

    # Parse dates - try HH:MM first, fallback to date-only
    if start_date and isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")  # Try seconds first
        except ValueError:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")  # Then minutes
            except ValueError:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")  # Then date only

        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")  # Try seconds first
        except ValueError:
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M")  # Then minutes
            except ValueError:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")  # Then date only
                end_date = end_date + timedelta(days=1)

    emails = []
    skipped = 0
    allowed_senders = [s.strip().lower() for s in IMC_SENDER.split(',')]

    for msg in messages:
        # Skip non-email items (meeting invites, receipts, etc.)
        try:
            sender = (msg.SenderEmailAddress or "").lower()
        except Exception:
            skipped += 1
            continue

        # Filter by sender
        if not any(s in sender for s in allowed_senders):
            continue

        # Filter by date range
        try:
            if start_date or end_date:
                msg_date = msg.ReceivedTime
                if hasattr(msg_date, 'replace'):
                    msg_date = msg_date.replace(tzinfo=None)
                if start_date and msg_date < start_date:
                    continue
                if end_date and msg_date >= end_date:
                    continue
        except Exception:
            continue

        # Filter by read status
        if only_unread and msg.UnRead != True:
            continue

        try:
            subject = msg.Subject or ""

            if msg.HTMLBody:
                soup = BeautifulSoup(msg.HTMLBody, "html.parser")
                body = soup.get_text(separator="\n")
            else:
                body = msg.Body or ""

            emails.append(
                OutlookEmail(
                    subject=subject,
                    body=body,
                    message_id=msg.EntryID
                )
            )

            if len(emails) >= limit:
                break

        except Exception:
            continue

    if skipped > 0:
        print(f"[SCHEDULER] Skipped {skipped} non-email items (meeting invites, receipts, etc.)")

    return emails