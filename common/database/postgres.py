"""
PostgreSQL Database Connection Helper for IMC
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from common.config.settings import (
    POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER,
    POSTGRES_PASSWORD, POSTGRES_PORT
)


def get_postgres_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST, database=POSTGRES_DB,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT
    )


def get_postgres_cursor(connection, dict_cursor=True):
    if dict_cursor:
        return connection.cursor(cursor_factory=RealDictCursor)
    return connection.cursor()


def init_imc_database():
    """
    Initialize Database Tables
    CHANGES: 
    1. imc_emails: id -> message_id (PK), removed host
    2. incidents: removed host
    """
    conn = get_postgres_connection()
    cursor = conn.cursor()

    # TABLE 1: Audit trail - Uses message_id as Primary Key to prevent duplicates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS imc_emails (
            message_id      TEXT PRIMARY KEY,
            incident_key    TEXT NOT NULL,
            type            TEXT,
            severity        TEXT,
            trap_time       TIMESTAMP,
            subject         TEXT,
            action_taken    TEXT,
            created_at      TIMESTAMP DEFAULT NOW()
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_emails_incident_key 
        ON imc_emails(incident_key)
    ''')

    # TABLE 2: Current state - Removed host column (derived from key)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            incident_key  TEXT PRIMARY KEY,
            type          TEXT,
            severity      TEXT,
            first_seen    TIMESTAMP,
            last_seen     TIMESTAMP,
            jira_id       TEXT,
            is_active     INTEGER DEFAULT 1,
            flip_count    INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_incidents_active 
        ON incidents(is_active)
    ''')

    # TABLE 3: Scheduler state
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduler_state (
            id                  SERIAL PRIMARY KEY,
            last_processed_time TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Initialize scheduler_state if empty
    cursor.execute('SELECT COUNT(*) FROM scheduler_state')
    if cursor.fetchone()[0] == 0:
        from datetime import datetime
        cursor.execute('INSERT INTO scheduler_state (last_processed_time) VALUES (%s)', (datetime.now(),))

    conn.commit()
    cursor.close()
    conn.close()
    print("[✓] Database initialized (message_id PK, host column removed)")


if __name__ == "__main__":
    init_imc_database()