from datetime import datetime

def evaluate_business_rules(row, cycle_mins=15):
    """
    Decides the action based on the current incident state (DB row) and business rules.
    row indices:
    2: etype (REACHABILITY, DISK, BACKUP)
    3: severity (Critical, Info)
    4: first_ts (Time the incident was first created/seen)
    6: jira_id (Existing Ticket ID or 'P1_TICKET_QUEUED')
    8: usage (Disk usage percentage)
    9: flip_count (Number of state changes)
    10: last_flip_time (Time of last state change)
    """
    etype = str(row[2]).upper()
    severity = str(row[3]).title()
    first_ts = row[4]
    jira_id = row[6]
    usage = row[8]
    flip_count = row[9] if len(row) > 9 else 0
    last_flip_time = row[10] if len(row) > 10 else None
    
    current_time = datetime.now()

    # ------------------------------------------------------------------
    # RULE 1: FLAPPING CHECK (Unstable Device)
    # ------------------------------------------------------------------
    # If device has flipped state recently, escalate immediately.
    if flip_count > 0 and last_flip_time:
        try:
            flip_dt = datetime.fromisoformat(str(last_flip_time).strip())
            # Check if the flip happened within the 'cycle_mins' window
            if (current_time - flip_dt).total_seconds() / 60 <= cycle_mins:
                # If ticket exists, just wait (don't create duplicate). 
                # Otherwise, CREATE_P1 immediately.
                return "WAIT" if jira_id else "CREATE_P1"
        except: pass

    # ------------------------------------------------------------------
    # RULE 2: REACHABILITY (Device Down/Up)
    # ------------------------------------------------------------------
    if etype == "REACHABILITY":
        if severity == "Critical":
            if jira_id: return "WAIT" # Ticket Exists - Duplicate suppression
            
            # Check for Delayed Email (Instant P1)
            # If email is old (> 5 mins), create ticket immediately
            try:
                trap_dt = datetime.fromisoformat(str(first_ts).strip()) if first_ts else current_time
                if (current_time - trap_dt).total_seconds() / 60 >= 5.0:
                    return "CREATE_P1"
            except: pass
            
            # Standard Case: Wait 5 mins for self-healing
            return "WAIT"

        # Severity == Info (Recovery)
        # --- ZOMBIE PROTECTION FIX ---
        # If a ticket exists, DO NOT auto-resolve. Keep it open for human check.
        if jira_id: 
            return "WAIT" 
        
        # If no ticket exists, it's a transient blip that healed. Close it.
        return "RESOLVE"

    # ------------------------------------------------------------------
    # RULE 3: DISK USAGE
    # ------------------------------------------------------------------
    elif etype == "DISK":
        if severity == "Critical" and usage >= 90.0:
            return "WAIT" if jira_id else "CREATE_P2"
        return "RESOLVE"

    # ------------------------------------------------------------------
    # RULE 4: BACKUP STATUS
    # ------------------------------------------------------------------
    elif etype == "BACKUP":
        if severity == "Critical": # Failure
             return "WAIT" if jira_id else "CREATE_P2"
        return "RESOLVE" # Success

    # ------------------------------------------------------------------
    # RULE 5: UNKNOWN
    # ------------------------------------------------------------------
    elif etype == "UNKNOWN":
        return "IGNORE"

    return "IGNORE"