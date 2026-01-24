import asyncio
import logging

import grpc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.dependency import get_db
from app.db.models import Payment
from app.config import Settings

from app.grpc import payment_pb2, payment_pb2_grpc

logger = logging.getLogger(__name__)

class PaymentServiceServicer(payment_pb2_grpc.PaymentServiceServicer):
    """Реализация сервиса payment для grpc, будем переопределять методы(описывать их)"""
    
    
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        # Мы принимаем фабрику сессий при создании сервиса, используем как di
        self.session_maker = session_maker
    
    
    async def GetPaymentStatus(self, request, context):
        """
        gRPC-метод: по order_id возвращает статус платежа
        """
        order_id = request.order_id
        logger.info(f"gRPC GetPaymentStatus called for order_id={order_id}")
        
        #через сессию пытаемся получить данные
        async with self.session_maker() as session:
            status, payment_id, amount, method = await self._get_payment_data(session, order_id)
        
        #обьект ответа 
        # response = payment_pb2.GetPaymentStatusResponse(
        #     order_id=order_id,
        #     status=status,
        #     payment_id=payment_id or 0,
        #     amount=float(amount or 0.0),
        #     payment_method=method or "",
        # )
        # return response
    
    @staticmethod
    async def _get_payment_data(session: AsyncSession, order_id: int):
        """Получаем данные по id при помощи выборки"""
        statement = (
            select(Payment) #таблица для выборки
            .where(Payment.order_id == order_id)#по id
            .order_by(Payment.created_at.desc())#сортировка по убыванию даты создания
            .limit(1)#всего один, самый новый заказ
        ) 
        result = await session.execute(statement) #выполняем запрос
        payment: Payment | None = result.scalar_one_or_none() #тот самый один обьект

        if not payment: #если с выборки ничего не пришло
            return "not_found", None, None, None
        
        return payment.status, payment.id, payment.amount, payment.payment_method
    

async def serve_grpc(): 
    """
    Поднимает grpc сервер на порту из конфига
    """
    server = grpc.aio.server()
    # payment_pb2_grpc.PaymentServiceServicer.add_to_server(PaymentServiceServicer(), server)