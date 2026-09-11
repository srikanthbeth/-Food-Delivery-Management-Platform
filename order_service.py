from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models.order import Order
from models.order_item import OrderItem
from models.restaurant import Restaurant
from models.customer import Customer

from repositories.cart_repository import (
    clear_cart,
    get_cart_by_customer,
)

from repositories.customer_repository import (
    get_customer_by_id,
)

from repositories.order_repository import (
    create_order,
    get_all_orders,
    get_order_by_id,
    get_orders_by_customer,
    search_orders,
    update_order,
)

from repositories.coupon_repository import (
    get_coupon_by_code,
    increment_coupon_usage,
)

from utils.enums import (
    OrderStatus,
    PaymentStatus,
    RestaurantStatus,
)

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


TAX_RATE = Decimal("0.05")
DELIVERY_FEE = Decimal("40.00")


def validate_customer_access(
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

    if current_user.role.value == "Admin":
        return customer

    if current_user.role.value == "Customer":

        if customer.user_id != current_user.id:
            raise BusinessRuleException(
                "You can only manage your own orders"
            )

        return customer

    raise PermissionError(
        "Insufficient permissions"
    )


def calculate_coupon_discount(
    db: Session,
    coupon_code: str | None,
    subtotal: Decimal,
):
    if not coupon_code:
        return Decimal("0.00"), None

    coupon = get_coupon_by_code(
        db,
        coupon_code.strip().upper(),
    )

    if not coupon:
        raise ResourceNotFoundException(
            "Coupon not found"
        )

    from datetime import date

    if not coupon.status:
        raise BusinessRuleException(
            "Coupon is inactive"
        )

    today = date.today()

    if today < coupon.start_date:
        raise BusinessRuleException(
            "Coupon is not active yet"
        )

    if today > coupon.expiry_date:
        raise BusinessRuleException(
            "Coupon has expired"
        )

    if (
        coupon.usage_limit is not None
        and coupon.usage_count >= coupon.usage_limit
    ):
        raise BusinessRuleException(
            "Coupon usage limit exceeded"
        )

    if subtotal < coupon.minimum_order_value:
        raise BusinessRuleException(
            "Minimum order value not satisfied"
        )

    if coupon.discount_type == "Percentage":

        discount = (
            subtotal
            * coupon.discount_value
            / Decimal("100")
        )

        if coupon.maximum_discount is not None:
            discount = min(
                discount,
                coupon.maximum_discount,
            )

    else:

        discount = min(
            coupon.discount_value,
            subtotal,
        )

    discount = discount.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return discount, coupon


def create_order_service(
    db: Session,
    customer_id: int,
    order_data,
    current_user,
):
    validate_customer_access(
        db,
        customer_id,
        current_user,
    )

    # --------------------------------------------------------
    # GET CUSTOMER CART
    # --------------------------------------------------------

    cart = get_cart_by_customer(
        db,
        customer_id,
    )

    if not cart or not cart.items:
        raise BusinessRuleException(
            "Cart is empty"
        )

    # --------------------------------------------------------
    # VALIDATE ADDRESS
    # --------------------------------------------------------

    address = None

    for customer_address in cart.customer.addresses:
        if (
            customer_address.id
            == order_data.address_id
        ):
            address = customer_address
            break

    if not address:
        raise BusinessRuleException(
            "Address does not belong to customer"
        )

    # --------------------------------------------------------
    # RESTAURANT
    # --------------------------------------------------------

    restaurant_id = (
        cart.items[0]
        .menu_item
        .restaurant_id
    )

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id
        )
        .first()
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    if restaurant.status in (
        RestaurantStatus.CLOSED,
        RestaurantStatus.TEMPORARILY_UNAVAILABLE,
    ):
        raise BusinessRuleException(
            "Restaurant is not accepting orders"
        )

    # --------------------------------------------------------
    # VALIDATE CART ITEMS
    # --------------------------------------------------------

    subtotal = Decimal("0.00")

    for cart_item in cart.items:

        menu_item = cart_item.menu_item

        if not menu_item.availability:
            raise BusinessRuleException(
                f"Menu item '{menu_item.name}' is unavailable"
            )

        item_total = (
            Decimal(str(cart_item.unit_price))
            * cart_item.quantity
        )

        subtotal += item_total

    subtotal = subtotal.quantize(
        Decimal("0.01")
    )

    # --------------------------------------------------------
    # COUPON
    # --------------------------------------------------------

    discount, coupon = calculate_coupon_discount(
        db,
        order_data.coupon_code,
        subtotal,
    )

    # --------------------------------------------------------
    # TAX
    # --------------------------------------------------------

    tax = (
        subtotal * TAX_RATE
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total_amount = (
        subtotal
        + tax
        + DELIVERY_FEE
        - discount
    )

    total_amount = max(
        total_amount,
        Decimal("0.00"),
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # --------------------------------------------------------
    # CREATE ORDER
    # --------------------------------------------------------

    order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        address_id=order_data.address_id,
        subtotal=subtotal,
        delivery_fee=DELIVERY_FEE,
        discount=discount,
        tax=tax,
        total_amount=total_amount,
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
    )

    db.add(order)
    db.flush()

    # --------------------------------------------------------
    # CREATE ORDER ITEMS
    # --------------------------------------------------------

    for cart_item in cart.items:

        item_total = (
            Decimal(
                str(cart_item.unit_price)
            )
            * cart_item.quantity
        )

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=cart_item.menu_item_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            item_total=item_total,
        )

        db.add(order_item)

    # --------------------------------------------------------
    # COUPON USAGE
    # --------------------------------------------------------

    if coupon:
        coupon.usage_count += 1

    # --------------------------------------------------------
    # CLEAR CART
    # --------------------------------------------------------

    db.query(
        cart.items[0].__class__
    ).filter(
        cart.items[0].__class__.cart_id
        == cart.id
    ).delete(
        synchronize_session=False
    )

    db.commit()
    db.refresh(order)

    return order


def get_orders_service(
    db: Session,
    current_user,
):
    if current_user.role.value == "Admin":
        return get_all_orders(db)

    if current_user.role.value == "Customer":

        customer = (
            db.query(Customer)
            .filter(
                Customer.user_id
                == current_user.id
            )
            .first()
        )

        if not customer:
            raise ResourceNotFoundException(
                "Customer profile not found"
            )

        return get_orders_by_customer(
            db,
            customer.id,
        )

    raise PermissionError(
        "Insufficient permissions"
    )


def get_order_service(
    db: Session,
    order_id: int,
    current_user,
):
    order = get_order_by_id(
        db,
        order_id,
    )

    if not order:
        raise ResourceNotFoundException(
            "Order not found"
        )

    if current_user.role.value == "Admin":
        return order

    if current_user.role.value == "Customer":

        if (
            order.customer.user_id
            != current_user.id
        ):
            raise BusinessRuleException(
                "You can only access your own orders"
            )

        return order

    raise PermissionError(
        "Insufficient permissions"
    )


def cancel_order_service(
    db: Session,
    order_id: int,
    current_user,
):
    order = get_order_service(
        db,
        order_id,
        current_user,
    )

    if order.order_status == OrderStatus.DELIVERED:
        raise BusinessRuleException(
            "Delivered order cannot be cancelled"
        )

    if order.order_status == OrderStatus.CANCELLED:
        raise BusinessRuleException(
            "Order is already cancelled"
        )

    if order.order_status in (
        OrderStatus.READY,
        OrderStatus.PICKED_UP,
        OrderStatus.OUT_FOR_DELIVERY,
    ):
        raise BusinessRuleException(
            "Order cannot be cancelled at this stage"
        )

    update_order(
        db,
        order,
        order_status=OrderStatus.CANCELLED,
    )

    return {
        "success": True,
        "message": "Order cancelled successfully",
        "order_id": order.id,
        "order_status": order.order_status,
    }



def search_orders_service(
    db: Session,
    current_user,
    customer_id: int | None = None,
    restaurant_id: int | None = None,
    delivery_partner_id: int | None = None,
    order_status=None,
    payment_status=None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc",
):
    # --------------------------------------------------------
    # VALIDATE AMOUNT RANGE
    # --------------------------------------------------------

    if (
        min_amount is not None
        and max_amount is not None
        and min_amount > max_amount
    ):
        raise BusinessRuleException(
            "Minimum amount cannot be greater than maximum amount"
        )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if current_user.role.value == "Admin":

        orders, total = search_orders(
            db=db,
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            delivery_partner_id=delivery_partner_id,
            order_status=order_status,
            payment_status=payment_status,
            min_amount=min_amount,
            max_amount=max_amount,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    elif current_user.role.value == "Customer":

        customer = (
            db.query(Customer)
            .filter(
                Customer.user_id
                == current_user.id
            )
            .first()
        )

        if not customer:
            raise ResourceNotFoundException(
                "Customer profile not found"
            )

        # Customer can only search their own orders.
        # Ignore any customer_id supplied by the client.
        orders, total = search_orders(
            db=db,
            customer_id=customer.id,
            restaurant_id=restaurant_id,
            delivery_partner_id=delivery_partner_id,
            order_status=order_status,
            payment_status=payment_status,
            min_amount=min_amount,
            max_amount=max_amount,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    else:
        raise PermissionError(
            "Insufficient permissions"
        )

    pages = (
        (total + limit - 1) // limit
        if total > 0
        else 0
    )

    return {
        "items": orders,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
    }