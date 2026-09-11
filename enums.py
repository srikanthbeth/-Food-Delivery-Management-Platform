from enum import Enum


class UserRole(str, Enum):
    ADMIN = "Admin"
    RESTAURANT_OWNER = "Restaurant Owner"
    RESTAURANT_STAFF = "Restaurant Staff"
    DELIVERY_PARTNER = "Delivery Partner"
    CUSTOMER = "Customer"


class RestaurantStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    BUSY = "Busy"
    TEMPORARILY_UNAVAILABLE = "Temporarily Unavailable"

class OrderStatus(str, Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    PREPARING = "Preparing"
    READY = "Ready"
    PICKED_UP = "Picked Up"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class PaymentStatus(str, Enum):
    PENDING = "Pending"
    PAID = "Paid"
    FAILED = "Failed"
    REFUNDED = "Refunded"   

class DeliveryAvailabilityStatus(str, Enum):
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"
    ON_DELIVERY = "On Delivery"


class TrackingStatus(str, Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    PREPARING = "Preparing"
    READY = "Ready"
    PICKED_UP = "Picked Up"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"



class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "Card"
    WALLET = "Wallet"
    CASH_ON_DELIVERY = "Cash on Delivery"


class PaymentTransactionStatus(str, Enum):
    PENDING = "Pending"
    SUCCESSFUL = "Successful"
    FAILED = "Failed"
    REFUNDED = "Refunded"