from datetime import datetime
from imc_categorization_consumer.src.parser import extract_email_data
from imc_categorization_consumer.src.engine import evaluate_business_rules
from imc_categorization_consumer.src.state_manager import (
    get_active_incident, save_state_single, update_incident,
    mark_recovered, log_email_to_audit
)
from common.config.settings import SCHEDULER_CYCLE_MINUTES

class EmailAdapter:
    def __init__(self, outlook_email):
        self.outlook_email = outlook_email
        self._subject = outlook_email.subject
        self._body = outlook_email.body
        self.message_id = outlook_email.message_id 
    def get_content(self): return self._body
    def is_multipart(self): return False
    def __getitem__(self, key): return self._subject if key == 'subject' else None

def process_message(email):
    adapted_email = EmailAdapter(email)
    extracted = extract_email_data(adapted_email)
    incident_key = extracted['incident_key']
    alert_type = extracted['type']
    severity = extracted['severity']
    trap_time_str = extracted['timestamp'].isoformat()

    # --- VISUAL SEPARATOR ADDED HERE ---
    print(f"[CONSUMER] ──────────────────────────────────────────────────")
    print(f"[CONSUMER] EMAIL: \"{email.subject[:90]}\"")

    incident_state = get_active_incident(incident_key)
    
    # Flip Detection
    is_flip = False
    if incident_state and incident_state.get('severity') == 'Info' and severity == 'Critical':
        is_flip = True
        print(f"[CONSUMER]   FLIP   : Detected! Info -> Critical")

    # Build row
    if incident_state:
        row = [incident_key, None, alert_type, severity, incident_state['first_seen'], trap_time_str, incident_state.get('jira_id'), 1, extracted.get('usage'), incident_state.get('flip_count', 0), incident_state.get('last_flip_time')]
    else:
        row = [incident_key, None, alert_type, severity, trap_time_str, trap_time_str, None, 1, extracted.get('usage'), 0, None]

    action = evaluate_business_rules(row, cycle_mins=SCHEDULER_CYCLE_MINUTES)

    if action in ["RESOLVE", "IGNORE"]:
        if incident_state: mark_recovered(incident_key, trap_time_str, severity)
        print(f"[CONSUMER]   ENGINE : Action={action}")
        
    elif action.startswith("CREATE"):
        priority = action.split("_")[1]
        if not incident_state: save_state_single(incident_key, alert_type, trap_time_str, severity)
        update_incident(incident_key, trap_time_str, jira_id=f"PENDING_{priority}", severity=severity, increment_flip=is_flip)
        print(f"[CONSUMER]   ENGINE : Action={action} | Ticket=PENDING_{priority}")
        
    else: # WAIT
        if not incident_state: 
            save_state_single(incident_key, alert_type, trap_time_str, severity)
            print(f"[CONSUMER]   ENGINE : Action=WAIT | Monitoring...")
        else: 
            update_incident(incident_key, trap_time_str, severity=severity, increment_flip=is_flip)
            
            # Check for Duplicate logic to print specific log
            if incident_state.get('jira_id'):
                print(f"[CONSUMER]   ENGINE : Action=WAIT | Duplicate: Ticket already exists ({incident_state['jira_id']})")
            else:
                print(f"[CONSUMER]   ENGINE : Action=WAIT | Monitoring...")

    log_email_to_audit(email.message_id, incident_key, alert_type, severity, trap_time_str, email.subject, action)
    return {"action": action}