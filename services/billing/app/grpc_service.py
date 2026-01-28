import asyncio
import logging
import signal

import grpc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from app.db.models import Payment
from app.config import Settings
from libs.grpc import payment_pb2, payment_pb2_grpc
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

class PaymentServiceServicer(payment_pb2_grpc.PaymentServiceServicer):
    
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self.session_maker = session_maker


    """Реализация сервиса payment для grpc, будем переопределять методы(описывать их)"""    
    async def GetPaymentStatus(self, request, context):
        """
        gRPC-метод: по order_id возвращает статус платежа, наследуемся от сгенерированного класса, переопределяем логику
        """
        order_id = request.order_id
        logger.info(f"gRPC GetPaymentStatus called for order_id={order_id}")
        try:
            #через сессию пытаемся получить данные
            async with self.session_maker() as session:
                    status, payment_id, amount, method = await self._get_payment_data(session, order_id)
        except SQLAlchemyError as e:
            logger.error(f"Database error for order_id={order_id}: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal Database Error. Please try again later.")#выброс исключения если проблемы с базой
        except Exception as e:#любые другие ошибки
            logger.exception(f"Unexpected error for order_id={order_id}: {e}")
            await context.abort(grpc.StatusCode.UNKNOWN, "Unknown server error")
        
        #обьект ответа 
        return payment_pb2.GetPaymentStatusResponse(#type: ignore
            order_id=order_id,
            status=status,
            payment_id=payment_id or 0,
            amount=float(amount or 0.0),
            payment_method=method or "",
        )
    
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
    

async def start_server_grpc(settings: Settings, engine: AsyncEngine): 
    """
    Поднимает grpc сервер на порту из конфига
    """
    
    print(f"DEBUG: start_server_grpc called with port {settings.billing_grpc_port}")


    # Создаем фабрику сессий
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    
    server = grpc.aio.server()#создаем асинхронный grpc сервер
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentServiceServicer(session_maker=session_maker), server)#регистрируем реализацию(связываем с rpc вызовами), с переопределнными методами
    
    #открываем порт
    listen_addr = f"[::]:{settings.billing_grpc_port}"
    server.add_insecure_port(listen_addr)
    logger.info(f"Starting gRPC server on {listen_addr}")
    
    await server.start()#запускаем сервер
    return server