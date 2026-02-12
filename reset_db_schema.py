import sys
sys.path.insert(0, '.')
from common.database.postgres import get_postgres_connection, init_imc_database

def reset():
    print("⚠️  Wiping Database (Applying Short IDs & Clean Schema)...")
    conn = get_postgres_connection()
    cur = conn.cursor()
    try:
        cur.execute("DROP TABLE IF EXISTS imc_emails CASCADE")
        cur.execute("DROP TABLE IF EXISTS incidents CASCADE")
        cur.execute("DROP TABLE IF EXISTS scheduler_state CASCADE")
        conn.commit()
        print("✅ Tables dropped.")
    except Exception as e:
        print(f"Error dropping tables: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    init_imc_database()
    print("✅ Database Re-initialized successfully.")

if __name__ == "__main__":
    reset()