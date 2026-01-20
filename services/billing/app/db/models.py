from app.db.base import Base
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column


class Payment(Base): 
    __tablename__ = "payments"
    
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)#сумма заказа
    payment_method: Mapped[str] = mapped_column(String(50), default="card")#изначально карта
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending, succeeded, failed
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now()) #автоматически задаем сервером
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(), onupdate=datetime.now()
    )
    
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, order_id={self.order_id}, status={self.status})>"