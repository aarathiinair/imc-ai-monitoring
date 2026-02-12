import re
from datetime import datetime
from email.utils import parsedate_to_datetime


def extract_email_data(msg):
    """Parses email content into structured data for the Engine."""
    subj = msg['subject'] or ""
    body = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_content()
                    break
        else:
            body = msg.get_content()
    except:
        body = ""

    combined_content = (subj + " " + body)
    full_lower = combined_content.lower()

    # 1. Classification
    etype = "UNKNOWN"
    if "disk" in full_lower:
        etype = "DISK"
    elif any(k in full_lower for k in ["reachability", "ping", "unreachable", "respond"]):
        etype = "REACHABILITY"
    elif "backup" in full_lower:
        etype = "BACKUP"

    # 2. Host extraction
    host = "UNKNOWN"
    h_match = re.search(r'(?:alarm|notice):\s+([A-Z0-9]+)\(', subj, re.IGNORECASE)
    if h_match:
        host = h_match.group(1).upper()
    else:
        backup_match = re.search(r'BITZER[_-]([A-Z0-9]+)[_-]?Backup', subj, re.IGNORECASE)
        if backup_match:
            host = f"BITZER_{backup_match.group(1).upper()}"

    # 3. Disk Usage
    usage = 0.0
    if etype == "DISK":
        u_match = re.search(r'is\s+["\']?([\d.]+)\s*%["\']?', combined_content, re.IGNORECASE)
        if u_match:
            usage = float(u_match.group(1))
        else:
            all_pcts = re.findall(r'([\d.]+)\s*%', combined_content)
            for p in all_pcts:
                val = float(p)
                if val != 90.00:
                    usage = val
                    break

    # 4. Severity
    severity = "Info"
    if "[critical]" in full_lower:
        severity = "Critical"
    elif "[info]" in full_lower:
        severity = "Info"

    if etype == "BACKUP":
        # 1. PRIORITY CHECK: Partial Success is actually a FAILURE (Critical)
        if "part succeeded" in full_lower:
            severity = "Critical"  # This triggers CREATE_P2
            
        # 2. Only if it's NOT partial, check for full success
        elif "succeeded" in full_lower or "success" in full_lower:
            severity = "Info"      # This triggers RESOLVE/IGNORE
            
        # 3. Check for explicit failures
        elif "fail" in full_lower:
            severity = "Critical"  # This triggers CREATE_P2
            
        else:
            severity = "Info" # Default safe fallback

    # 5. Timestamp extraction from body
    timestamp = None

    trap_match = re.search(
        r'Trap Time:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
        body, re.IGNORECASE
    )
    if trap_match:
        try:
            timestamp = datetime.strptime(trap_match.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    if timestamp is None and etype == "BACKUP":
        fin_match = re.search(
            r'Finished time:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            body, re.IGNORECASE
        )
        if fin_match:
            try:
                timestamp = datetime.strptime(fin_match.group(1), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

    if timestamp is None:
        try:
            timestamp = parsedate_to_datetime(msg['date']).replace(tzinfo=None)
        except:
            timestamp = datetime.now()

    return {
        "incident_key": f"{host}_{etype}",
        "host": host,
        "type": etype,
        "severity": severity,
        "timestamp": timestamp,
        "usage": usage,
        "raw": combined_content
    }