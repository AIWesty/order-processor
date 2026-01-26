from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependency import get_db, get_billing_client
from app.schemas.order import OrderCreate, OrderResponse, OrderList
from app.services.order_service import OrderRepository
from app.grpc_client import BillingGrpcClient


router = APIRouter(prefix='/orders', tags=['orders'])#создаем роутер и ставим prefix для всех путей эндпоинтов

@router.post('/', response_model=OrderResponse, status_code=201)
async def create_order(order_data: OrderCreate, db: AsyncSession =  Depends(get_db)):
    """Создаем новый заказ"""
    order = await OrderRepository.create_order(db, order_data)#используем наш репозиторий и передаем в него данные
    return order #возврат ответа, автовалидация при response_model

@router.get('/{order_id}', response_model=OrderResponse, status_code=200)
async def get_order_by_id(order_id: int, db: AsyncSession = Depends(get_db)):#парсим order_id из пути url
    """Получение заказа по id """
    order = await OrderRepository.get_order_by_id(db, order_id)# выполняем выборку через репозиторий
    if not order: 
        raise HTTPException(status_code=404, detail='order not found')
    return order



@router.get('/', response_model=OrderList, status_code=200)
async def get_list_orders(
    skip: int = Query(0, ge=0), 
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка заказов и количества заказов с пагинацией"""
    orders, total = await OrderRepository.get_orders(db, skip, limit)
    return orders, total


@router.get("/customer/{customer_id}/status/{status}", response_model=list[OrderResponse])#ответом будет список заказов
async def get_orders_by_customers_and_status(customer_id: int, status: str, db: AsyncSession = Depends(get_db)): 
    """Получаеам заказы по customers id и status с сортировкой по дате создания(новые сверху)"""
    orders = await OrderRepository.get_orders_by_customers_and_status(db, customer_id, status)
    return orders

@router.get("/{order_id}/payment-status")
async def get_payment_status(order_id: int, db: AsyncSession = Depends(get_db), billing_client: BillingGrpcClient = Depends(get_billing_client)): 
    """синхронный для клиента http запрос через grpc к Billing, принимаем grpc клиент как зависимость"""
    order = await OrderRepository.get_order_by_id(db, order_id)#выбираем обьект заказа из бд 
    if not order: 
        raise HTTPException(status_code=404, detail="Order not found")
    
    response = await billing_client.get_payment_status(order_id)#отдаем в grpc на обработку
    
    return { #генерируем ответ из пришедших данных
        "order_id": response.order_id,
        "order_status": order.status,
        "payment_status": response.status,
        "payment_id": response.payment_id,
        "amount": response.amount,
        "payment_method": response.payment_method,
    }