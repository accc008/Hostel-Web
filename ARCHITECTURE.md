# 🏛️ System Architecture & Production Engineering Documentation

This document provides a comprehensive technical overview of the **Hostel Management System (HMS)** architecture, detailing its software design patterns, Object-Oriented Programming (OOP) principles, data flow pipelines, role-based security boundaries, and authoritative persistence layers.

---

## 1. High-Level System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                 CLIENT BROWSERS                                   |
|   (Desktop, Tablet, Mobile - Owner / Manager / Resident / Public Guest Portals)   |
+-----------------------------------------------------------------------------------+
                                         │  HTTPS Requests
                                         ▼
+-----------------------------------------------------------------------------------+
|                       EDGE ROUTING & SERVERLESS RUNTIME                           |
|                    Vercel Edge Network -> api/index.py (WSGI)                     |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                          CORE APPLICATION (app.py)                                |
|  - Role-Based Authentication Guards (@login_required(role=...))                    |
|  - Cryptographically Signed Session Cookies (HttpOnly, SameSite=Lax)              |
|  - Post-Redirect-Get (PRG) Pattern to Prevent Form Resubmissions                  |
|  - Dynamic Jinja2 Server-Side Template Rendering Engine                           |
|  - Static Asset Delivery (CDN Fallbacks for FontAwesome, Bootstrap, Datatables)   |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                    AUTHORITATIVE DATABASE ENGINE (db.py)                          |
|  - Unified Adapter with Dynamic SQL Parameter Translation (%s vs ?)               |
|  - Single-Transaction Atomic Operations (Room Allotment, Food Ordering)           |
|  - Password Hashing & Seamless Legacy Plain-Text Upgrade Engine                   |
|  - Public Application Review & Account Provisioning Lifecycle                     |
|  - Idempotent Seeding Engine (users_credentials.json)                             |
+-----------------------------------------------------------------------------------+
                     │                                         │
     (VERCEL=1: DATABASE_URL Required)                 (Local Development / Testing)
                     ▼                                         ▼
+---------------------------------------+   +---------------------------------------+
|        SUPABASE POSTGRESQL            |   |           LOCAL SQLITE                |
|  - Authoritative Cloud PostgreSQL DB  |   |  - Persistent dev database            |
|  - Zero cold-start data loss          |   |    (data/hostel.db)                   |
|  - Connection pooling (pg8000/psycopg)|   |  - Isolated test fixtures for pytest  |
|  - Strict Vercel production check     |   |  - Zero configuration setup           |
+---------------------------------------+   +---------------------------------------+
```

---

## 2. Object-Oriented Programming (OOP) Principles Applied

### A. Encapsulation
Every business entity is modeled as an independent class that encapsulates its internal state, attributes, and mutation behaviors:
- **`Id` (Resident Entity)**: Encapsulates personal identity (`name`, `email`, `pin`), allocated room details (`roomNo`, `roomType`), accumulated financial liabilities (`expenditures`), and associated food orders (`myOrderedFoods`).
- **`Rooms`**: Encapsulates room category names, monthly pricing, total room capacity, currently booked inventory, and starting numbering offsets.
- **`Foods`**: Encapsulates canteen menu pricing, unit economics, and stock quantity.
- **`workers`**: Encapsulates staff job title, compensation, and personnel identification.
- **`RequestResidence`**: Encapsulates prospective student applications, tracking name, email, credentials, and lifecycle status (`pending`, `approved`, `rejected`).

### B. Abstraction
The data layer (`Database` class in `db.py`) abstracts away the underlying database engine:
- Calling code in `app.py` invokes high-level domain operations like `db.get_residents()`, `db.allot_room()`, `db.order_food()`, or `db.approve_residence_request()` without coupling to SQLite or PostgreSQL drivers.
- Differences in parameter binding syntax (`%s` in PostgreSQL vs `?` in SQLite) and auto-increment keywords (`SERIAL` vs `INTEGER PRIMARY KEY AUTOINCREMENT`) are abstracted internally.

### C. Polymorphism
The database query execution adapts dynamically:
- If `DATABASE_URL` is configured, connection objects adapt to PostgreSQL drivers (`psycopg2` or `pg8000`).
- If in local development or test mode, connection objects adapt to `sqlite3`.
- Return rows from both engines map into identical domain models (`Id`, `Rooms`, `Foods`), providing uniform interfaces to Flask route controllers.

---

## 3. Production Architecture vs Previous Vulnerabilities

| Architectural Dimension | Previous Vulnerable Implementation | Production-Hardened Architecture |
| :--- | :--- | :--- |
| **Vercel Data Persistence** | Silent fallback to `/tmp/hostel.db`, wiped on serverless cold starts | **Authoritative Supabase PostgreSQL**. Raises explicit `RuntimeError` if `DATABASE_URL` is missing on Vercel. |
| **Public Applications** | Submissions stuck in `residence_requests` with no approval workflow | **Full Approval Lifecycle**: Manager reviews applications, clicks "Approve", creating a resident account transactionally with hashed password. |
| **Password Storage** | Plain-text strings stored in database | **Werkzeug Password Hashing** (`pbkdf2:sha256`) with automatic seamless upgrade of legacy plain-text upon login. |
| **Authorization Guards** | No decorators; routes fell back to hardcoded demo strings (`vikram.patel@hostel.in`) | **Strict `@login_required(role=...)`** decorator. Zero hardcoded fallback identities. Unauthenticated users are redirected. |
| **Transaction Integrity** | Multi-statement room allotment and food ordering without atomicity | **Single-Transaction Atomic Operations** with concurrency checks, capacity guards, stock checks, and automatic rollback. |
| **Seeding Idempotency** | Seeding dependent only on owner count; risk of duplicate or wiped data | **Idempotent Independent Seeding**: Each table checked separately; never overwrites user data upon restart. |

---

## 4. End-to-End Data Lifecycles

### 1. Resident Admission Lifecycle
```text
Public Applicant visits /applyresidence
     │
     ▼ Submits Name, Email, Password
Record created in residence_requests (status = 'pending')
     │
     ▼ Manager navigates to /requestsResidents
Manager reviews application and clicks "Approve"
     │
     ▼ Single Atomic Transaction (approve_residence_request)
1. Checks applicant not already approved.
2. Checks email uniqueness in residents table.
3. Hashes password and inserts into residents table.
4. Updates residence_requests status to 'approved'.
     │
     ▼ Success Notification
Applicant can now immediately log in at /login with their email and password!
```

### 2. Room Allocation Lifecycle
```text
Authenticated Resident visits /getRoom
     │
     ▼ Selects Room Tier (Single Deluxe, Double Sharing, etc.)
POST to /getnewRoom -> db.allot_room(email, pin, room_type)
     │
     ▼ Single Atomic Transaction
1. Authenticates resident credentials.
2. Checks room capacity (book_rooms < total_rooms).
3. If full: rolls back and returns "fully booked" error.
4. Increments book_rooms, assigns new room_no.
5. Updates resident record and adds room price to expenditures.
     │
     ▼ Redirect to /resident dashboard displaying new room & updated dues.
```

### 3. Canteen Order Lifecycle
```text
Authenticated Resident visits /orderfood
     │
     ▼ Selects Food Item & Quantity
POST to /orderfoodnow -> db.order_food(email, pin, food_name, quantity)
     │
     ▼ Single Atomic Transaction
1. Validates quantity >= 1.
2. Checks canteen inventory (food.quantity >= requested_quantity).
3. If insufficient: rolls back and returns stock error.
4. Deducts stock from foods table.
5. Records order in ordered_foods with price frozen at order time.
6. Adds total cost to resident expenditures.
     │
     ▼ Redirect to /orderfooddetail showing order history.
```
