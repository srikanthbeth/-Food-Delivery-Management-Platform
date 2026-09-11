from sqlalchemy.orm import Session

from models.cart import Cart
from models.cart_item import CartItem


def get_cart_by_customer(
    db: Session,
    customer_id: int,
) -> Cart | None:
    return (
        db.query(Cart)
        .filter(Cart.customer_id == customer_id)
        .first()
    )


def create_cart(
    db: Session,
    cart: Cart,
) -> Cart:
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def get_cart_item(
    db: Session,
    item_id: int,
) -> CartItem | None:
    return (
        db.query(CartItem)
        .filter(CartItem.id == item_id)
        .first()
    )


def get_cart_item_by_menu_item(
    db: Session,
    cart_id: int,
    menu_item_id: int,
) -> CartItem | None:
    return (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart_id,
            CartItem.menu_item_id == menu_item_id,
        )
        .first()
    )


def create_cart_item(
    db: Session,
    cart_item: CartItem,
) -> CartItem:
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def update_cart_item(
    db: Session,
    cart_item: CartItem,
    quantity: int,
) -> CartItem:
    cart_item.quantity = quantity
    db.commit()
    db.refresh(cart_item)
    return cart_item


def delete_cart_item(
    db: Session,
    cart_item: CartItem,
) -> None:
    db.delete(cart_item)
    db.commit()


def clear_cart(
    db: Session,
    cart: Cart,
) -> None:
    db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).delete(
        synchronize_session=False
    )

    db.commit()