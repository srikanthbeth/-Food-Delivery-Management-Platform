
from decimal import Decimal

from sqlalchemy.orm import Session

from models.cart import Cart
from models.cart_item import CartItem
from models.menu_item import MenuItem

from repositories.cart_repository import (
    clear_cart,
    create_cart,
    create_cart_item,
    delete_cart_item,
    get_cart_by_customer,
    get_cart_item,
    get_cart_item_by_menu_item,
    update_cart_item,
)

from repositories.customer_repository import (
    get_customer_by_id,
)

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


# ============================================================
# BUILD CART RESPONSE
# ============================================================

def build_cart_response(cart: Cart) -> dict:
    """
    Convert Cart SQLAlchemy object into the response structure.

    Calculates:
    - item_total
    - subtotal
    """

    items = []

    subtotal = Decimal("0.00")

    for item in cart.items:
        unit_price = Decimal(
            str(item.unit_price)
        )

        item_total = (
            unit_price * item.quantity
        )

        subtotal += item_total

        items.append(
            {
                "id": item.id,
                "menu_item_id": item.menu_item_id,
                "quantity": item.quantity,
                "unit_price": float(unit_price),
                "item_total": float(item_total),
            }
        )

    return {
        "id": cart.id,
        "customer_id": cart.customer_id,
        "items": items,
        "subtotal": float(subtotal),
    }


# ============================================================
# CUSTOMER ACCESS VALIDATION
# ============================================================

def validate_customer(
    db: Session,
    customer_id: int,
    current_user,
):
    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if not customer:
        raise ResourceNotFoundException(
            "Customer not found"
        )

    # Admin can manage any customer's cart
    if current_user.role.value == "Admin":
        return customer

    # Customer can manage only their own cart
    if current_user.role.value == "Customer":
        if customer.user_id != current_user.id:
            raise BusinessRuleException(
                "You can only manage your own cart"
            )

        return customer

    raise PermissionError(
        "Insufficient permissions"
    )


# ============================================================
# GET OR CREATE CART
# ============================================================

def get_or_create_cart(
    db: Session,
    customer_id: int,
) -> Cart:

    cart = get_cart_by_customer(
        db,
        customer_id,
    )

    if cart:
        return cart

    cart = Cart(
        customer_id=customer_id,
    )

    return create_cart(
        db,
        cart,
    )


# ============================================================
# CALCULATE SUBTOTAL
# ============================================================

def calculate_subtotal(
    cart: Cart,
) -> Decimal:

    subtotal = Decimal("0.00")

    for item in cart.items:
        unit_price = Decimal(
            str(item.unit_price)
        )

        subtotal += (
            unit_price * item.quantity
        )

    return subtotal


# ============================================================
# ADD CART ITEM
# ============================================================

def add_cart_item_service(
    db: Session,
    customer_id: int,
    item_data,
    current_user,
):

    # Validate customer access
    validate_customer(
        db,
        customer_id,
        current_user,
    )

    # Find menu item
    menu_item = (
        db.query(MenuItem)
        .filter(
            MenuItem.id == item_data.menu_item_id
        )
        .first()
    )

    if not menu_item:
        raise ResourceNotFoundException(
            "Menu item not found"
        )

    # Item must be available
    if not menu_item.availability:
        raise BusinessRuleException(
            "Menu item is unavailable"
        )

    # Get or create cart
    cart = get_or_create_cart(
        db,
        customer_id,
    )

    # Check whether the same item already exists
    existing_item = get_cart_item_by_menu_item(
        db,
        cart.id,
        menu_item.id,
    )

    if existing_item:

        existing_item.quantity += (
            item_data.quantity
        )

        db.commit()
        db.refresh(existing_item)

        # Refresh cart so the latest relationship
        # data is available
        db.refresh(cart)

        return build_cart_response(
            cart
        )

    # Only one restaurant can exist in a cart
    if cart.items:

        existing_restaurant_id = (
            cart.items[0]
            .menu_item
            .restaurant_id
        )

        if (
            existing_restaurant_id
            != menu_item.restaurant_id
        ):
            raise BusinessRuleException(
                "Cart can contain items from only one restaurant"
            )

    # Create cart item
    cart_item = CartItem(
        cart_id=cart.id,
        menu_item_id=menu_item.id,
        quantity=item_data.quantity,
        unit_price=menu_item.price,
    )

    create_cart_item(
        db,
        cart_item,
    )

    # Refresh cart
    db.refresh(cart)

    return build_cart_response(
        cart
    )


# ============================================================
# GET CART
# ============================================================

def get_cart_service(
    db: Session,
    customer_id: int,
    current_user,
):

    validate_customer(
        db,
        customer_id,
        current_user,
    )

    cart = get_cart_by_customer(
        db,
        customer_id,
    )

    # Create an empty cart if one doesn't exist
    if not cart:

        cart = get_or_create_cart(
            db,
            customer_id,
        )

    return build_cart_response(
        cart
    )


# ============================================================
# UPDATE CART ITEM
# ============================================================

def update_cart_item_service(
    db: Session,
    item_id: int,
    item_data,
    current_user,
):

    cart_item = get_cart_item(
        db,
        item_id,
    )

    if not cart_item:
        raise ResourceNotFoundException(
            "Cart item not found"
        )

    cart = cart_item.cart

    # Validate ownership/access
    validate_customer(
        db,
        cart.customer_id,
        current_user,
    )

    # Item must still be available
    if not cart_item.menu_item.availability:
        raise BusinessRuleException(
            "Menu item is unavailable"
        )

    update_cart_item(
        db,
        cart_item,
        item_data.quantity,
    )

    db.refresh(cart)

    return build_cart_response(
        cart
    )


# ============================================================
# REMOVE CART ITEM
# ============================================================

def remove_cart_item_service(
    db: Session,
    item_id: int,
    current_user,
):

    cart_item = get_cart_item(
        db,
        item_id,
    )

    if not cart_item:
        raise ResourceNotFoundException(
            "Cart item not found"
        )

    cart = cart_item.cart

    # Validate ownership/access
    validate_customer(
        db,
        cart.customer_id,
        current_user,
    )

    delete_cart_item(
        db,
        cart_item,
    )

    # Reload cart after deletion
    db.refresh(cart)

    return build_cart_response(
        cart
    )


# ============================================================
# CLEAR CART
# ============================================================

def clear_cart_service(
    db: Session,
    customer_id: int,
    current_user,
):

    validate_customer(
        db,
        customer_id,
        current_user,
    )

    cart = get_cart_by_customer(
        db,
        customer_id,
    )

    # If cart doesn't exist, create an empty cart
    if not cart:

        cart = get_or_create_cart(
            db,
            customer_id,
        )

        return build_cart_response(
            cart
        )

    # Remove all cart items
    clear_cart(
        db,
        cart,
    )

    # Reload cart after deletion
    db.refresh(cart)

    return build_cart_response(
        cart
    )

