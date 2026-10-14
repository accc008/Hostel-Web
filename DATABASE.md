# 🗄️ Database Architecture & Relational Schema Specification

This document outlines the complete relational data model for the **Hostel Management System (HMS)**, including table definitions, Entity-Relationship (ER) structures, and cloud integration with **Supabase / PostgreSQL**.

---

## 1. Entity-Relationship (ER) Diagram

```text
       +--------------------+
       |       owners       |
       +--------------------+
       | id (PK)            |
       | name               |
       | email (UNIQUE)     |
       | pin                |
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
       | pin                |                    | salary             |
       +--------------------+                    +--------------------+
                 │
                 │ (Manages Residents, Rooms, Food, Complaints)
                 ▼
+--------------------+       (Allots)       +--------------------+
|     residents      | ───────────────────> |       rooms        |
+--------------------+                      +--------------------+
| id (PK)            |                      | id (PK)            |
| name               |                      | type_room (UNIQUE) |
| email (UNIQUE)     |                      | price_room         |
| pin                |                      | total_rooms        |
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
| price              |     | created_at         |
| resident_name      |     +--------------------+
| pin                |
| created_at         |
+--------------------+
      │
      ▼ (References)
+--------------------+
|       foods        |
+--------------------+
| id (PK)            |
| name (UNIQUE)      |
| price              |
| quantity           |
+--------------------+
```

---

## 2. Table Specifications & Data Dictionaries

### 1. `owners`
Stores executive administrator / trustee credentials.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique owner identifier |
| `name` | VARCHAR(100) | NOT NULL | Full name of the owner |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | Login email address |
| `pin` | VARCHAR(50) | NOT NULL | Security PIN / Password |

### 2. `managers`
Stores hostel operations managers and wardens.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique manager identifier |
| `name` | VARCHAR(100) | NOT NULL | Full name of manager |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | Login email address |
| `pin` | VARCHAR(50) | NOT NULL | Security PIN / Password |

### 3. `residents`
Stores student resident profiles, allocated room numbers, and financial dues.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL / INT | PRIMARY KEY | Unique resident identifier |
| `name` | VARCHAR(100) | NOT NULL | Full name of resident |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | Login email address |
| `pin` | VARCHAR(50) | NOT NULL | Security PIN / Password |
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
| `price` | NUMERIC(10,2)| NOT NULL | Price at time of order |
| `resident_name`| VARCHAR(100)| NOT NULL | Name of student |
| `pin` | VARCHAR(50) | NOT NULL | Student authentication PIN |
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

### 10. `residence_requests` & `job_requests`
Public queues for prospective student admissions and job applicants.

---

## 3. Supabase Cloud Integration

### Step-by-Step Setup
1. **Create Project**: Sign in to [Supabase](https://supabase.com) and create a new project.
2. **Execute Schema (Optional)**:
   - Navigate to the **SQL Editor** tab in your Supabase dashboard.
   - Copy the contents of [`schema.sql`](schema.sql) and click **Run**.
   *(Note: This step is optional because `db.py` will automatically execute `CREATE TABLE IF NOT EXISTS` upon first startup).*
3. **Configure Environment Variable**:
   - In Supabase, open **Project Settings** -> **Database**.
   - Copy the **Connection URI** (use port 5432 or 6543 pooler).
   - In your Vercel Project Dashboard, add:
     ```env
     DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
     ```
4. **Auto-Seeding**: Upon the first request, the database engine detects empty tables and auto-populates the entire Indian dataset from `users_credentials.json`.
