from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Order(Base): 
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)# количество товара, по дефолту 1 
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False) #итоговая цена(будет высчитываться, число с плавающей точкой типа: 99.99)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )  # возможные статусы: pending, paid, failed, delivered etc
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(), nullable=False
    ) #время создания, берем автоматически
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(), onupdate=datetime.now(), nullable=False
    ) #время обновления 
    
    
    __table_args__ = (Index(
        "id_customer_status_created", "customer_id", "status", "created_at" #кастомный индекс для быстрой выборке по id заказчика > status > время создания
        ), )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, customer_id={self.customer_id}, status={self.status})>"