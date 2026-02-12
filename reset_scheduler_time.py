"""
Reset Scheduler Timestamp - Utility for Testing
Use this to set the scheduler's last processed time to a specific value
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from scheduler.state_manager import reset_scheduler_timestamp, get_last_processed_timestamp


def main():
    print("="*60)
    print("Reset Scheduler Timestamp")
    print("="*60)
    
    # Show current timestamp
    current = get_last_processed_timestamp()
    print(f"\nCurrent last_processed_time: {current}")
    
    print("\nOptions:")
    print("1. Set to NOW")
    print("2. Set to 1 hour ago")
    print("3. Set to custom time (YYYY-MM-DD HH:MM:SS)")
    print("4. Cancel")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        reset_scheduler_timestamp()
        new_time = get_last_processed_timestamp()
        print(f"\n[✓] Timestamp set to NOW: {new_time}")
        
    elif choice == "2":
        one_hour_ago = datetime.now() - timedelta(hours=1)
        reset_scheduler_timestamp(one_hour_ago)
        new_time = get_last_processed_timestamp()
        print(f"\n[✓] Timestamp set to 1 hour ago: {new_time}")
        
    elif choice == "3":
        custom = input("Enter timestamp (YYYY-MM-DD HH:MM:SS): ").strip()
        try:
            reset_scheduler_timestamp(custom)
            new_time = get_last_processed_timestamp()
            print(f"\n[✓] Timestamp set to: {new_time}")
        except Exception as e:
            print(f"\n[✗] Error: {e}")
            
    else:
        print("\n[✓] Cancelled")


if __name__ == "__main__":
    main()