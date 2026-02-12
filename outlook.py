import win32com.client
from datetime import datetime
 
MAILBOX_NAME = "Monitoring.AI@bitzer.de"
 
outlook = win32com.client.Dispatch("Outlook.Application")
namespace = outlook.GetNamespace("MAPI")
 
mailbox = namespace.Folders[MAILBOX_NAME]
inbox = mailbox.Folders["Inbox"]
 
messages = inbox.Items
messages.Sort("[ReceivedTime]", True)
 
print("Recent 20 emails with sender info:")
print("="*80)
 
for i, msg in enumerate(list(messages)[:20], 1):
    try:
        sender = msg.SenderEmailAddress or "NO SENDER"
        subject = (msg.Subject or "NO SUBJECT")[:60]
        received = msg.ReceivedTime
        print(f"{i}. SENDER: {sender}")
        print(f"   SUBJECT: {subject}")
        print(f"   DATE: {received}")
        print("-"*80)
    except Exception as e:
        print(f"{i}. ERROR: {e}")
        print("-"*80)