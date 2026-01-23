from pydantic import BaseModel
from typing import Literal

class OrderCreatedEvent(BaseModel):
    """
    Будем использовать pydantic модель для конкракта 
    между producer и consumer, чтобы они ожидали одинаковые данные
    """
    event_name: Literal["OrderCreated"] = "OrderCreated" # ставим жестко определнный тип эвента
    order_id: int
    customer_id: int 
    total_price: float
    status: str
    
    class Config: 
        json_encoders = {
            # Позволяет сериализовать datetime и другие типы правильно
        }
        
        
class PaymentSucceededEvent(BaseModel):
    """
    Модель для контракта получения данных об обработке платежа(заказа)
    """
    
    event_name: Literal["PaymentSucceeded"] = "PaymentSucceeded" #указываем строгий тип
    order_id: int #id обработанного заказа
    payment_id: int #айди операции обработки заказа
    amount: float #сумма заказа
    payment_method: str #способ оплаты заказа
    
    class Config: 
        json_encoders = {
            # Позволяет сериализовать datetime и другие типы правильно
        }

class PaymentFailedEvent(BaseModel): 
    event_name: Literal["PaymentFailed"] = "PaymentFailed" 
    order_id: int 
    reason: str #причина отмены операции 