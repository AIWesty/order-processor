from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Order
from app.schemas.order import OrderCreate
from libs.contracts.events import OrderCreatedEvent
from app.kafka_producer import kafka_client


class OrderRepository:
    """ 
    Слой бизнесс логики, изолированная работа с бд
    service и репозиторий обьединены вместе для простоты
    """
    
    @staticmethod
    async def create_order(db: AsyncSession, data: OrderCreate) -> Order: # принимаем сессию и отвалидированные данные
        order = Order(
            customer_id=data.customer_id,
            product_name=data.product_name,
            quantity=data.quantity,
            total_price=data.total_price, #считаем на фронте 
            status='pending' # статус обработка
        )
        db.add(order)# помечаем обьект на вставку после коммита
        await db.commit() # отправляем обьект в базу,сохраняем, потом получим id 
        await db.refresh(order) #подтягиваем обновления с базы, обьект получает id и мы можем его использовать
        
        #собираем эвент по модели
        event = OrderCreatedEvent(
            order_id=order.id,
            customer_id=order.customer_id, # все данные берем с ордера
            total_price=order.total_price,
            status=order.status
        )
        # топик автоматически создается по новому имени
        await kafka_client.send_message("orders.created", event.model_dump()) # передаем сообщение в топик кафке, превращаем в словарь
        
        return order #возвращаем python обьект 
    
    
    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: int) -> Order | None: #принимаем айди обьекта заказа, на выходе Обьект заказа
        order = select(Order).where(Order.id == order_id)#формируем запрос при помощи select
        result = await db.execute(order)#выполнение запроса
        return result.scalar_one_or_none()#возвращаем один результат или ничего
    
    @staticmethod 
    async def get_orders(db: AsyncSession, skip: int = 0, limit: int = 30) -> tuple[list[Order], int]: 
        """Получаем список, количество заказов с пагинацией"""
        orders_list = select(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit)# делаем выборку, с сортировкой по созданию(новые сверху), пагинацией
        result_tuple = await db.execute(orders_list)# выполняем запрос, получаем обьект(кортеж строк)
        # [
        #   (Order(id=1, customer_id=10, ...),),  # строка 1
        #   (Order(id=2, customer_id=20, ...),),  # строка 2 ]
        
        orders = result_tuple.scalars().all()#преобразует и оставляет только обьекты  [Order(id=1, customer_id=10, ...), ...] 
        
        count_orders = select(func.count()).select_from(Order)#считаем количество обьектов из таблицы Order
        total = await db.scalar(count_orders)# одно значение (из первого столбца первой строки)
        
        return list(orders), total or 0
    
    
    @staticmethod
    async def get_orders_by_customers_and_status(db: AsyncSession, customer_id: int, status: str) -> list[Order]:
        """Делаем выборку заказов по customer_id и status"""
        query = select(Order).where(Order.customer_id == customer_id, Order.status == status).order_by(Order.created_at.desc())#формируем запрос 
        result = await db.execute(query)#выполняем и получаем список кортежекй
        return list(result.scalars().all())#получаем при помощи scalars all() обьекты и оборачиваем в список
    
    
    @staticmethod 
    async def update_order_status(db: AsyncSession, order_id: int,  new_status: str): 
        """Обновление статуса заказа"""
        order = ( 
            update(Order) #обновить у order
            .where(Order.id == order_id)# по пришедшему айди
            .values(status=new_status)
        )
        await db.execute(order)#выполняем запрос
        await db.commit()#сохраняем транзакцию
