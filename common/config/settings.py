RABBITMQ_HOST = "localhost"
QUEUE_IMC_CATEGORIZATION = "imc.categorization1"

POSTGRES_HOST = "localhost"
POSTGRES_DB = "email_processor_duplicate"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "Admin"  
POSTGRES_PORT = 5432

# ============================================
# SCHEDULER CONFIGURATION
# ============================================
# ============================================
# SCHEDULER CONFIGURATION
# ============================================
POLL_INTERVAL_SECONDS = 900  # Scheduler runs every 15 minutes (15 * 60 seconds)
EMAIL_FETCH_LIMIT = 100

# Flapper detection window (must match poll interval for clean logic)
SCHEDULER_CYCLE_MINUTES = 15  # Just a parameter for engine, not a separate scheduler

# ============================================
# IMC SOURCE CONFIGURATION
# ============================================
SOURCE_NAME_IMC = "imc"
IMC_SENDER = "imc@bitzer.biz,nair,aarathi,7836716C475843019137C9185D88C57B"  # Comma-separated
IMC_ASSIGNMENT_GROUP = "Telecommunications Team"

MAILBOX_NAME = "Monitoring.AI@bitzer.de"