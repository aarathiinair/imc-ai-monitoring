import hashlib
from common.database.postgres import get_postgres_connection, get_postgres_cursor

def _shorten_id(long_id):
    """Generates a consistent 10-character hash from the long Outlook ID"""
    if not long_id: return "unknown"
    return hashlib.sha256(long_id.encode()).hexdigest()[:10]

def log_email_to_audit(message_id, incident_key, alert_type, severity, trap_time, subject, action_taken):
    """
    Logs email to DB.
    IMPORTANT: Converts long Outlook ID -> Short Hash ID here.
    """
    short_id = _shorten_id(message_id)
    
    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO imc_emails
        (message_id, incident_key, type, severity, trap_time, subject, action_taken)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (message_id) DO NOTHING
    ''', (short_id, incident_key, alert_type, severity, trap_time, subject, action_taken))

    conn.commit()
    cursor.close()
    conn.close()

def get_active_incident(incident_key):
    conn = get_postgres_connection()
    cursor = get_postgres_cursor(conn, dict_cursor=True)

    cursor.execute('SELECT * FROM incidents WHERE incident_key = %s', (incident_key,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row: return None
    
    derived_host = row['incident_key'].rsplit('_', 1)[0]

    return {
        'incident_key': row['incident_key'],
        'host': derived_host,
        'type': row['type'],
        'severity': row['severity'],
        'first_seen': str(row['first_seen']),
        'last_seen': str(row['last_seen']),
        'jira_id': row['jira_id'],
        'is_active': row['is_active'],
        'flip_count': row.get('flip_count', 0),
        'last_flip_time': str(row['last_seen'])
    }

def save_state_single(incident_key, alert_type, timestamp, severity=None):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO incidents
        (incident_key, type, severity, first_seen, last_seen, is_active, flip_count)
        VALUES (%s, %s, %s, %s, %s, 1, 0)
        ON CONFLICT (incident_key) DO UPDATE SET
            first_seen = EXCLUDED.first_seen,
            last_seen = EXCLUDED.last_seen,
            severity = EXCLUDED.severity,
            is_active = 1
    ''', (incident_key, alert_type, severity, timestamp, timestamp))
    conn.commit()
    cursor.close()
    conn.close()

def update_incident(incident_key, current_timestamp, jira_id=None, severity=None, increment_flip=False):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    flip_sql = "flip_count = flip_count + 1," if increment_flip else ""
    
    cursor.execute(f'''
        UPDATE incidents
        SET last_seen = %s,
            jira_id = COALESCE(%s, jira_id),
            severity = COALESCE(%s, severity),
            is_active = 1,
            {flip_sql}
            type = type
        WHERE incident_key = %s
    ''', (current_timestamp, jira_id, severity, incident_key))
    conn.commit()
    cursor.close()
    conn.close()

def mark_recovered(incident_key, timestamp, severity):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT flip_count FROM incidents WHERE incident_key = %s', (incident_key,))
    res = cursor.fetchone()
    is_active = 1 if (res and res[0] > 0) else 0

    cursor.execute('''
        UPDATE incidents
        SET severity = %s, last_seen = %s, is_active = %s
        WHERE incident_key = %s
    ''', (severity, timestamp, is_active, incident_key))
    conn.commit()
    cursor.close()
    conn.close()