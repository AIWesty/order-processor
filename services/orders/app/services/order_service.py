from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Order
from app.schemas.order import OrderCreate


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
        await db.flush() # отправляем обьект в базу, но не закрываем транзакцию, чтобы получить id для возврата
        await db.refresh(order) #подтягиваем обновления с базы, обьект получается id и мы можем его использовать
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
    
    