"""
Scheduler State Manager - Tracks last processed timestamp for sliding window
"""
from datetime import datetime
from common.database.postgres import get_postgres_connection, get_postgres_cursor


def get_last_processed_timestamp():
    """
    Get the last processed timestamp from scheduler_state table
    Returns datetime object
    """
    conn = get_postgres_connection()
    cursor = get_postgres_cursor(conn, dict_cursor=True)

    cursor.execute('''
        SELECT last_processed_time 
        FROM scheduler_state 
        ORDER BY id DESC 
        LIMIT 1
    ''')

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return row['last_processed_time']
    else:
        # If no record exists, return current time
        return datetime.now()


def update_last_processed_timestamp(new_timestamp):
    """
    Update the last processed timestamp in scheduler_state table
    
    Args:
        new_timestamp: datetime object or ISO string
    """
    conn = get_postgres_connection()
    cursor = conn.cursor()

    # Convert string to datetime if needed
    if isinstance(new_timestamp, str):
        new_timestamp = datetime.fromisoformat(new_timestamp)

    # Update the single row (or insert if doesn't exist)
    cursor.execute('''
        UPDATE scheduler_state 
        SET last_processed_time = %s,
            updated_at = NOW()
        WHERE id = (SELECT id FROM scheduler_state ORDER BY id DESC LIMIT 1)
    ''', (new_timestamp,))

    # If no rows updated, insert new row
    if cursor.rowcount == 0:
        cursor.execute('''
            INSERT INTO scheduler_state (last_processed_time)
            VALUES (%s)
        ''', (new_timestamp,))

    conn.commit()
    cursor.close()
    conn.close()


def reset_scheduler_timestamp(timestamp=None):
    """
    Reset scheduler timestamp (useful for testing)
    
    Args:
        timestamp: datetime object or ISO string. If None, uses current time.
    """
    if timestamp is None:
        timestamp = datetime.now()
    elif isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM scheduler_state
    ''')

    cursor.execute('''
        INSERT INTO scheduler_state (last_processed_time)
        VALUES (%s)
    ''', (timestamp,))

    conn.commit()
    cursor.close()
    conn.close()

    print(f"[✓] Scheduler timestamp reset to: {timestamp}")