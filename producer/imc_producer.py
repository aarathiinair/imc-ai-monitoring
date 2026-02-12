import json
import pika
import logging
from common.messaging.rabbitmq import get_imc_channel
from common.config.settings import QUEUE_IMC_CATEGORIZATION, SOURCE_NAME_IMC

def publish_email(email):
    try:
        connection, channel = get_imc_channel()
        message = {
            "source": SOURCE_NAME_IMC,
            "message_id": email.message_id,
            "subject": email.subject,
            "body": email.body
        }
        
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_IMC_CATEGORIZATION,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
    except Exception as e:
        logging.error(f"[PRODUCER] Failed to publish: {e}")