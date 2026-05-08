from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from db.database import session, engine
import models.database_models as database_models
from schemas.models import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    CartItemCreate,
    CartItemResponse,
    CartResponse,
    OrderCreate,
    OrderResponse,
    ReviewCreate,
    ReviewResponse,
    FavoriteCreate,
    FavoriteResponse,
)
from models.database_models import (
    Users,
    Token,
    Products,
    Carts,
    CartItems,
    Orders,
    OrderItems,
    Reviews,
    Favorites,
)
from sqlalchemy.orm import Session
from core.utils import get_hashed_password, verify_password, create_access_token, create_refresh_token
from core.auth_bearer import JWTBearer, decode_jwt
from typing import List, Optional
from datetime import datetime

api = FastAPI(title="FastAPI E-Commerce API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database_models.base.metadata.create_all(bind=engine)


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
    payload = decode_jwt(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user_id = int(payload["sub"])
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    token_record = (
        db.query(Token)
        .filter(Token.user_id == user_id, Token.access_token == token, Token.is_active == True)
        .first()
    )
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    return user


def build_cart_response(cart, db: Session):
    items = (
        db.query(CartItems)
        .filter(CartItems.cart_id == cart.cart_id)
        .all()
    )
    return {
        "cart_id": cart.cart_id,
        "user_id": cart.user_id,
        "created_at": cart.created_at,
        "is_active": cart.is_active,
        "items": [
            {
                "cartitem_id": item.cartitem_id,
                "cart_id": item.cart_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "total_price": item.total_price,
            }
            for item in items
        ],
    }


def build_order_response(order, db: Session):
    items = (
        db.query(OrderItems)
        .filter(OrderItems.order_id == order.order_id)
        .all()
    )
    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "delivery_address": order.delivery_address,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "items": [
            {
                "orderitem_id": item.orderitem_id,
                "order_id": item.order_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "total_price": item.total_price,
            }
            for item in items
        ],
    }


@api.get("/health")
def health_check():
    return {"status": "ok", "message": "FastAPI e-commerce backend is running."}


@api.post("/register/", status_code=201, response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(Users).filter(Users.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered.")

    hashed_password = get_hashed_password(user.password)
    new_user = Users(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        password=hashed_password,
        is_seller=user.is_seller,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(new_user.id)
    refresh_token = create_refresh_token(new_user.id)
    token_record = Token(
        user_id=new_user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        is_active=True,
    )
    db.add(token_record)
    db.commit()
    db.refresh(token_record)

    return {"user": new_user, "access_token": access_token, "refresh_token": refresh_token}


@api.post("/login/", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.email == request.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email.")
    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid password.")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    token_record = Token(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        is_active=True,
    )
    db.add(token_record)
    db.commit()
    db.refresh(token_record)

    return {"user": user, "access_token": access_token, "refresh_token": refresh_token}


@api.post("/refresh-token/", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    decoded = decode_jwt(payload.refresh_token, refresh=True)
    if not decoded or "sub" not in decoded:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    user_id = int(decoded["sub"])
    token_record = (
        db.query(Token)
        .filter(Token.user_id == user_id, Token.refresh_token == payload.refresh_token, Token.is_active == True)
        .first()
    )
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    token_record.access_token = new_access_token
    token_record.refresh_token = new_refresh_token
    db.add(token_record)
    db.commit()
    db.refresh(token_record)

    user = db.query(Users).filter(Users.id == user_id).first()
    return {"user": user, "access_token": new_access_token, "refresh_token": new_refresh_token}


@api.post("/logout/")
def logout(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
    payload = decode_jwt(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token.")

    user_id = int(payload["sub"])
    token_record = (
        db.query(Token)
        .filter(Token.user_id == user_id, Token.access_token == token, Token.is_active == True)
        .first()
    )
    if not token_record:
        raise HTTPException(status_code=401, detail="Token not found or already logged out.")

    token_record.is_active = False
    db.add(token_record)
    db.commit()
    return {"message": "User logged out successfully."}


@api.get("/me/", response_model=UserResponse)
def get_profile(current_user: Users = Depends(get_current_user)):
    return current_user


@api.put("/me/", response_model=UserResponse)
def update_profile(user_update: UserUpdate, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@api.post("/become-seller/", response_model=UserResponse)
def become_seller(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.is_seller = True
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@api.post("/seller/products/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_seller:
        raise HTTPException(status_code=403, detail="Only sellers can list products.")
    if product.product_stoke <= 0:
        raise HTTPException(status_code=400, detail="Product stock must be greater than zero.")

    new_product = Products(
        user_id=current_user.id,
        product_name=product.product_name,
        product_description=product.product_description,
        product_price=product.product_price,
        product_stoke=product.product_stoke,
        category=product.category,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@api.get("/seller/products/", response_model=List[ProductResponse])
def get_seller_products(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    products = db.query(Products).filter(Products.user_id == current_user.id).all()
    return products


@api.get("/products/", response_model=List[ProductResponse])
def list_products(query: Optional[str] = None, db: Session = Depends(get_db)):
    products = db.query(Products)
    if query:
        products = products.filter(Products.product_name.ilike(f"%{query}%"))
    return products.order_by(Products.created_at.desc()).all()


@api.get("/products/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Products).filter(Products.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@api.put("/seller/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Products).filter(Products.product_id == product_id, Products.user_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or unauthorized.")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@api.delete("/seller/products/{product_id}")
def delete_product(product_id: int, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Products).filter(Products.product_id == product_id, Products.user_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or unauthorized.")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully."}


@api.get("/cart/", response_model=CartResponse)
def get_or_create_cart(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Carts).filter(Carts.user_id == current_user.id, Carts.is_active == True).first()
    if not cart:
        cart = Carts(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return build_cart_response(cart, db)


@api.post("/cart/items/", response_model=CartItemResponse)
def add_to_cart(
    cart_item: CartItemCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Products).filter(Products.product_id == cart_item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    if product.product_stoke < cart_item.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available.")

    cart = db.query(Carts).filter(Carts.user_id == current_user.id, Carts.is_active == True).first()
    if not cart:
        cart = Carts(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    existing_item = (
        db.query(CartItems)
        .filter(CartItems.cart_id == cart.cart_id, CartItems.product_id == product.product_id)
        .first()
    )
    if existing_item:
        existing_item.quantity += cart_item.quantity
        existing_item.total_price = existing_item.quantity * product.product_price
        db.add(existing_item)
        db.commit()
        db.refresh(existing_item)
        return existing_item

    new_item = CartItems(
        user_id=current_user.id,
        cart_id=cart.cart_id,
        product_id=product.product_id,
        quantity=cart_item.quantity,
        total_price=product.product_price * cart_item.quantity,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@api.get("/cart/items/", response_model=List[CartItemResponse])
def list_cart_items(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Carts).filter(Carts.user_id == current_user.id, Carts.is_active == True).first()
    if not cart:
        return []
    return db.query(CartItems).filter(CartItems.cart_id == cart.cart_id).all()


@api.patch("/cart/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int,
    cart_item: CartItemCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = db.query(Carts).filter(Carts.user_id == current_user.id, Carts.is_active == True).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Active cart not found.")

    item = db.query(CartItems).filter(CartItems.cartitem_id == item_id, CartItems.cart_id == cart.cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")

    if cart_item.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")

    item.quantity = cart_item.quantity
    item.total_price = cart_item.quantity * db.query(Products).filter(Products.product_id == item.product_id).first().product_price
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@api.delete("/cart/items/{item_id}")
def remove_cart_item(item_id: int, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Carts).filter(Carts.user_id == current_user.id, Carts.is_active == True).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Active cart not found.")

    item = db.query(CartItems).filter(CartItems.cartitem_id == item_id, CartItems.cart_id == cart.cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")

    db.delete(item)
    db.commit()
    return {"message": "Cart item removed successfully."}


@api.delete("/cart/clear/")
def clear_cart(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Carts).filter(Carts.user_id == current_user.id, Carts.is_active == True).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Active cart not found.")

    db.query(CartItems).filter(CartItems.cart_id == cart.cart_id).delete()
    db.commit()
    return {"message": "Cart cleared successfully."}


@api.post("/orders/", response_model=OrderResponse)
def place_order(order_data: OrderCreate, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Carts).filter(Carts.user_id == current_user.id, Carts.is_active == True).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Active cart not found.")

    items = db.query(CartItems).filter(CartItems.cart_id == cart.cart_id).all()
    if not items:
        raise HTTPException(status_code=404, detail="No items in cart.")

    total_amount = 0.0
    for item in items:
        product = db.query(Products).filter(Products.product_id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found.")
        if product.product_stoke < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.product_name}.")
        product.product_stoke -= item.quantity
        db.add(product)
        total_amount += item.total_price

    order = Orders(
        user_id=current_user.id,
        total_amount=total_amount,
        delivery_address=order_data.delivery_address,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item in items:
        order_item = OrderItems(
            order_id=order.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            total_price=item.total_price,
        )
        db.add(order_item)

    cart.is_active = False
    db.add(cart)
    db.commit()
    return build_order_response(order, db)


@api.get("/orders/", response_model=List[OrderResponse])
def get_orders(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Orders).filter(Orders.user_id == current_user.id).order_by(Orders.created_at.desc()).all()
    return [build_order_response(order, db) for order in orders]


@api.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    order = (
        db.query(Orders)
        .filter(Orders.order_id == order_id, Orders.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return build_order_response(order, db)


@api.post("/products/{product_id}/reviews/", response_model=ReviewResponse)
def review_product(
    product_id: int,
    review: ReviewCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Products).filter(Products.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    existing_review = (
        db.query(Reviews)
        .filter(Reviews.product_id == product_id, Reviews.user_id == current_user.id)
        .first()
    )
    if existing_review:
        existing_review.rating = review.rating
        existing_review.comment = review.comment
        db.add(existing_review)
        db.commit()
        db.refresh(existing_review)
        return existing_review

    new_review = Reviews(
        user_id=current_user.id,
        product_id=product_id,
        rating=review.rating,
        comment=review.comment,
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


@api.get("/products/{product_id}/reviews/", response_model=List[ReviewResponse])
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Reviews).filter(Reviews.product_id == product_id).order_by(Reviews.created_at.desc()).all()
    return reviews


@api.post("/favorites/", response_model=FavoriteResponse)
def add_favorite(
    favorite: FavoriteCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Products).filter(Products.product_id == favorite.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    existing_favorite = (
        db.query(Favorites)
        .filter(Favorites.user_id == current_user.id, Favorites.product_id == favorite.product_id)
        .first()
    )
    if existing_favorite:
        return existing_favorite

    new_favorite = Favorites(user_id=current_user.id, product_id=favorite.product_id)
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    return new_favorite


@api.get("/favorites/", response_model=List[FavoriteResponse])
def list_favorites(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Favorites)
        .filter(Favorites.user_id == current_user.id)
        .order_by(Favorites.created_at.desc())
        .all()
    )


@api.delete("/favorites/{product_id}")
def remove_favorite(product_id: int, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    favorite = (
        db.query(Favorites)
        .filter(Favorites.user_id == current_user.id, Favorites.product_id == product_id)
        .first()
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite item not found.")
    db.delete(favorite)
    db.commit()
    return {"message": "Favorite removed successfully."}


@api.get("/products/search/", response_model=List[ProductResponse])
def search_products(query: str, db: Session = Depends(get_db)):
    products = db.query(Products).filter(
        Products.product_name.ilike(f"%{query}%") | Products.product_description.ilike(f"%{query}%")
    )
    return products.order_by(Products.created_at.desc()).all()


# Mount static files at root - MUST be last so API routes are matched first
static_dir = Path(__file__).resolve().parents[1] / "frontend"
api.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")



# https://docs.google.com/document/d/14onmXFCQL_AqgE837KHe8FirQBLayT8Y8qdUAGpjqow/edit?tab=t.0