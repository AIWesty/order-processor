import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from app.config import settings

from libs.contracts.events import OrderCreatedEvent

logger = logging.getLogger(__name__)

async def consume_orders():
    """Фоновая задача для чтения из kafkи"""
    consumer = AIOKafkaConsumer(
        "orders.created", #топик откуда читать
        bootstrap_servers=settings.kafka_bootstrap_servers, #показываем где брокер
        group_id="billing_group", #группа консьюмеров для деления нагрузки между инстансами(у нас нет)
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="earliest" # читать с начала, если нет смещения
    )
    
    await consumer.start() #запускаем consumer
    logger.info("Billing Consumer is started")
    
    try:
        async for message in consumer: #под капотом это асинк итератор, ожидаем новых сообщений
            try: 
                data = message.value #берем словарь из прилетевшего сообщения
                event = OrderCreatedEvent.model_validate(data)#распаковываем словарь при помощи нашего pydantic контракта
                
                logger.info(f"Billing received event: {event}")
                logger.info(f"Processing payment for Order ID: {event.order_id}...")
                
                
                # ТУТ БУДЕТ ЛОГИКА ОПЛАТЫ 
                
                
            except Exception as e: 
                logger.error(f'Error processing message: {e}')
    finally: 
        await consumer.stop()