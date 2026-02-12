"""
Single Run Test - Process emails once without loop
Use this for quick testing
"""
import sys
sys.path.insert(0, '.')

import logging
from scheduler.imc_scheduler import run_imc_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

if __name__ == "__main__":
   
    
    input("\nPress Enter to start...")
    
    try:
        # Run scheduler once
        run_imc_scheduler()
        
       
        
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        import traceback
        traceback.print_exc()