# 🏛️ System Architecture & OOP Design Documentation

This document provides a comprehensive technical overview of the **Hostel Management System (HMS)** architecture, detailing its software design patterns, Object-Oriented Programming (OOP) principles, data flow pipelines, and serverless hosting adaptations.

---

## 1. High-Level System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                 CLIENT BROWSERS                                   |
|   (Desktop, Tablet, Mobile - Owner / Manager / Resident / Public Guest Portals)   |
+-----------------------------------------------------------------------------------+
                                         │  HTTPS / HTTP Requests
                                         ▼
+-----------------------------------------------------------------------------------+
|                       EDGE ROUTING & SERVERLESS RUNTIME                           |
|                    Vercel Edge Network -> api/index.py (WSGI)                     |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                          CORE APPLICATION (app.py)                                |
|  - Flask Routing Controllers & Request Validation                                 |
|  - Encrypted Client-Side Cookie Session Management (Flask session)                |
|  - Server-Side Jinja2 Template Rendering Engine (templates/)                      |
|  - Static Asset Delivery (static/css, static/js, static/vendor)                   |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                    DUAL-MODE DATABASE ENGINE (db.py)                              |
|  - Abstract Database Layer with Polymorphic Query Execution                       |
|  - Auto-Migration & Schema Bootstrap (schema.sql)                                 |
|  - Auto-Seeding Engine (users_credentials.json)                                   |
+-----------------------------------------------------------------------------------+
                     │                                         │
     (DATABASE_URL set)                               (Fallback / Local)
                     ▼                                         ▼
+---------------------------------------+   +---------------------------------------+
|        SUPABASE POSTGRESQL            |   |           LOCAL SQLITE                |
|  - Cloud PostgreSQL Relational DB     |   |  - Embedded serverless DB (/tmp)      |
|  - Permanent multi-tenant persistence |   |  - Zero-config local dev (hostel.db)  |
|  - Connection pooling (pg8000/psycopg)|   |  - Synchronized flat files (data/*.txt|
+---------------------------------------+   +---------------------------------------+
```

---

## 2. Object-Oriented Programming (OOP) Principles Applied

The application is structured to demonstrate the core tenets of Object-Oriented Programming:

### A. Encapsulation
Every business entity is modeled as an independent class that encapsulates its internal state, attributes, and mutation behaviors:
- **`Id` (Resident Entity)**: Encapsulates personal identity (`name`, `email`, `pin`), allocated room details (`roomNo`, `roomType`), accumulated financial liabilities (`expenditures`), and associated food orders (`myOrderedFoods`).
  ```python
  class Id:
      def __init__(self, nameR, emailR, pinR, no=0, typeRoom="None", expen=0):
          self.name = nameR
          self.email = emailR
          self.pin = str(pinR)
          self.roomNo = int(no)
          self.roomType = typeRoom
          self.expenditures = float(expen)
          self.myOrderedFoods = []

      def addOrderedFood(self, name, quantity, price):
          orderfood = OrderedFoods(name, int(quantity), float(price))
          self.myOrderedFoods.append(orderfood)
  ```
- **`Rooms`**: Encapsulates room category names, monthly pricing, total room capacity, currently booked inventory, and starting numbering offsets.
- **`Foods`**: Encapsulates canteen menu pricing and stock quantity.
- **`workers`**: Encapsulates staff job title, compensation, and personnel identification.

### B. Abstraction
The data layer (`Database` class in `db.py`) abstracts away the underlying database engine:
- Calling code in `app.py` invokes high-level domain operations like `db.get_residents()`, `db.allot_room()`, or `db.order_food()` without needing to know whether the target database is SQLite or PostgreSQL.
- SQL parameter binding differences (`%s` for PostgreSQL vs `?` for SQLite) are abstracted inside the `Database.execute_insert()` and `Database.query()` methods.

### C. Polymorphism
The database query execution adapts dynamically:
- If `DATABASE_URL` is configured, connection objects adapt to PostgreSQL drivers (`psycopg2` or `pg8000`).
- If no cloud database is specified, connection objects adapt seamlessly to SQLite (`sqlite3`).
- Return objects from both database engines instantiate identical domain models (`Id`, `Rooms`, `Foods`), providing uniform interfaces to Flask route controllers.

---

## 3. Serverless vs Traditional Monolith Adaptation

| Architectural Dimension | Traditional Flask Monolith | Modernized Serverless Adaptation (This Project) |
| :--- | :--- | :--- |
| **Process Model** | Long-running daemon process | Ephemeral, stateless execution per HTTP request |
| **Session Storage** | In-memory global variables (`MyEmail`, `MyPin`) | Cryptographically signed client-side session cookies (`Flask session`) |
| **Filesystem Write** | Persistent local disk writes | Dual-mode: writes to `/tmp/hostel.db` on serverless, or cloud PostgreSQL via Supabase |
| **Concurrency** | Single-user race condition on global variables | Isolated request contexts with zero state leakage across concurrent users |
| **Scalability** | Vertical server scaling | Auto-scaling horizontal execution on Vercel Edge nodes |

---

## 4. Security & Defensive Design

1. **Cookie-Based Cryptographic Signing**: Sessions use `app.secret_key` with HMAC signing, preventing client-side session tampering.
2. **Parameterized SQL Queries**: All queries execute with parameterized arguments, preventing SQL injection vulnerabilities.
3. **Graceful Fallbacks**: If the cloud database connection temporarily drops or is unconfigured, the application falls back to local storage without throwing unhandled 500 exceptions.
4. **Environment Isolation**: Production credentials, secrets, and database strings are managed through `os.environ` rather than hardcoded in source control.
