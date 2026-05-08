# FastAPI E-Commerce Backend

This repository implements a complete FastAPI e-commerce backend with:

- User registration, login, logout, and JWT authentication
- Refresh token support
- Seller onboarding and product management
- Public product listing and search
- Shopping cart operations: add, update, remove, clear
- Order placement and order history
- Product reviews and ratings
- Wishlist / favorites support

## Run locally

1. Activate your Python environment
2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Start the server

```bash
uvicorn app.main:api --reload
```

## Main endpoints

- `POST /register/`
- `POST /login/`
- `POST /refresh-token/`
- `POST /logout/`
- `GET /me/`
- `PUT /me/`
- `POST /become-seller/`
- `GET /products/`
- `GET /products/search/?query=...`
- `GET /products/{product_id}`
- `POST /seller/products/`
- `PUT /seller/products/{product_id}`
- `DELETE /seller/products/{product_id}`
- `GET /seller/products/`
- `GET /cart/`
- `POST /cart/items/`
- `PATCH /cart/items/{item_id}`
- `DELETE /cart/items/{item_id}`
- `DELETE /cart/clear/`
- `POST /orders/`
- `GET /orders/`
- `GET /orders/{order_id}`
- `POST /products/{product_id}/reviews/`
- `GET /products/{product_id}/reviews/`
- `POST /favorites/`
- `GET /favorites/`
- `DELETE /favorites/{product_id}`

## Notes

- This backend uses SQLAlchemy and PostgreSQL by default.
- Update `db/database.py` with your database connection string.
- If schema changes, drop the existing tables and restart the server.
