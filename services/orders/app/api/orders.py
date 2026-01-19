from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderResponse, OrderList
from app.services.order_service import OrderRepository


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