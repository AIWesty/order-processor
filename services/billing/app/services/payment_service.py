import random
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Payment
from libs.contracts.events import OrderCreatedEvent, PaymentSucceededEvent, PaymentFailedEvent
from app.kafka_producer import kafka_producer


logger = logging.getLogger(__name__)


class PaymentService: 
    @staticmethod
    async def process_payment(db: AsyncSession, event: OrderCreatedEvent) -> Payment:  #принимаем ивент из кафки 
        """
        Обработка платежа для заказа
        Создает запись Payment в бд 
        Эмулирует обработку (успех операции или фейл)
        публикуем результат в kafka
        """
        logger.info(f"Processing payment for order {event.order_id}")
        
        payment = Payment(
            order_id=event.order_id, #берем данные из события с топика
            amount=event.total_price,
            payment_method="card",
            status="pending",
        )
        db.add(payment)#добавляем в базу обьект обработки заказа()
        await db.commit()#сохраняем в базе изменения
        await db.refresh(payment)
        
        #эмуляция обработки платежа, получаем True/false
        success = random.random() > 0.1
        
        if success:  #при удачной обработке
            payment.status = "succeeded"
            await db.commit() #меняем статус обработки 
            
            # собираем обьект по схеме pydantic 
            result_event = PaymentSucceededEvent(
                order_id=event.order_id,
                payment_id=payment.id,
                amount=float(payment.amount),
                payment_method=payment.payment_method,
            )
            await kafka_producer.send_message("payments.succeeded", result_event.model_dump()) #публикуем его в топик 
            logger.info(f"Payment {payment.id} succeeded for order {event.order_id}")
            
        else: # неудачная обработка
            payment.status = "failed" #меняем статус в бд
            await db.commit()
            
            result_event = PaymentFailedEvent(# делаем обьект для передачи в топик
                order_id=event.order_id,
                reason="Insufficient funds (simulated)",
            )
            await kafka_producer.send_message("payments.failed", result_event.model_dump())# передаем обьект фейла операции
            logger.warning(f"Payment failed for order {event.order_id}")
            
        return payment