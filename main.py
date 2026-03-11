
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# Sample products
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "stock": 10},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "stock": 20},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "stock": 0},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "stock": 5}
]

# Day 1 - GET all products
@app.get("/products")
def get_products():
    return products

# Day 2 - Q1: Filter products
@app.get("/products/filter")
def filter_products(category: str = None, min_price: int = Query(0), max_price: int = None):
    filtered = products
    if category:
        filtered = [p for p in filtered if p["category"].lower() == category.lower()]
    if min_price is not None:
        filtered = [p for p in filtered if p["price"] >= min_price]
    if max_price is not None:
        filtered = [p for p in filtered if p["price"] <= max_price]
    return filtered

# Day 2 - Q2: Product price only
@app.get("/products/{product_id}/price")
def product_price(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}
    return {"error": "Product not found"}

# Day 2 - Q3: Feedback
feedback_list = []

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

@app.post("/feedback")
def submit_feedback(feedback: CustomerFeedback):
    feedback_list.append(feedback.dict())
    return {
        "message": "Feedback submitted successfully",
        "feedback": feedback.dict(),
        "total_feedback": len(feedback_list)
    }

# Day 2 - Q4: Product summary
@app.get("/products/summary")
def products_summary():
    total_products = len(products)
    in_stock_count = sum(1 for p in products if p["stock"] > 0)
    out_of_stock_count = total_products - in_stock_count
    most_expensive = max(products, key=lambda x: x["price"])
    cheapest = min(products, key=lambda x: x["price"])
    categories = list(set(p["category"] for p in products))
    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "most_expensive": {"name": most_expensive["name"], "price": most_expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }

# Day 2 - Q5: Bulk Order
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: list[OrderItem] = Field(..., min_items=1)

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif product["stock"] < item.quantity:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = item.quantity * product["price"]
            confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})
            grand_total += subtotal
    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

# Bonus - Order tracker
orders_list = []

@app.post("/orders")
def create_order(order: BulkOrder):
    order_dict = order.dict()
    order_dict["status"] = "pending"
    order_id = len(orders_list) + 1
    order_dict["id"] = order_id
    orders_list.append(order_dict)
    return order_dict

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    order = next((o for o in orders_list if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    return order

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    order = next((o for o in orders_list if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    order["status"] = "confirmed"
    return order