from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class OderCreate(BaseModel): 
    """Валидация пришедших данных. Схема для создания заказа"""
    customer_id: int = Field(..., gt=0) #обязательное поле, больше 0
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(default=1, gt=0)#по дефолту 1
    total_price: float = Field(..., gt=0)

    
class OrderResponse(BaseModel):
    """Валидируем пришедшие данные. Схема для ответа пользователю
        тк данные с сервера, можем не указывать Field с значениями"""
    id: int
    customer_id: int
    product_name: str
    quantity: int 
    total_price: float
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True) #можно прямо в коде преобразовывать orm обьект в pydantic модель, валидировать на лету
    
    
    

class OrderList(BaseModel):
    """Выборка нескольких заказов с пагинацией"""
    total: int 
    items: list[OrderResponse]
    
    