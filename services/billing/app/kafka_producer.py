import logging
import json
from aiokafka import AIOKafkaProducer
from app.config import settings

logger = logging.getLogger(__name__)

class KafkaProducerClient: 
    def __init__(self) -> None: 
        self.producer = None # здесь храним обьект AIOKafkaProducer
        
    async def start(self): 
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8") # сериализация данных в json, затем в bytes
        )
        await self.producer.start() #стартуем 
        logger.info("Billing Kafka Producer started")
    
    async def stop(self): 
        if self.producer: 
            await self.producer.stop() 
            logger.info("Billing Kafka Producer stopped")
    
    async def send_message(self, topic: str, message: dict): 
        if not self.producer: 
            raise RuntimeError("Kafka Producer is not started")
        try: 
            await self.producer.send_and_wait(topic, message)
            logger.info(f"Billing sent message to {topic}: {message}")
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            raise
        
        
kafka_producer = KafkaProducerClient() #синглтон - один обьект на всю программу
