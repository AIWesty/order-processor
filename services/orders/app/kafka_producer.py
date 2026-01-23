import json 
import logging
from aiokafka import AIOKafkaProducer
from app.config import Settings


logger = logging.getLogger(__name__)

class KafkaProducerClient: 
    """
    Синглтон для управления соединением с кафкой на стороне producer'a, так просто проще чем такщить DI
    Будет создаваться экземпляр один раз за все выполнение программы
    """
    def __init__(self) -> None:
        self.producer = None #задаем producer как None для переопределения
        
    async def start(self, settings: Settings): 
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers, #прокидываем брокера, для подключения и получения данных о остальных брокерах
            value_serializer=lambda v: json.dumps(v).encode("utf-8")#переводим данные в bytes понятные для kafka
        )
        await self.producer.start() #запускаем producer
        logger.info("Kafka Producer started")    
        
    async def stop(self): 
        if self.producer: #проверяем есть ли инстанс, чтобы закрыть его 
            await self.producer.stop()
            
    async def send_message(self, topic: str, message: dict): #принимаем куда и что(в каком виде пишем)
        if not self.producer: #есть ли инстанс кафки
            raise RuntimeError("Kafka Producer is not started")
        
        try:
            await self.producer.send_and_wait(topic, message)#пытаемся отправить сообщение в топик с подтверждением того что оно пришло
            logger.info(f"message - {message} sends to topic - {topic}")
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: ", e)
            # вреальном проде тут нужен ретрай или outbox pattern
            raise # прокидываем выше
        
        
kafka_client = KafkaProducerClient()