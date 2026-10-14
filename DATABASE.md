# 🗄️ Database Architecture & Relational Schema Specification

This document outlines the complete relational data model for the **Hostel Management System (HMS)**, including table definitions, Entity-Relationship (ER) structures, atomic transaction protocols, password security standards, and cloud integration with **Supabase / PostgreSQL**.

---

## 1. Authoritative Architecture & Production Guardrails

```text
Browser Client
     │  (HTTPS Requests)
     ▼
Flask WSGI Application (Vercel Serverless / Localhost)
     │
     ├── In Production (Vercel):
     │     └── Supabase / PostgreSQL (AUTHORITATIVE & PERSISTENT)
     │           * Strict check: DATABASE_URL must be configured.
     │           * Ephemeral SQLite (/tmp/hostel.db) is permanently DISABLED
     │             to guarantee zero data loss between cold starts.
     │
     └── In Local Development / Testing:
           └── Persistent SQLite (data/hostel.db or pytest tmp_path)
```

---

## 2. Entity-Relationship (ER) Diagram

```text
       +--------------------+
       |       owners       |
       +--------------------+
       | id (PK)            |
       | name               |
       | email (UNIQUE)     |
       | pin (HASHED)       |
       +--------------------+
                 │
                 │ (Oversees Operations & Staff)
                 ▼
       +--------------------+                    +--------------------+
       |      managers      |                    |      workers       |
       +--------------------+                    +--------------------+
       | id (PK)            |                    | id (PK)            |
       | name               |                    | name               |
       | email (UNIQUE)     |                    | job                |
       | pin (HASHED)       |                    | salary             |
       +--------------------+                    +--------------------+
                 │
                 │ (Reviews & Approves Applications)
                 ▼
       +------------------------+
       |   residence_requests   |
       +------------------------+
       | id (PK)                |
       | name                   |
       | email                  |
       | pin (HASHED)           |
       | status (pending/appr)  |
       | created_at             |
       +------------------------+
                 │
                 │ (Approved by Manager -> Account Created)
                 ▼
+--------------------+       (Allots)       +--------------------+
|     residents      | ───────────────────> |       rooms        |
+--------------------+                      +--------------------+
| id (PK)            |                      | id (PK)            |
| name               |                      | type_room (UNIQUE) |
| email (UNIQUE)     |                      | price_room         |
| pin (HASHED)       |                      | total_rooms        |
| room_no            |                      | book_rooms         |
| room_type          |                      | starting_room      |
| expenditures       |                      +--------------------+
+--------------------+
      │            │
      │ (Orders)   │ (Lodges)
      ▼            ▼
+--------------------+     +--------------------+
|   ordered_foods    |     |     complaints     |
+--------------------+     +--------------------+
| id (PK)            |     | id (PK)            |
| food_name          |     | complain           |
| quantity           |     | resident_name      |
| price (FROZEN)     |     | created_at         |
| resident_name      |     +--------------------+
| pin (HASHED)       |
| created_at         |
+--------------------+
      │
      ▼ (Stock Deducted)
+--------------------+
|       foods        |
+--------------------+
| id (PK)            |
| name (UNIQUE)      |
| price              |
| quantity (STOCK)   |
+--------------------+
```

---

## 3. Table Specifications & Data Dictionaries

### 1. `owners`
Stores executive administrator / trustee credentials.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique owner identifier |
| `name` | VARCHAR(100) | NOT NULL | Full name of the owner |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | Login email address |
| `pin` | VARCHAR(255) | NOT NULL | Werkzeug-hashed password (`pbkdf2:sha256`) |

### 2. `managers`
Stores hostel operations managers and wardens.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique manager identifier |
| `name` | VARCHAR(100) | NOT NULL | Full name of manager |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | Login email address |
| `pin` | VARCHAR(255) | NOT NULL | Werkzeug-hashed password (`pbkdf2:sha256`) |

### 3. `residents`
Stores student resident profiles, allocated room numbers, and financial dues.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique resident identifier |
| `name` | VARCHAR(100) | NOT NULL | Full name of resident |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | Login email address |
| `pin` | VARCHAR(255) | NOT NULL | Werkzeug-hashed password (`pbkdf2:sha256`) |
| `room_no` | INTEGER | DEFAULT 0 | Assigned room number |
| `room_type` | VARCHAR(100) | DEFAULT 'None' | Category of room |
| `expenditures` | NUMERIC(10,2)| DEFAULT 0.00 | Total dues accumulated (₹) |

### 4. `rooms`
Manages room inventory, tiered room pricing, and numbering ranges.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique room tier identifier |
| `type_room` | VARCHAR(100) | UNIQUE, NOT NULL | Category name (e.g. Single Deluxe) |
| `price_room`| NUMERIC(10,2)| NOT NULL | Monthly rate in ₹ |
| `total_rooms`| INTEGER | NOT NULL | Total room units in category |
| `book_rooms`| INTEGER | DEFAULT 0 | Currently allocated units |
| `starting_room`| INTEGER | NOT NULL | Base room numbering offset |

### 5. `foods`
Canteen inventory and menu items.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique food item identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Food item name (e.g. Masala Dosa) |
| `price` | NUMERIC(10,2)| NOT NULL | Unit price in ₹ |
| `quantity` | INTEGER | NOT NULL | Current canteen stock count |

### 6. `ordered_foods`
Log of resident food orders with timestamp and resident association.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Order transaction identifier |
| `food_name` | VARCHAR(100) | NOT NULL | Name of ordered item |
| `quantity` | INTEGER | NOT NULL | Quantity ordered |
| `price` | NUMERIC(10,2)| NOT NULL | Unit price frozen at time of order |
| `resident_name`| VARCHAR(100)| NOT NULL | Name of student |
| `pin` | VARCHAR(255) | NOT NULL | Student verification hash |
| `created_at`| TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Order creation timestamp |

### 7. `workers`
Hostel staff payroll, roles, and records.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique staff identifier |
| `name` | VARCHAR(100) | NOT NULL | Staff member's name |
| `job` | VARCHAR(100) | NOT NULL | Designation / Job role |
| `salary` | NUMERIC(10,2)| NOT NULL | Monthly salary in ₹ |

### 8. `complaints`
Student grievance records lodged to management.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Complaint identifier |
| `complain` | TEXT | NOT NULL | Grievance description |
| `resident_name`| VARCHAR(100)| NOT NULL | Lodging student's name |
| `created_at`| TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Submission timestamp |

### 9. `messages`
Confidential operational communications between Owner and Manager.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Message identifier |
| `message` | TEXT | NOT NULL | Message body |
| `sender` | VARCHAR(50) | NOT NULL | Role of sender (`owner` or `admin`) |
| `created_at`| TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Dispatch timestamp |

### 10. `residence_requests`
Public applications submitted by prospective students.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Application identifier |
| `name` | VARCHAR(100) | NOT NULL | Applicant full name |
| `email` | VARCHAR(120) | NOT NULL | Applicant contact email |
| `pin` | VARCHAR(255) | NOT NULL | Securely hashed password for future login |
| `status` | VARCHAR(20) | DEFAULT 'pending' | Status: `pending`, `approved`, `rejected` |
| `created_at`| TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Application timestamp |

### 11. `job_requests`
Public applications submitted by prospective staff candidates.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Application identifier |
| `name` | VARCHAR(100) | NOT NULL | Applicant full name |
| `email` | VARCHAR(120) | NOT NULL | Contact email |
| `job` | VARCHAR(100) | NOT NULL | Desired job role |
| `created_at`| TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Application timestamp |

---

## 4. Atomic Multi-Step Transaction Protocols

### A. Room Allocation (`allot_room`)
1. **Verification**: Validates resident credentials using hashed PIN comparison.
2. **Capacity Check**: Queries room tier; checks if `book_rooms < total_rooms`. If full, immediately aborts with clear error message.
3. **Previous Room Adjustment**: If the resident was previously in another room category, decrements previous category's `book_rooms`.
4. **Atomic Write**: In a single database transaction:
   - Increments `rooms.book_rooms`.
   - Computes unique `room_no = starting_room + book_rooms + 1`.
   - Updates resident `room_no`, `room_type`, and increments `expenditures += price_room`.
5. **Rollback**: Any error or constraint violation rolls back all changes completely.

### B. Canteen Ordering (`order_food`)
1. **Validation**: Enforces `quantity >= 1`.
2. **Verification**: Authenticates resident credentials.
3. **Inventory Check**: Queries `foods` table; ensures `food.quantity >= requested_quantity`.
4. **Atomic Write**: In a single database transaction:
   - Deducts requested quantity from `foods.quantity`.
   - Inserts immutable record into `ordered_foods` with unit price frozen at order time.
   - Increments resident `expenditures += (unit_price * quantity)`.
5. **Rollback**: If stock is insufficient, transaction rolls back with zero modifications to stock or resident balances.

---

## 5. Security & Password Lifecycle

1. **Hashing Standard**: Passwords and PINs are hashed using Werkzeug (`generate_password_hash` with PBKDF2:SHA256).
2. **Seamless Legacy Upgrade**: When an existing user with a legacy plain-text password logs in, the system verifies the plain text and immediately upgrades the database record to a salted hash.
3. **Role Guards**: All routes are protected by `@login_required(role=...)`. Hardcoded fallback emails have been eradicated from the application.

---

## 6. Supabase Cloud Integration

### Production Environment Variable
In your Vercel Project Settings -> **Environment Variables**:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

### Automatic Seeding & Idempotency
- When `db.py` initializes against an empty database, it idempotently seeds the Indian dataset (1 Owner, 2 Managers, 16 Residents, 4 Room tiers, 5 Staff members, 10 Canteen items) with hashed credentials and INR prices.
- On subsequent restarts, existing records are detected and preserved. User-modified data is never overwritten.
