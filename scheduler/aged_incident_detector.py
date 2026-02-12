import logging
from datetime import datetime
from common.database.postgres import get_postgres_connection, get_postgres_cursor

def check_aged_incidents():
    """
    Checks for incidents past threshold.
    Now executed by the Consumer Process upon Heartbeat.
    """
    conn = get_postgres_connection()
    cursor = get_postgres_cursor(conn, dict_cursor=True)

    cursor.execute('''
        SELECT incident_key, type, severity, first_seen
        FROM incidents
        WHERE is_active = 1
          AND type = 'REACHABILITY'
          AND severity = 'Critical'
          AND (jira_id IS NULL OR jira_id = '')
    ''')
    
    candidates = cursor.fetchall()
    
    for row in candidates:
        incident_key = row['incident_key']
        first_seen = row['first_seen']
        
        if isinstance(first_seen, str): first_dt = datetime.fromisoformat(first_seen)
        else: first_dt = first_seen
            
        elapsed_mins = (datetime.now() - first_dt).total_seconds() / 60
        
        if elapsed_mins >= 5.0:
            cursor.execute('''
                UPDATE incidents
                SET jira_id = 'P1_TICKET_QUEUED'
                WHERE incident_key = %s
            ''', (incident_key,))
            
            # THE "SAY ACTION" LOG YOU REQUESTED
            # Since this runs in the Consumer process, it prints to the Consumer terminal
            print(f"[CONSUMER]   AGED CHECK : P1 Ticket Queued for {incident_key} (Elapsed {elapsed_mins:.1f}m > 5m)")

    conn.commit()
    cursor.close()
    conn.close()