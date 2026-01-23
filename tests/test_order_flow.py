import pytest 
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_order_success(test_client: AsyncClient):
    """Тест создания заказа"""
    payload = {
        "customer_id": 344,
        "product_name": "cool product", 
        "quantity": 3,
        "total_price": 1234.45
    }
    
    response = await test_client.post("/orders/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == 344
    assert data["product_name"] == "cool product"
    assert data["status"] == "pending"
    assert "id" in data
    
    

@pytest.mark.asyncio
async def test_get_order(test_client: AsyncClient):
    """Тест получения заказа по ID"""
    # Сначала создаём
    payload = {
        "customer_id": 888,
        "product_name": "Mouse",
        "quantity": 1,
        "total_price": 29.99
    }
    create_response = await test_client.post("/orders/", json=payload)
    order_id = create_response.json()["id"]
    
    # Получаем
    response = await test_client.get(f"/orders/{order_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert data["customer_id"] == 888


@pytest.mark.asyncio
async def test_list_orders(test_client: AsyncClient):
    """Тест списка заказов с пагинацией"""
    # Создаём несколько заказов
    for i in range(5):
        payload = {
            "customer_id": 777,
            "product_name": f"Product {i}",
            "quantity": 1,
            "total_price": 10.0 * i
        }
        await test_client.post("/orders/", json=payload)
    
    # Запрашиваем список
    response = await test_client.get("/orders/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) >= 5


@pytest.mark.asyncio
async def test_customer_orders_by_status(test_client: AsyncClient):
    """Тест фильтрации по customer_id и статусу (тяжёлый запрос с индексом)"""
    customer_id = 555
    
    # Создаём заказы
    for _ in range(3):
        await test_client.post("/orders/", json={
            "customer_id": customer_id,
            "product_name": "Item",
            "quantity": 1,
            "total_price": 100.0
        })
    
    # Запрашиваем
    response = await test_client.get(f"/orders/customer/{customer_id}/status/pending")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(order["customer_id"] == customer_id for order in data)
    assert all(order["status"] == "pending" for order in data)