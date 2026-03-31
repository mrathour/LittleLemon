# Little Lemon Restaurant API

A fully functional production-style REST API for the Little Lemon Restaurant, built with Django REST Framework. This API supports role-based access control, cart management, order workflows, user group management, filtering, pagination, and token authentication.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [System Roles](#system-roles)
- [API Endpoints](#api-endpoints)
- [Installation & Setup](#installation--setup)
- [Environment Setup](#environment-setup)
- [Running the Project](#running-the-project)
- [Authentication](#authentication)
- [Role-Based Access](#role-based-access)
- [Filtering, Search & Ordering](#filtering-search--ordering)
- [Pagination](#pagination)
- [Throttling](#throttling)
- [Key Design Decisions](#key-design-decisions)

---

## Project Overview

The Little Lemon Restaurant API allows client applications (web and mobile) to:

- Browse and manage menu items
- Manage shopping carts
- Place and track orders
- Manage user roles (Manager, Delivery Crew)

Different users have different levels of access based on their assigned role.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Django 4.x | Web framework |
| Django REST Framework | API layer |
| Djoser | Authentication endpoints |
| Token Authentication | API security |
| django-filters | Filtering support |
| SQLite | Database (development) |

---

## Project Structure

```
LittleLemon/
├── LittleLemon/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── LittleLemonAPI/
    ├── models.py          # Data models
    ├── serializers.py     # Request/response serialization
    ├── views.py           # API views and viewsets
    ├── permissions.py     # Custom permission classes
    ├── services.py        # Business logic (cart → order)
    ├── paginations.py     # Pagination configuration
    └── urls.py            # App-level URL routing
```

---

## System Roles

| Role | Description |
|---|---|
| **Customer** | Authenticated user not assigned to any group |
| **Manager** | Assigned to the `Manager` group via Django admin |
| **Delivery Crew** | Assigned to the `Delivery Crew` group via Django admin |

Users not assigned to any group are treated as Customers by default.

---

## API Endpoints

### Authentication (Djoser)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/users/` | Public | Register a new user |
| GET | `/api/users/me/` | Authenticated | Get current user info |
| POST | `/token/login/` | Public | Get auth token |
| POST | `/token/logout/` | Authenticated | Invalidate token |

---

### Menu Items

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/menu-items/` | All authenticated | List all menu items |
| GET | `/api/menu-items/{id}/` | All authenticated | Get single menu item |
| POST | `/api/menu-items/` | Manager | Create menu item |
| PUT/PATCH | `/api/menu-items/{id}/` | Manager | Update menu item |
| DELETE | `/api/menu-items/{id}/` | Manager | Delete menu item |

---

### Cart

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/cart/menu-items/` | Customer | View current cart |
| POST | `/api/cart/menu-items/` | Customer | Add item to cart (updates quantity if exists) |
| DELETE | `/api/cart/menu-items/` | Customer | Clear entire cart |

---

### Orders

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/orders/` | Customer | View own orders |
| GET | `/api/orders/` | Manager | View all orders |
| GET | `/api/orders/` | Delivery Crew | View assigned orders |
| POST | `/api/orders/` | Customer | Create order from cart |
| GET | `/api/orders/{id}/` | All authenticated | View order detail |
| PUT/PATCH | `/api/orders/{id}/` | Manager | Update order (assign crew, change status) |
| PATCH | `/api/orders/{id}/` | Delivery Crew | Update order status only |
| DELETE | `/api/orders/{id}/` | Manager | Delete order |

---

### User Group Management

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/groups/manager/users/` | Manager | List all managers |
| POST | `/api/groups/manager/users/` | Manager | Add user to Manager group |
| DELETE | `/api/groups/manager/users/{id}/` | Manager | Remove user from Manager group |
| GET | `/api/groups/delivery-crew/users/` | Manager | List all delivery crew |
| POST | `/api/groups/delivery-crew/users/` | Manager | Add user to Delivery Crew group |
| DELETE | `/api/groups/delivery-crew/users/{id}/` | Manager | Remove user from Delivery Crew group |

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/mrathour/LittleLemon.git
cd LittleLemon
```

### 2. Install dependencies

```bash
pipenv install
pipenv shell
```

### 3. Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create a superuser (Manager account)

```bash
python manage.py createsuperuser
```

### 5. Create required groups in Django Admin

Go to `http://127.0.0.1:8000/admin/` and create two groups:

```
Groups → Add Group → "Manager"
Groups → Add Group → "Delivery Crew"
```

Then assign your superuser to the `Manager` group.

---

## Environment Setup

> **Important:** Before going to production, move sensitive settings to environment variables.

In `settings.py`:

```python
SECRET_KEY = 'your-secret-key-here'   # Move to .env
DEBUG = True                           # Set to False in production
ALLOWED_HOSTS = []                     # Add your domain in production
```

---

## Running the Project

```bash
python manage.py runserver
```

API is available at: `http://127.0.0.1:8000/`

---

## Authentication

This project uses **Token Authentication** via Djoser.

### Get a token

```bash
POST /token/login/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

### Use the token

Include the token in the `Authorization` header for all subsequent requests:

```
Authorization: Token <your_token_here>
```

---

## Role-Based Access

### Customer
- Browse menu items
- Manage own cart (add, view, clear)
- Place orders from cart
- View own orders only

### Manager
- Full menu item management (create, update, delete)
- View all orders across all users
- Assign delivery crew to orders
- Update order status
- Delete orders
- Manage user group membership

### Delivery Crew
- View orders assigned to them
- Update order status only (`status` field via PATCH)
- Cannot modify any other order fields

---

## Order Workflow

```
1. Customer adds items to cart
   POST /api/cart/menu-items/

2. Customer places order
   POST /api/orders/
   → Cart items copied to OrderItems
   → Cart is cleared automatically
   → Order total calculated

3. Manager assigns delivery crew
   PATCH /api/orders/{id}/
   { "delivery_crew": <user_id> }

4. Delivery crew marks as delivered
   PATCH /api/orders/{id}/
   { "status": true }
```

### Order Status

| `status` | `delivery_crew` | Meaning |
|---|---|---|
| `false` | `null` | Pending — not yet assigned |
| `false` | assigned | Out for delivery |
| `true` | assigned | Delivered |

---

## Filtering, Search & Ordering

### Menu Items (`/api/menu-items/`)

| Parameter | Example | Description |
|---|---|---|
| `search` | `?search=burger` | Search by title |
| `featured` | `?featured=true` | Filter by featured status |
| `category` | `?category=1` | Filter by category ID |
| `ordering` | `?ordering=price` | Sort ascending by price |
| `ordering` | `?ordering=-price` | Sort descending by price |

### Orders (`/api/orders/`)

| Parameter | Example | Description |
|---|---|---|
| `search` | `?search=john` | Search by customer username |
| `status` | `?status=false` | Filter by delivery status |
| `ordering` | `?ordering=-date` | Sort by date descending |
| `ordering` | `?ordering=total` | Sort by total ascending |

---

## Pagination

| Endpoint | Default Page Size | Max Page Size |
|---|---|---|
| `/api/menu-items/` | 10 | 20 |
| `/api/orders/` | 5 | 10 |

Control page size with query parameters:

```
?page=2
?page_size=5
```

---

## Throttling

| User Type | Rate Limit |
|---|---|
| Authenticated users | 30 requests/minute |
| Anonymous users | 10 requests/minute |

---

## Key Design Decisions

**Service Layer** — Cart to order conversion lives in `services.py`, not the view. The entire operation is wrapped in `@transaction.atomic` — if any step fails, all database changes are rolled back.

**Price Snapshotting** — Prices are captured at cart-add time (`unit_price` stored on CartItem). Order items inherit this snapshot, so historical orders are never affected by future price changes.

**Permission Architecture** — Custom permission classes (`IsManager`, `IsDeliveryCrew`, `IsCustomer`) handle role-based access at the view level. Field-level restrictions (delivery crew can only update `status`) are enforced in the view's `partial_update` method.

**Serializer Context** — `OrderSerializer` uses `get_fields()` to dynamically hide the `user` field from non-manager responses. Managers see who placed each order; customers and crew do not.

**`update_or_create` for Cart** — Adding an existing item to the cart updates its quantity rather than returning a conflict error, providing a better API consumer experience.

---

## License

This project was built as part of the Meta Back-End Developer Professional Certificate coursework.