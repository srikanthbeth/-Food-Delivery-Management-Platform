# Restaurant & Food Delivery Management System

A complete **Restaurant & Food Delivery Management System** built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, **JWT Authentication**, **Alembic**, and **Pytest**.

The system provides end-to-end functionality for restaurant management, menu management, customers, carts, coupons, orders, delivery partners, payments, refunds, reviews, notifications, dashboards, analytics, security, and data integrity.

---

## Project Overview

The Restaurant & Food Delivery Management System is designed as a scalable backend platform that manages the complete food-ordering lifecycle.

### Main Workflow

```text
Register
   ↓
Login
   ↓
Create Restaurant
   ↓
Add Menu Items
   ↓
Customer Login
   ↓
Add Address
   ↓
Add Items to Cart
   ↓
Apply Coupon
   ↓
Place Order
   ↓
Make Payment
   ↓
Assign Delivery Partner
   ↓
Track Order
   ↓
Deliver Order
   ↓
Submit Review
```

---

## Technology Stack

| Technology         | Purpose                     |
| ------------------ | --------------------------- |
| Python 3.10+       | Programming Language        |
| FastAPI            | REST API Framework          |
| Pydantic           | Request/Response Validation |
| SQLAlchemy ORM     | Database ORM                |
| PostgreSQL         | Relational Database         |
| Alembic            | Database Migrations         |
| JWT                | Authentication              |
| Passlib/Bcrypt     | Password Hashing            |
| Uvicorn            | ASGI Server                 |
| Pytest             | Automated Testing           |
| FastAPI TestClient | API Testing                 |

---

# User Roles

The application supports five major roles:

1. **Admin**
2. **Restaurant Owner**
3. **Restaurant Staff**
4. **Delivery Partner**
5. **Customer**

Role-Based Access Control (RBAC) is implemented throughout the application to ensure users can access only the operations permitted for their role.

---

# Completed Levels

The following assignment levels have been implemented:

### Level 1 – Authentication & Authorization

* User registration
* User login
* JWT authentication
* Refresh tokens
* Current user information
* Change password
* User activation/deactivation
* Role-Based Access Control
* Password hashing

### Level 2 – Restaurant Management

* Create restaurant
* View restaurants
* Search restaurants
* Restaurant details
* Update restaurant
* Delete restaurant
* Restaurant ownership validation
* Restaurant status management

### Level 3 – Menu & Food Items

* Add menu items
* View menu items
* Search menu items
* Update menu items
* Delete menu items
* Food availability
* Vegetarian/non-vegetarian information
* Spicy level
* Preparation time

### Level 4 – Customer & Address Management

* Customer management
* Customer profile
* Address creation
* Address retrieval
* Address updates
* Default address support
* Customer ownership validation

### Level 5 – Cart Management

* Add items to cart
* View cart
* Update quantity
* Remove cart items
* Clear cart
* Quantity validation
* Menu item validation

### Level 6 – Coupons & Offers

* Create coupons
* View coupons
* Apply coupons
* Fixed discounts
* Percentage discounts
* Minimum order validation
* Maximum discount validation
* Coupon expiry validation
* Usage limits

### Level 7 – Order Management

* Create orders
* Order items
* Order totals
* Delivery charges
* Tax calculation
* Discount calculation
* Coupon integration
* Order status
* Order search
* Order history

### Level 8 – Delivery Partner Management

* Create delivery partners
* View delivery partners
* Availability status
* Driver assignment
* Vehicle information
* Delivery partner management

### Level 9 – Order Tracking

* Order tracking history
* Tracking status
* Location updates
* Delivery remarks
* Order status synchronization
* Tracking access control

### Level 10 – Payments

* Payment creation
* Payment methods
* Transaction IDs
* Payment validation
* Duplicate transaction prevention
* Payment ownership validation
* Payment status management
* Order payment status synchronization
* Amount validation

Supported payment methods:

* UPI
* Card
* Wallet
* Cash on Delivery

### Level 11 – Cancellation & Refund

* Order cancellation
* Refund processing
* Refund records
* Payment refund status
* Cancellation validation
* Refund validation
* Duplicate refund prevention

### Level 12 – Reviews & Ratings

* Customer reviews
* Restaurant ratings
* Food item ratings
* Delivery partner ratings
* Rating validation
* Delivered-order validation
* Review ownership validation

### Level 13 – Search, Filtering & Pagination

* Restaurant search
* Menu item search
* Order search
* Filtering
* Pagination
* Sorting
* Validation of search parameters

### Level 14 – Notifications

* User notifications
* Unread notifications
* Mark notification as read
* Background task processing
* Notification generation
* Notification access control

### Level 15 – Restaurant Dashboard

* Restaurant dashboard
* Order statistics
* Revenue statistics
* Menu statistics
* Customer/order insights
* Restaurant performance information

### Level 16 – Admin Analytics

* Overall order analytics
* Revenue analytics
* Restaurant analytics
* Customer analytics
* Payment analytics
* Delivery analytics
* System-level statistics

### Level 17 – Security & Data Integrity

Security and data-integrity features include:

* JWT authentication
* Role-Based Access Control
* Password hashing
* Foreign key constraints
* Unique constraints
* Request validation
* Database transactions
* Global exception handling
* Audit logging
* Soft delete support
* CORS configuration
* Ownership validation

---

# Automated Testing

The complete automated test suite has been executed successfully.

## Test Result

```text
468 passed, 4 warnings in 546.46s (0:09:06)
```

### Final Test Status

| Result                 |   Count |
| ---------------------- | ------: |
| Passed                 | **468** |
| Failed                 |   **0** |
| Warnings               |   **4** |
| Total Successful Tests | **468** |

### Test Suite Status

**✅ 468 tests passed successfully**

**❌ 0 tests failed**

The warnings are deprecation warnings and do not indicate test failures.

---

# Testing

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Run the complete test suite:

```powershell
pytest -q
```

Run tests with detailed output:

```powershell
pytest -v
```

Run a specific test file:

```powershell
pytest tests/test_payment.py -v
```

Run a specific test:

```powershell
pytest tests/test_payment.py::test_payment_success -v
```

---

# Database

The project uses **PostgreSQL** as the primary database.

Alembic is used for database schema migrations.

### Check Migration History

```powershell
alembic history
```

### Check Current Migration

```powershell
alembic current
```

### Check Migration Heads

```powershell
alembic heads
```

### Apply Migrations

```powershell
alembic upgrade head
```

### Create a New Migration

```powershell
alembic revision --autogenerate -m "migration message"
```

---

# Architecture

The project follows a clean layered architecture.

```text
Routes
   ↓
Services
   ↓
Repositories
   ↓
Models
   ↓
Database
```

### Routes

Responsible for:

* API endpoints
* Authentication dependencies
* Request handling
* Response handling

### Services

Responsible for:

* Business logic
* Authorization
* Business rules
* Validation
* Transactions

### Repositories

Responsible for:

* Database queries
* Create operations
* Update operations
* Delete operations
* Filtering and retrieval

### Models

Responsible for:

* SQLAlchemy database models
* Relationships
* Foreign keys
* Constraints

### Schemas

Responsible for:

* Request validation
* Response serialization
* Pydantic models

---

# Project Structure

```text
restaurant_food_delivery/
│
├── models/
│   ├── user.py
│   ├── restaurant.py
│   ├── menu_item.py
│   ├── customer.py
│   ├── address.py
│   ├── cart.py
│   ├── cart_item.py
│   ├── coupon.py
│   ├── order.py
│   ├── order_item.py
│   ├── delivery_partner.py
│   ├── order_tracking.py
│   ├── payment.py
│   ├── refund.py
│   ├── review.py
│   ├── notification.py
│   └── audit_log.py
│
├── schemas/
│   ├── user.py
│   ├── restaurant.py
│   ├── menu.py
│   ├── customer.py
│   ├── address.py
│   ├── cart.py
│   ├── coupon.py
│   ├── order.py
│   ├── delivery_partner.py
│   ├── tracking.py
│   ├── payment.py
│   ├── refund.py
│   ├── review.py
│   ├── notification.py
│   └── audit_log.py
│
├── repositories/
│   ├── user_repository.py
│   ├── restaurant_repository.py
│   ├── menu_repository.py
│   ├── customer_repository.py
│   ├── cart_repository.py
│   ├── coupon_repository.py
│   ├── order_repository.py
│   ├── delivery_repository.py
│   ├── tracking_repository.py
│   ├── payment_repository.py
│   ├── refund_repository.py
│   ├── review_repository.py
│   ├── notification_repository.py
│   └── audit_log_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── restaurant_service.py
│   ├── menu_service.py
│   ├── customer_service.py
│   ├── cart_service.py
│   ├── coupon_service.py
│   ├── order_service.py
│   ├── delivery_service.py
│   ├── tracking_service.py
│   ├── payment_service.py
│   ├── refund_service.py
│   ├── review_service.py
│   ├── notification_service.py
│   ├── dashboard_service.py
│   ├── analytics_service.py
│   └── audit_log_service.py
│
├── routes/
│   ├── auth.py
│   ├── restaurants.py
│   ├── menu.py
│   ├── customers.py
│   ├── cart.py
│   ├── coupons.py
│   ├── orders.py
│   ├── delivery.py
│   ├── tracking.py
│   ├── payments.py
│   ├── refunds.py
│   ├── reviews.py
│   ├── notifications.py
│   ├── dashboard.py
│   ├── admin_analytics.py
│   └── audit_logs.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_restaurant.py
│   ├── test_menu.py
│   ├── test_customer.py
│   ├── test_cart.py
│   ├── test_coupon.py
│   ├── test_order.py
│   ├── test_delivery.py
│   ├── test_tracking.py
│   ├── test_payment.py
│   ├── test_refund.py
│   ├── test_review.py
│   ├── test_search.py
│   ├── test_notifications.py
│   ├── test_dashboard.py
│   └── test_admin_analytics.py
│
├── utils/
│   ├── auth.py
│   ├── enums.py
│   ├── exceptions.py
│   ├── security.py
│   └── exception_handlers.py
│
├── alembic/
│   └── versions/
│
├── database.py
├── main.py
├── alembic.ini
├── requirements.txt
└── README.md
```

---

# API Documentation

Start the FastAPI server:

```powershell
uvicorn main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

---

# Main API Modules

### Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
PUT  /api/v1/auth/change-password
PUT  /api/v1/auth/users/{user_id}/status
```

### Restaurants

```text
GET    /api/v1/restaurants
POST   /api/v1/restaurants
GET    /api/v1/restaurants/search
GET    /api/v1/restaurants/{restaurant_id}
PUT    /api/v1/restaurants/{restaurant_id}
DELETE /api/v1/restaurants/{restaurant_id}
```

### Menu

```text
POST   /api/v1/menu/items
GET    /api/v1/menu/items
GET    /api/v1/menu/items/search
GET    /api/v1/menu/items/{menu_item_id}
PUT    /api/v1/menu/items/{menu_item_id}
DELETE /api/v1/menu/items/{menu_item_id}
```

### Customers & Addresses

```text
POST /api/v1/customers
GET  /api/v1/customers/{customer_id}

POST /api/v1/customers/{customer_id}/addresses
GET  /api/v1/customers/{customer_id}/addresses
PUT  /api/v1/addresses/{address_id}
```

### Cart

```text
POST   /api/v1/cart/items
GET    /api/v1/cart
PUT    /api/v1/cart/items/{item_id}
DELETE /api/v1/cart/items/{item_id}
DELETE /api/v1/cart/clear
```

### Coupons

```text
GET  /api/v1/coupons
POST /api/v1/coupons
POST /api/v1/coupons/apply
```

### Orders

```text
POST /api/v1/orders
GET  /api/v1/orders
GET  /api/v1/orders/search
GET  /api/v1/orders/{order_id}
POST /api/v1/orders/{order_id}/cancel
```

### Delivery

```text
GET  /api/v1/delivery-partners
POST /api/v1/delivery-partners
PUT  /api/v1/delivery-partners/{delivery_partner_id}/status

POST /api/v1/orders/{order_id}/assign-driver
```

### Tracking

```text
POST /api/v1/orders/{order_id}/tracking
GET  /api/v1/orders/{order_id}/tracking
```

### Payments

```text
POST /api/v1/payments/{order_id}
GET  /api/v1/payments/{payment_id}
GET  /api/v1/orders/{order_id}/payment
```

### Refunds

```text
POST /api/v1/payments/{payment_id}/refund
GET  /api/v1/refunds
```

### Reviews

```text
POST /api/v1/reviews
GET  /api/v1/restaurants/{restaurant_id}/reviews
GET  /api/v1/food-items/{food_item_id}/reviews
```

### Notifications

```text
GET /api/v1/notifications
GET /api/v1/notifications/unread
PUT /api/v1/notifications/{notification_id}/read
```

### Restaurant Dashboard

```text
GET /api/v1/restaurants/dashboard
```

### Admin Analytics

```text
GET /api/v1/admin/analytics
```

### Audit Logs

```text
GET /api/v1/audit-logs
```

---

# Security Features

The application implements multiple security and data-integrity mechanisms.

### JWT Authentication

Protected endpoints require a valid JWT access token.

### Role-Based Access Control

Access to APIs is controlled according to the user's role.

### Password Security

Passwords are stored using secure password hashing rather than plain text.

### Ownership Validation

Users cannot access or modify resources belonging to other users without authorization.

### Database Constraints

Foreign keys and unique constraints protect relational data integrity.

### Request Validation

Pydantic validates incoming API requests before business logic is executed.

### Global Exception Handling

Common application exceptions are converted into consistent API responses.

### Audit Logging

Important system actions can be recorded with:

* User
* Action
* Resource type
* Resource ID
* Description
* IP address
* Timestamp

### Soft Delete

Supported resources can be marked as deleted without immediately removing their database records.

### CORS

Cross-Origin Resource Sharing is configured for controlled frontend/API integration.

---

# Demo Accounts

The following accounts can be used for demonstration.

| Role             | Email                | Password     |
| ---------------- | -------------------- | ------------ |
| Admin            | `admin@example.com`  | `Admin@123`  |
| Restaurant Owner | `suresh@example.com` | `Suresh@123` |
| Customer         | `ravi@example.com`   | `Ravi@123`   |

For security, these credentials should be changed or removed before using the project in a production environment.

---

# Example Demo Data

### Restaurant

```text
Restaurant:
Sri Annapurna Restaurant

City:
Tirupati

Cuisine:
Indian

Status:
Open
```

### Menu Item

```text
Chicken Biryani
Price: ₹250
Preparation Time: 30 minutes
```

### Coupon

```text
Code: WELCOME50
Type: FIXED
Discount: ₹50
Minimum Order: ₹300
```

---

# Example Order

A sample completed order can contain:

```text
Restaurant:
Sri Annapurna Restaurant

Item:
Chicken Biryani × 3

Subtotal:
₹750

Delivery Fee:
₹40

Discount:
₹50

Tax:
₹37.50

Total:
₹777.50

Payment:
Paid

Order Status:
Delivered
```

---

# Running the Project

## 1. Clone the Repository

```powershell
git clone <repository-url>
cd restaurant_food_delivery
```

## 2. Create Virtual Environment

```powershell
python -m venv venv
```

## 3. Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

## 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

## 5. Configure Database

Configure the PostgreSQL database connection using the project's environment configuration.

Example:

```text
DATABASE_URL=postgresql+psycopg://username:password@localhost:5433/restaurant_food_delivery
```

## 6. Run Database Migrations

```powershell
alembic upgrade head
```

## 7. Start the Server

```powershell
uvicorn main:app --reload
```

## 8. Open Swagger

```text
http://127.0.0.1:8000/docs
```

---

# Testing

Run all tests:

```powershell
pytest -q
```

Expected successful result:

```text
468 passed, 4 warnings in 546.46s
```

The test suite completed successfully with:

```text
468 PASSED
0 FAILED
4 WARNINGS
```

The warnings are related to dependency/API deprecations and do not represent failed tests.

---

# Database Migrations

The project uses Alembic for version-controlled database migrations.

Migration history includes database changes for:

* Users
* Restaurants
* Menu Items
* Customers
* Addresses
* Cart
* Coupons
* Orders
* Delivery Partners
* Order Tracking
* Payments
* Refunds
* Reviews
* Additional security/data-integrity features

Useful commands:

```powershell
alembic history
```

```powershell
alembic current
```

```powershell
alembic heads
```

```powershell
alembic upgrade head
```

---

# Future Enhancements

Possible future improvements include:

* Redis caching
* Docker containerization
* WebSocket-based live order tracking
* Google Maps integration
* PDF invoice generation
* Excel report generation
* Celery background workers
* CI/CD pipeline
* Advanced analytics
* Cloud deployment
* Payment gateway integration
* Real-time customer notifications

---

# Project Highlights

* Complete food delivery backend
* RESTful API architecture
* JWT authentication
* RBAC authorization
* Secure password hashing
* PostgreSQL database
* SQLAlchemy ORM
* Alembic migrations
* Business-rule validation
* Payment and refund management
* Order tracking
* Notifications
* Restaurant dashboard
* Admin analytics
* Audit logging
* Soft delete
* Global exception handling
* Comprehensive automated testing

---

# Final Test Status

```text
========================================
       RESTAURANT FOOD DELIVERY
            TEST RESULTS
========================================

Passed : 468
Failed : 0
Warnings: 4

Status : SUCCESS
========================================
```

**468 automated tests passed successfully.**

---

# Author

**Srikanth Bethamcharla**
