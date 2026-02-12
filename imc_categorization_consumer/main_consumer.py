import sys
import json
import logging
from common.messaging.rabbitmq import get_imc_consumer
from imc_categorization_consumer.consumer.categorization_consumer import process_message
from imc_categorization_consumer.models.model import OutlookEmail
from common.config.settings import QUEUE_IMC_CATEGORIZATION

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logging.getLogger("pika").setLevel(logging.WARNING)

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        
        # Standard processing
        email = OutlookEmail(
            subject=data.get('subject', 'No Subject'),
            body=data.get('body', ''),
            message_id=data.get('message_id', 'unknown')
        )
        process_message(email)
            
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logging.error(f"[CONSUMER] Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_consumer():
    channel = get_imc_consumer()
    # Explicitly use the restored queue name
    channel.queue_declare(queue=QUEUE_IMC_CATEGORIZATION, durable=True)
    
    channel.basic_consume(queue=QUEUE_IMC_CATEGORIZATION, on_message_callback=callback)
    logging.info(f"IMC Categorization Consumer STARTED | Queue: {QUEUE_IMC_CATEGORIZATION}")
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()