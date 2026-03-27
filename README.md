# 🛒 ShopZone — E-Commerce API

A production-grade Django REST API for a multi-seller e-commerce platform.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Client (React / Mobile)                                │
└────────────────┬────────────────────────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────────────────────────┐
│  Nginx (reverse proxy + static files)                   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Django + Gunicorn (4 workers)                          │
│  ├── accounts  (auth, sellers, addresses)               │
│  ├── products  (catalog, variants, images)              │
│  ├── cart      (cart, coupons)                         │
│  ├── orders    (orders, PDF invoices)                   │
│  └── chat      (buyer ↔ seller messaging)              │
└───────┬─────────────────────┬───────────────────────────┘
        │                     │
┌───────▼───────┐    ┌────────▼────────┐
│  PostgreSQL   │    │  Redis          │
│  (primary DB) │    │  (cache+celery) │
└───────────────┘    └────────┬────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Celery Workers   │
                    │  + Beat Scheduler │
                    └───────────────────┘
```

## 🚀 Quick Start

```bash
# 1. Clone & enter directory
cd src-main

# 2. Start all services
docker-compose up -d

# 3. Create superuser
docker-compose exec web python manage.py createsuperuser

# 4. API is live at http://localhost:8000
```

## 👥 User Roles

| Role   | Can Do                                              |
|--------|-----------------------------------------------------|
| Buyer  | Browse, add to cart, place orders, chat with seller |
| Seller | Manage products, view/update orders, send invoices  |
| Admin  | Approve seller requests, manage everything          |

### Becoming a Seller
1. Register as normal buyer
2. POST `/api/accounts/seller-request/` with store details
3. Admin reviews in Django Admin panel → approves
4. User role automatically changes to `seller`

## 📡 API Endpoints

### 🔐 Auth — `/api/accounts/`
| Method | Endpoint            | Auth | Description              |
|--------|---------------------|------|--------------------------|
| POST   | register/           | ❌   | Register new user        |
| POST   | verify-otp/         | ❌   | Verify email OTP         |
| POST   | resend-otp/         | ❌   | Resend OTP               |
| POST   | login/              | ❌   | Login → JWT tokens       |
| POST   | logout/             | ✅   | Blacklist refresh token  |
| POST   | google/             | ❌   | Google OAuth login       |
| POST   | token/refresh/      | ❌   | Refresh access token     |
| GET    | profile/            | ✅   | Get my profile           |
| PATCH  | profile/            | ✅   | Update profile           |
| POST   | change-password/    | ✅   | Change password          |
| POST   | forgot-password/    | ❌   | Request reset OTP        |
| POST   | reset-password/     | ❌   | Reset password with OTP  |
| POST   | seller-request/     | ✅   | Apply to become seller   |
| GET    | seller-request/     | ✅   | Check request status     |
| GET    | addresses/          | ✅   | List my addresses        |
| POST   | addresses/          | ✅   | Add new address          |
| PATCH  | addresses/{id}/     | ✅   | Update address           |
| DELETE | addresses/{id}/     | ✅   | Delete address           |

### 🛍️ Products — `/api/products/`
| Method | Endpoint              | Auth     | Description                |
|--------|-----------------------|----------|----------------------------|
| GET    |                       | ❌       | List products (filterable) |
| GET    | categories/           | ❌       | Category tree              |
| GET    | featured/             | ❌       | Featured products          |
| GET    | best-sellers/         | ❌       | Best sellers               |
| GET    | on-sale/              | ❌       | On-sale products           |
| GET    | {slug}/               | ❌       | Product detail             |
| GET    | my-products/          | 🏪Seller | List my products           |
| POST   | my-products/          | 🏪Seller | Create product             |
| PATCH  | my-products/{slug}/   | 🏪Seller | Update product             |
| DELETE | my-products/{slug}/   | 🏪Seller | Remove product (soft)      |

#### Product Filters
```
GET /api/products/?search=shoes&category=footwear&tag=sale
GET /api/products/?on_sale=true&ordering=-price
GET /api/products/?featured=true&type=physical
```

### 🛒 Cart — `/api/cart/`
| Method | Endpoint                       | Auth | Description          |
|--------|--------------------------------|------|----------------------|
| GET    |                                | ✅   | View cart            |
| DELETE |                                | ✅   | Clear cart           |
| GET    | summary/                       | ✅   | Cart totals (header) |
| POST   | add/                           | ✅   | Add item             |
| PATCH  | items/{id}/                    | ✅   | Update quantity      |
| DELETE | items/{id}/remove/             | ✅   | Remove item          |
| POST   | items/{id}/save/               | ✅   | Save for later       |
| POST   | items/{id}/move-to-cart/       | ✅   | Move back to cart    |
| POST   | coupon/                        | ✅   | Apply coupon         |
| DELETE | coupon/                        | ✅   | Remove coupon        |

### 📦 Orders — `/api/orders/`
| Method | Endpoint                        | Auth     | Description             |
|--------|---------------------------------|----------|-------------------------|
| POST   | place/                          | ✅       | Place order from cart   |
| GET    |                                 | ✅       | My orders               |
| GET    | {order_number}/                 | ✅       | Order detail            |
| DELETE | {order_number}/                 | ✅       | Cancel order            |
| GET    | {order_number}/invoice/         | ✅       | 📄 Download PDF invoice |
| GET    | seller/orders/                  | 🏪Seller | My incoming orders      |
| PATCH  | seller/items/{id}/update/       | 🏪Seller | Update item status      |
| GET    | seller/items/{id}/invoice/      | 🏪Seller | Download buyer invoice  |

#### Order Status Flow
```
pending → confirmed → processing → shipped → delivered
                    ↘ cancelled
```

### 💬 Chat — `/api/chat/`
| Method | Endpoint              | Auth | Description              |
|--------|-----------------------|------|--------------------------|
| GET    |                       | ✅   | List my conversations    |
| POST   | start/                | ✅   | Start chat with seller   |
| GET    | {id}/                 | ✅   | Get conversation messages|
| POST   | {id}/send/            | ✅   | Send a message           |

## 🔑 Authentication

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

Token expires in 60 minutes. Refresh with:
```json
POST /api/accounts/token/refresh/
{ "refresh": "<refresh_token>" }
```

## 📄 PDF Invoice

Invoices include:
- Store branding (ShopZone logo + colors)
- Order number, date, status
- Buyer shipping address
- Itemized product table (name, variant, qty, price)
- Subtotal, discount, shipping, **total**
- Thank you footer

## ⚡ Performance Features

- **Redis caching** — API responses cached (5 min TTL)
- **DB connection pooling** — `CONN_MAX_AGE=60`
- **select_related / prefetch_related** — no N+1 queries
- **Celery async tasks** — emails sent in background
- **Pagination** — 20 items per page
- **WhiteNoise** — optimized static file serving

## 🔒 Security

- JWT with token blacklisting on logout
- OTP email verification (SHA-256 hashed)
- Rate limiting (30/min anon, 120/min user)
- Password validation (length, common, similarity)
- Seller approval gate (admin must approve)
- CORS configured
- `SECURE_CONTENT_TYPE_NOSNIFF` enabled

## 🧪 Example: Full Buyer Flow

```bash
# 1. Register
POST /api/accounts/register/
{ "email": "buyer@example.com", "full_name": "Ahmed", "password": "...", "password2": "..." }

# 2. Verify OTP from email
POST /api/accounts/verify-otp/
{ "email": "buyer@example.com", "otp": "123456" }
→ Returns: { "access": "...", "refresh": "..." }

# 3. Add address
POST /api/accounts/addresses/
{ "label": "Home", "full_name": "Ahmed Ali", "phone": "01012345678",
  "address_line1": "123 Tahrir St", "city": "Cairo", "country": "Egypt" }

# 4. Browse & add to cart
GET /api/products/?category=electronics
POST /api/cart/add/
{ "variant_id": 5, "quantity": 2 }

# 5. Apply coupon (optional)
POST /api/cart/coupon/
{ "code": "SAVE10" }

# 6. Place order
POST /api/orders/place/
{ "address_id": 1, "payment_method": "cod" }
→ Returns full order object

# 7. Download invoice
GET /api/orders/ORD-12345678/invoice/
→ Returns PDF file
```

## 🧪 Example: Full Seller Flow

```bash
# 1. Apply to become seller
POST /api/accounts/seller-request/
{ "store_name": "Ahmed's Store", "description": "...", "national_id": "...", "phone": "..." }

# 2. Wait for admin approval (get notified by email)

# 3. Add products
POST /api/products/my-products/
{ "name": "Nike Shoes", "category": 3, "base_price": "499.00",
  "product_type": "physical", "description": "..." }

# 4. Check incoming orders
GET /api/orders/seller/orders/

# 5. Mark order as shipped
PATCH /api/orders/seller/items/42/update/
{ "item_status": "shipped", "tracking_number": "EG123456789" }

# 6. Chat with buyer
GET /api/chat/  (see buyer messages)
POST /api/chat/5/send/
{ "content": "Your order has been shipped!" }
```
