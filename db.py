import os
import json
import sqlite3
from urllib.parse import urlparse

# Check for PostgreSQL database URL from environment (Supabase, Neon, or Vercel Postgres)
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("SUPABASE_DB_URL")

# Resolve project path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data classes matching original application structure
class Id:
    def __init__(self, nameR, emailR, pinR, no=0, typeRoom="None", expen=0):
        self.name = nameR
        self.email = emailR
        self.pin = str(pinR)
        self.roomNo = int(no) if no is not None else 0
        self.roomType = typeRoom or "None"
        self.expenditures = float(expen) if expen is not None else 0.0
        self.myOrderedFoods = []

    def addOrderedFood(self, name, quantity, price):
        orderfood = OrderedFoods(name, int(quantity), float(price))
        self.myOrderedFoods.append(orderfood)


class OrderedFoods:
    def __init__(self, name, quantity, price):
        self.namefood = name
        self.quantity = int(quantity)
        self.price = float(price)


class workers:
    def __init__(self, name, job, salary):
        self.name = name
        self.job = job
        self.salary = float(salary)


class Foods:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = float(price)
        self.quantity = int(quantity)


class Rooms:
    def __init__(self, typeR, priceR, totalR, book, sRoom):
        self.typeRoom = typeR
        self.priceRoom = float(priceR)
        self.totalRooms = int(totalR)
        self.bookRooms = int(book)
        self.startingRoom = int(sRoom)


class RequestResidence:
    def __init__(self, name, email, pin):
        self.name = name
        self.email = email
        self.pin = str(pin)


class RequestJobs:
    def __init__(self, name, email, job):
        self.name = name
        self.email = email
        self.job = job


class ManagerUser:
    def __init__(self, name, email, pin):
        self.name = name
        self.email = email
        self.pin = str(pin)


class OwnerUser:
    def __init__(self, name, email, pin):
        self.name = name
        self.email = email
        self.pin = str(pin)


class Database:
    def __init__(self):
        self.is_postgres = False
        self.conn_str = DATABASE_URL

        if self.conn_str and ("postgres" in self.conn_str or "postgresql" in self.conn_str):
            # Ensure protocol is postgresql:// for SQLAlchemy/pg8000/psycopg2
            if self.conn_str.startswith("postgres://"):
                self.conn_str = self.conn_str.replace("postgres://", "postgresql://", 1)
            self.is_postgres = True
            print("[DB] Using Cloud PostgreSQL / Supabase Database")
        else:
            # Use SQLite in /tmp for Vercel serverless or data/hostel.db locally
            if os.environ.get("VERCEL"):
                self.sqlite_path = "/tmp/hostel.db"
            else:
                data_dir = os.path.join(BASE_DIR, "data")
                os.makedirs(data_dir, exist_ok=True)
                self.sqlite_path = os.path.join(data_dir, "hostel.db")
            print(f"[DB] Using SQLite Database at {self.sqlite_path}")

        self.init_tables()
        self.seed_if_empty()

    def get_connection(self):
        if self.is_postgres:
            try:
                import psycopg2
                return psycopg2.connect(self.conn_str)
            except Exception:
                import pg8000
                p = urlparse(self.conn_str)
                return pg8000.connect(
                    user=p.username,
                    password=p.password,
                    host=p.hostname,
                    port=p.port or 5432,
                    database=p.path.lstrip("/"),
                    ssl_context=True
                )
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn

    def init_tables(self):
        """Create tables if they do not exist."""
        auto_inc = "SERIAL" if self.is_postgres else "INTEGER"
        pk = f"id {auto_inc} PRIMARY KEY" if self.is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"

        schema = f"""
        CREATE TABLE IF NOT EXISTS owners (
            {pk},
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS managers (
            {pk},
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS residents (
            {pk},
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL,
            room_no INTEGER DEFAULT 0,
            room_type TEXT DEFAULT 'None',
            expenditures REAL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS rooms (
            {pk},
            type_room TEXT UNIQUE NOT NULL,
            price_room REAL NOT NULL,
            total_rooms INTEGER NOT NULL,
            book_rooms INTEGER DEFAULT 0,
            starting_room INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS foods (
            {pk},
            name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workers (
            {pk},
            name TEXT NOT NULL,
            job TEXT NOT NULL,
            salary REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            {pk},
            message TEXT NOT NULL,
            sender TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS complaints (
            {pk},
            complain TEXT NOT NULL,
            resident_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS residence_requests (
            {pk},
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            pin TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS job_requests (
            {pk},
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            job TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ordered_foods (
            {pk},
            food_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            resident_name TEXT NOT NULL,
            pin TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn = self.get_connection()
        cur = conn.cursor()
        for stmt in schema.strip().split(";"):
            stmt_clean = stmt.strip()
            if stmt_clean:
                cur.execute(stmt_clean)
        conn.commit()
        cur.close()
        conn.close()

    def seed_if_empty(self):
        """Seed initial Indian dataset if tables are empty."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM owners")
        count = cur.fetchone()[0]
        if count == 0:
            print("[DB] Database is empty. Seeding Indian dataset...")
            # Load from users_credentials.json if available
            creds_path = os.path.join(BASE_DIR, "users_credentials.json")
            if os.path.exists(creds_path):
                with open(creds_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Seed Owner
                for u in data.get("users", {}).get("owner", []):
                    self.execute_insert(conn, "INSERT INTO owners (name, email, pin) VALUES (%s, %s, %s)",
                                        (u["name"], u["email"], str(u["password"])))

                # Seed Managers (2 managers)
                for u in data.get("users", {}).get("managers", []):
                    self.execute_insert(conn, "INSERT INTO managers (name, email, pin) VALUES (%s, %s, %s)",
                                        (u["name"], u["email"], str(u["password"])))

                # Seed Residents (16 residents)
                for u in data.get("users", {}).get("residents", []):
                    self.execute_insert(conn, "INSERT INTO residents (name, email, pin, room_no, room_type, expenditures) VALUES (%s, %s, %s, %s, %s, %s)",
                                        (u["name"], u["email"], str(u["password"]), u.get("room_no", 0), u.get("room_type", "None"), float(u.get("expenditures_inr", 0))))

                # Seed Workers
                for w in data.get("staff_workers", []):
                    self.execute_insert(conn, "INSERT INTO workers (name, job, salary) VALUES (%s, %s, %s)",
                                        (w["name"], w["job"], float(w["salary_inr"])))

                # Seed Foods
                for fd in data.get("canteen_foods", []):
                    self.execute_insert(conn, "INSERT INTO foods (name, price, quantity) VALUES (%s, %s, %s)",
                                        (fd["name"], float(fd["price_inr"]), int(fd["quantity"])))

            # Seed Rooms
            room_seed = [
                ("Single Deluxe", 12000.0, 10, 4, 101),
                ("Double Sharing", 8000.0, 15, 4, 201),
                ("Triple Sharing", 5500.0, 12, 4, 301),
                ("Four Sharing", 4000.0, 10, 4, 401)
            ]
            for r in room_seed:
                self.execute_insert(conn, "INSERT INTO rooms (type_room, price_room, total_rooms, book_rooms, starting_room) VALUES (%s, %s, %s, %s, %s)", r)

            # Seed Messages
            msg_seed = [
                ("Namaste Vikram, please ensure the room inspection for block 2 is completed today.", "owner"),
                ("Namaste Sir, room inspection for 2nd and 3rd floor is done. Everything is in order.", "admin"),
                ("Good. Also verify all new admissions before allocating room keys.", "owner"),
                ("Yes Sir, all documents and fee receipts are being verified at reception.", "admin"),
                ("Priya is managing the warden desk for student welfare and medical kits.", "admin"),
                ("Excellent, keep me updated on the monthly mess expenditure report.", "owner")
            ]
            for m in msg_seed:
                self.execute_insert(conn, "INSERT INTO messages (message, sender) VALUES (%s, %s)", m)

            # Seed Complaints
            comp_seed = [
                ("Room 102 hot water geyser requires inspection", "Ananya Gupta"),
                ("Wi-Fi router on 3rd floor frequent signal drops", "Ishaan Joshi"),
                ("Study room AC filter cleaning requested", "Siddharth Malhotra")
            ]
            for c in comp_seed:
                self.execute_insert(conn, "INSERT INTO complaints (complain, resident_name) VALUES (%s, %s)", c)

            # Seed Residence Requests
            rr_seed = [
                ("Arjun Kapoor", "arjun.kapoor@newadmit.in", "ak2026"),
                ("Kavita Sen", "kavita.sen@newadmit.in", "ks2026")
            ]
            for rr in rr_seed:
                self.execute_insert(conn, "INSERT INTO residence_requests (name, email, pin) VALUES (%s, %s, %s)", rr)

            # Seed Job Requests
            jr_seed = [
                ("Deepak Verma", "deepak.verma@work.in", "Cook Assistant"),
                ("Santosh Patil", "santosh.patil@work.in", "Night Security Guard")
            ]
            for jr in jr_seed:
                self.execute_insert(conn, "INSERT INTO job_requests (name, email, job) VALUES (%s, %s, %s)", jr)

            # Seed Ordered Foods
            of_seed = [
                ("Masala Dosa", 1, 60.0, "Aarav Mehta", "1001"),
                ("Paneer Butter Masala", 1, 150.0, "Ananya Gupta", "1002"),
                ("Butter Naan (2 pcs)", 1, 40.0, "Ananya Gupta", "1002"),
                ("Special Veg Thali", 1, 120.0, "Rohan Verma", "1003"),
                ("Chicken Biryani", 1, 180.0, "Siddharth Malhotra", "1011"),
                ("Gulab Jamun (2 pcs)", 1, 40.0, "Aarav Mehta", "1001")
            ]
            for of in of_seed:
                self.execute_insert(conn, "INSERT INTO ordered_foods (food_name, quantity, price, resident_name, pin) VALUES (%s, %s, %s, %s, %s)", of)

            conn.commit()
            print("[DB] Seeding complete with Indian dataset!")

        cur.close()
        conn.close()

    def execute_insert(self, conn, query, params):
        cur = conn.cursor()
        q = query if self.is_postgres else query.replace("%s", "?")
        cur.execute(q, params)
        cur.close()

    def query(self, sql, params=()):
        conn = self.get_connection()
        cur = conn.cursor()
        q = sql if self.is_postgres else sql.replace("%s", "?")
        cur.execute(q, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def execute(self, sql, params=()):
        conn = self.get_connection()
        cur = conn.cursor()
        q = sql if self.is_postgres else sql.replace("%s", "?")
        cur.execute(q, params)
        conn.commit()
        cur.close()
        conn.close()

    # --- OWNER METHODS ---
    def get_owner(self, email=None, pin=None):
        if email and pin:
            rows = self.query("SELECT name, email, pin FROM owners WHERE email = %s AND pin = %s", (email, str(pin)))
        elif email:
            rows = self.query("SELECT name, email, pin FROM owners WHERE email = %s", (email,))
        else:
            rows = self.query("SELECT name, email, pin FROM owners LIMIT 1")
        if rows:
            r = rows[0]
            return OwnerUser(r[0], r[1], str(r[2]))
        return None

    def update_owner_pin(self, email, new_pin):
        self.execute("UPDATE owners SET pin = %s WHERE email = %s", (str(new_pin), email))

    def register_owner(self, name, email, pin):
        self.execute("INSERT INTO owners (name, email, pin) VALUES (%s, %s, %s)", (name, email, str(pin)))

    # --- MANAGER METHODS ---
    def get_managers(self):
        rows = self.query("SELECT name, email, pin FROM managers ORDER BY id ASC")
        return [ManagerUser(r[0], r[1], str(r[2])) for r in rows]

    def get_manager(self, email=None, pin=None):
        if email and pin:
            rows = self.query("SELECT name, email, pin FROM managers WHERE email = %s AND pin = %s", (email, str(pin)))
        elif email:
            rows = self.query("SELECT name, email, pin FROM managers WHERE email = %s", (email,))
        else:
            rows = self.query("SELECT name, email, pin FROM managers LIMIT 1")
        if rows:
            r = rows[0]
            return ManagerUser(r[0], r[1], str(r[2]))
        return None

    def add_manager(self, name, email, pin):
        self.execute("INSERT INTO managers (name, email, pin) VALUES (%s, %s, %s)", (name, email, str(pin)))

    def update_manager_pin(self, email, new_pin):
        self.execute("UPDATE managers SET pin = %s WHERE email = %s", (str(new_pin), email))

    # --- RESIDENT METHODS ---
    def get_residents(self):
        rows = self.query("SELECT name, email, pin, room_no, room_type, expenditures FROM residents ORDER BY id ASC")
        residents = []
        for r in rows:
            person = Id(r[0], r[1], str(r[2]), r[3], r[4], r[5])
            # load food orders for this resident
            order_rows = self.query("SELECT food_name, quantity, price FROM ordered_foods WHERE resident_name = %s AND pin = %s", (r[0], str(r[2])))
            for of in order_rows:
                person.addOrderedFood(of[0], of[1], of[2])
            residents.append(person)
        return residents

    def get_resident(self, email, pin=None):
        if pin:
            rows = self.query("SELECT name, email, pin, room_no, room_type, expenditures FROM residents WHERE email = %s AND pin = %s", (email, str(pin)))
        else:
            rows = self.query("SELECT name, email, pin, room_no, room_type, expenditures FROM residents WHERE email = %s", (email,))
        if rows:
            r = rows[0]
            person = Id(r[0], r[1], str(r[2]), r[3], r[4], r[5])
            order_rows = self.query("SELECT food_name, quantity, price FROM ordered_foods WHERE resident_name = %s AND pin = %s", (r[0], str(r[2])))
            for of in order_rows:
                person.addOrderedFood(of[0], of[1], of[2])
            return person
        return None

    def add_resident(self, name, email, pin, room_no=0, room_type="None", expen=0):
        self.execute("INSERT INTO residents (name, email, pin, room_no, room_type, expenditures) VALUES (%s, %s, %s, %s, %s, %s)",
                     (name, email, str(pin), int(room_no), room_type, float(expen)))

    def delete_resident(self, name, pin):
        self.execute("DELETE FROM residents WHERE name = %s AND pin = %s", (name, str(pin)))

    def update_resident_pin(self, email, new_pin):
        self.execute("UPDATE residents SET pin = %s WHERE email = %s", (str(new_pin), email))

    def allot_room(self, email, pin, room_type):
        """Allocate a room to resident, increment book_rooms and add expenditure."""
        room_rows = self.query("SELECT type_room, price_room, total_rooms, book_rooms, starting_room FROM rooms WHERE type_room = %s", (room_type,))
        if not room_rows:
            return False
        r = room_rows[0]
        price = float(r[1])
        book_rooms = int(r[3])
        starting_room = int(r[4])

        new_room_no = starting_room + book_rooms + 1
        new_book_rooms = book_rooms + 1

        self.execute("UPDATE rooms SET book_rooms = %s WHERE type_room = %s", (new_book_rooms, room_type))
        self.execute("UPDATE residents SET room_no = %s, room_type = %s, expenditures = expenditures + %s WHERE email = %s AND pin = %s",
                     (new_room_no, room_type, price, email, str(pin)))
        return True

    # --- ROOM METHODS ---
    def get_rooms(self):
        rows = self.query("SELECT type_room, price_room, total_rooms, book_rooms, starting_room FROM rooms ORDER BY id ASC")
        return [Rooms(r[0], r[1], r[2], r[3], r[4]) for r in rows]

    def add_room(self, type_r, price_r, total_r, starting_r):
        self.execute("INSERT INTO rooms (type_room, price_room, total_rooms, book_rooms, starting_room) VALUES (%s, %s, %s, 0, %s)",
                     (type_r, float(price_r), int(total_r), int(starting_r)))

    def delete_room(self, type_r):
        self.execute("DELETE FROM rooms WHERE type_room = %s", (type_r,))

    # --- FOOD METHODS ---
    def get_foods(self):
        rows = self.query("SELECT name, price, quantity FROM foods ORDER BY id ASC")
        return [Foods(r[0], r[1], r[2]) for r in rows]

    def add_food(self, name, price, quantity):
        self.execute("INSERT INTO foods (name, price, quantity) VALUES (%s, %s, %s)",
                     (name, float(price), int(quantity)))

    def delete_food(self, name):
        self.execute("DELETE FROM foods WHERE name = %s", (name,))

    def order_food(self, email, pin, food_name, quantity):
        food_rows = self.query("SELECT price, quantity FROM foods WHERE name = %s", (food_name,))
        if not food_rows:
            return False
        price = float(food_rows[0][0])
        current_qty = int(food_rows[0][1])
        req_qty = int(quantity)

        res_rows = self.query("SELECT name FROM residents WHERE email = %s AND pin = %s", (email, str(pin)))
        if not res_rows:
            return False
        res_name = res_rows[0][0]

        total_cost = price * req_qty
        self.execute("INSERT INTO ordered_foods (food_name, quantity, price, resident_name, pin) VALUES (%s, %s, %s, %s, %s)",
                     (food_name, req_qty, price, res_name, str(pin)))
        self.execute("UPDATE residents SET expenditures = expenditures + %s WHERE email = %s AND pin = %s",
                     (total_cost, email, str(pin)))
        new_qty = max(0, current_qty - req_qty)
        self.execute("UPDATE foods SET quantity = %s WHERE name = %s", (new_qty, food_name))
        return True

    def get_ordered_foods_for_resident(self, resident_name, pin):
        rows = self.query("SELECT food_name, quantity, price FROM ordered_foods WHERE resident_name = %s AND pin = %s ORDER BY id DESC",
                          (resident_name, str(pin)))
        return [OrderedFoods(r[0], r[1], r[2]) for r in rows]

    # --- WORKER METHODS ---
    def get_workers(self):
        rows = self.query("SELECT name, job, salary FROM workers ORDER BY id ASC")
        return [workers(r[0], r[1], r[2]) for r in rows]

    def add_worker(self, name, job, salary):
        self.execute("INSERT INTO workers (name, job, salary) VALUES (%s, %s, %s)",
                     (name, job, float(salary)))

    def delete_worker(self, name, job):
        self.execute("DELETE FROM workers WHERE name = %s AND job = %s", (name, job))

    # --- MESSAGING METHODS ---
    def get_messages(self):
        rows = self.query("SELECT message, sender FROM messages ORDER BY id ASC")
        return [f"{r[0]},{r[1]}" for r in rows]

    def add_message(self, message, sender):
        self.execute("INSERT INTO messages (message, sender) VALUES (%s, %s)", (message, sender))

    # --- COMPLAINTS METHODS ---
    def get_complaints(self):
        rows = self.query("SELECT complain, resident_name FROM complaints ORDER BY id DESC")
        return [f"{r[0]},{r[1]}" for r in rows]

    def add_complaint(self, complain, resident_name):
        self.execute("INSERT INTO complaints (complain, resident_name) VALUES (%s, %s)", (complain, resident_name))

    def get_complaints_count_for_resident(self, resident_name):
        rows = self.query("SELECT COUNT(*) FROM complaints WHERE resident_name = %s", (resident_name,))
        return rows[0][0] if rows else 0

    # --- RESIDENCE & JOB REQUESTS ---
    def get_residence_requests(self):
        rows = self.query("SELECT name, email, pin FROM residence_requests ORDER BY id DESC")
        return [RequestResidence(r[0], r[1], str(r[2])) for r in rows]

    def add_residence_request(self, name, email, pin):
        self.execute("INSERT INTO residence_requests (name, email, pin) VALUES (%s, %s, %s)", (name, email, str(pin)))

    def delete_residence_request(self, email):
        self.execute("DELETE FROM residence_requests WHERE email = %s", (email,))

    def get_job_requests(self):
        rows = self.query("SELECT name, email, job FROM job_requests ORDER BY id DESC")
        return [RequestJobs(r[0], r[1], r[2]) for r in rows]

    def add_job_request(self, name, email, job):
        self.execute("INSERT INTO job_requests (name, email, job) VALUES (%s, %s, %s)", (name, email, job))

    def delete_job_request(self, email):
        self.execute("DELETE FROM job_requests WHERE email = %s", (email,))

# Singleton database instance
db = Database()
