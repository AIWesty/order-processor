import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from app.config import Settings
from app.services.order_service import OrderRepository
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from libs.contracts.events import PaymentSucceededEvent, PaymentFailedEvent


logger = logging.getLogger(__name__)

async def consume_payment_events(settings: Settings, session_maker: async_sessionmaker[AsyncSession]):
    consumer = AIOKafkaConsumer( #создание обьекта consumer
        "payments.succeeded",
        "payments.failed",
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="orders_group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="earliest"
    )
    
    await consumer.start()# запуск
    logger.info("Orders Kafka Consumer started (listening for payment events)")
    
    try: 
        async for message in consumer: #тк это асинх итератор идем по нему чтобы получать новые данные
            try: 
                data = message.value#из пришедших данных берем нужные
                if isinstance(data, dict):
                    event_name = data.get("event_name")#получаем имя события
                
                async with session_maker() as db: 
                    if event_name == "PaymentSucceeded": #если это из успешных платежей
                        event = PaymentSucceededEvent.model_validate(data)
                        logger.info(f"Payment succeeded for order {event.order_id}")
                        await OrderRepository.update_order_status(db, event.order_id, "paid") #обновляем данные в бд заказа
                    elif event_name == "PaymentFailed":  #иначе обновляем в бд данные на фейл
                        event = PaymentFailedEvent.model_validate(data)
                        logger.warning(f"Payment failed for order {event.order_id}: {event.reason}")
                        await OrderRepository.update_order_status(db, event.order_id, "failed")
                
            except Exception as e:
                logger.error(f"Error processing payment event: {e}", exc_info=True)
    finally:
        await consumer.stop() #остановка consumer в конце работы приложения