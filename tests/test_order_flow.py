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