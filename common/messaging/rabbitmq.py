import pika
from common.config.settings import RABBITMQ_HOST, QUEUE_IMC_CATEGORIZATION

def get_rabbitmq_connection():
    """
    Establishes a blocking connection to RabbitMQ.
    """
    return pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )

def get_imc_channel():
    """
    Used by PRODUCER to send messages.
    Returns (connection, channel).
    """
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    # Ensure queue exists before publishing
    channel.queue_declare(queue=QUEUE_IMC_CATEGORIZATION, durable=True)
    return connection, channel

def get_imc_consumer():
    """
    Used by CONSUMER to listen for messages.
    Returns just the channel object.
    """
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    
    # Ensure queue exists and is durable
    channel.queue_declare(queue=QUEUE_IMC_CATEGORIZATION, durable=True)
    
    # Fair dispatch: Don't give a worker more than 1 message at a time
    channel.basic_qos(prefetch_count=1)
    
    return channel