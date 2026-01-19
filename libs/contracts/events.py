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