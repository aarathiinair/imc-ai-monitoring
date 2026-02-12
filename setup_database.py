"""
Database Setup Script - 3-Table Architecture with Scheduler Tracking
Run this ONCE to initialize PostgreSQL database
"""
import sys
sys.path.insert(0, '.')

from common.database.postgres import init_imc_database

if __name__ == "__main__":
   
    
    try:
        init_imc_database()
        
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        print("\nMake sure PostgreSQL is running and credentials are correct.")
        print("Check common/config/settings.py")