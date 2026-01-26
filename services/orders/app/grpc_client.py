import logging

import grpc

from app.config import Settings
from libs.grpc import payment_pb2, payment_pb2_grpc

logger = logging.getLogger(__name__)

class BillingGrpcClient: 
    def __init__(self, settings: Settings) -> None:
        self._channel: grpc.aio.Channel | None = None #канал связи между клиентом и сервером
        self._stub: payment_pb2_grpc.PaymentServiceStub | None = None #заглушка с типизированными методами для вызова rpc
        self.settings = settings
        
    async def connect(self): 
        if self._channel is None:
            target = f"{self.settings.billing_grpc_host}:{self.settings.billing_grpc_port}"
            logger.info(f"Connecting to Billing gRPC at {target}")
            
            options = [
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
                ('grpc.keepalive_permit_without_calls', 1),
            ]
            
            self._channel = grpc.aio.insecure_channel(target, options=options) #регистрируем как канал нашу связь клиента и сервера
            self._stub = payment_pb2_grpc.PaymentServiceStub(self._channel)#передаем в стаб канал связи

    async def close(self):
        if self._channel is not None:
            await self._channel.close()#закрытие канала соединения
            logger.info("Billing gRPC channel closed")
            self._channel = None
            self._stub = None
        
    async def get_payment_status(self, order_id: int) -> payment_pb2.GetPaymentStatusResponse: # type:ignore
        if self._stub is None: 
            await self.connect() 
        
        request = payment_pb2.GetPaymentStatusRequest(order_id=order_id)#type:ignore
        response = await self._stub.GetPaymentStatus(request)#type:ignore
        return response

