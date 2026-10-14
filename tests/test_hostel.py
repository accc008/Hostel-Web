import os
import sys
import tempfile
import pytest

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from werkzeug.security import generate_password_hash, check_password_hash
from db import Database, hash_pin, verify_pin
from app import app


@pytest.fixture
def temp_db(tmp_path):
    """Fixture that initializes a clean, isolated SQLite test database with seed data."""
    db_file = str(tmp_path / "test_hostel.db")
    test_db = Database(db_path=db_file)
    return test_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Fixture providing a Flask test client with an isolated temporary database."""
    db_file = str(tmp_path / "client_hostel.db")
    test_db = Database(db_path=db_file)

    # Monkeypatch the singleton db in app and db modules
    import db
    import app as app_module
    monkeypatch.setattr(db, "db", test_db)
    monkeypatch.setattr(app_module, "db", test_db)

    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client, test_db


# ====================================================================
# TEST A: Manager Resident Registration Lifecycle
# ====================================================================
def test_a_manager_resident_registration(client):
    c, test_db = client

    # 1. Login as Manager
    login_resp = c.post("/manager", data={"myemail": "vikram.patel@hostel.in", "pin": "1111"}, follow_redirects=True)
    assert login_resp.status_code == 200

    with c.session_transaction() as sess:
        assert sess.get("user_role") == "manager"
        assert sess.get("manager_email") == "vikram.patel@hostel.in"

    # 2. Register a new resident
    new_res_email = "test.resident@student.in"
    reg_resp = c.post("/registerResident", data={
        "name1": "Rahul",
        "name2": "Deshmukh",
        "email": new_res_email,
        "password": "rahulpass2026"
    }, follow_redirects=True)
    assert reg_resp.status_code == 200

    # Verify manager remains manager
    with c.session_transaction() as sess:
        assert sess.get("user_role") == "manager"

    # Verify resident record created and password is securely hashed
    resident = test_db.get_resident(new_res_email)
    assert resident is not None
    assert resident.name == "Rahul Deshmukh"
    assert resident.pin.startswith(("pbkdf2:", "scrypt:", "argon2:"))

    # 3. Duplicate email registration is rejected
    dup_resp = c.post("/registerResident", data={
        "name1": "Duplicate",
        "name2": "Resident",
        "email": new_res_email,
        "password": "somepassword"
    }, follow_redirects=True)
    assert b"already exists" in dup_resp.data

    # 4. Logout manager
    c.get("/logout")

    # 5. Resident logs in immediately using credentials
    res_login = c.post("/success", data={"myemail": new_res_email, "pin": "rahulpass2026"}, follow_redirects=True)
    assert res_login.status_code == 200
    with c.session_transaction() as sess:
        assert sess.get("user_role") == "resident"
        assert sess.get("resident_email") == new_res_email


# ====================================================================
# TEST B: Public Residence Application & Approval Lifecycle
# ====================================================================
def test_b_public_residence_application_and_approval(client):
    c, test_db = client

    app_email = "tanvi.kulkarni@applicant.in"
    app_pin = "tanvi2026"

    # 1. Public submits application
    apply_resp = c.post("/applyResidence", data={
        "name1": "Tanvi",
        "name2": "Kulkarni",
        "email": app_email,
        "pin": app_pin
    }, follow_redirects=True)
    assert apply_resp.status_code == 200
    assert b"pending manager approval" in apply_resp.data

    # Verify request in database
    pending_reqs = test_db.get_residence_requests(status="pending")
    assert any(r.email == app_email for r in pending_reqs)

    # 2. Before approval, resident cannot log in
    fail_login = c.post("/success", data={"myemail": app_email, "pin": app_pin})
    assert b"Invalid resident credentials" in fail_login.data

    # 3. Manager logs in and views requests
    c.post("/manager", data={"myemail": "vikram.patel@hostel.in", "pin": "1111"}, follow_redirects=True)
    req_view = c.get("/requestsResidents")
    assert b"Tanvi Kulkarni" in req_view.data

    # 4. Manager approves application
    approve_resp = c.post("/approveResidenceRequest", data={"email": app_email}, follow_redirects=True)
    assert approve_resp.status_code == 200
    assert b"Resident account created" in approve_resp.data

    # Verify status in residence_requests is 'approved'
    approved_reqs = test_db.get_residence_requests(status="approved")
    assert any(r.email == app_email for r in approved_reqs)

    # 5. Duplicate approval is rejected
    dup_approve = c.post("/approveResidenceRequest", data={"email": app_email}, follow_redirects=True)
    assert b"already been approved" in dup_approve.data or b"already exists" in dup_approve.data

    # Verify manager session is still manager (no auto-login as resident)
    with c.session_transaction() as sess:
        assert sess.get("user_role") == "manager"

    # 6. Newly approved resident can now log in
    c.get("/logout")
    res_login = c.post("/success", data={"myemail": app_email, "pin": app_pin}, follow_redirects=True)
    assert res_login.status_code == 200
    with c.session_transaction() as sess:
        assert sess.get("user_role") == "resident"
        assert sess.get("resident_email") == app_email


# ====================================================================
# TEST C: Atomic Room Allocation
# ====================================================================
def test_c_atomic_room_allocation(client):
    c, test_db = client

    # Use seeded resident Aarav Mehta
    res_email = "aarav.mehta@student.in"
    res_pin = "1001"

    # Log in resident
    c.post("/success", data={"myemail": res_email, "pin": res_pin}, follow_redirects=True)

    # Initial state
    res_before = test_db.get_resident(res_email)
    exp_before = res_before.expenditures

    # 1. Allocate room
    room_type = "Single Deluxe"
    allot_resp = c.post("/getnewRoom", data={"pin": res_pin, "room": room_type}, follow_redirects=True)
    assert allot_resp.status_code == 200

    res_after = test_db.get_resident(res_email)
    assert res_after.roomType == room_type
    assert res_after.roomNo > 0
    assert res_after.expenditures == exp_before + 12000.0

    # 2. Fully booked room rejection & atomic rollback test
    # Create a full room category (0 total, 0 booked)
    test_db.add_room("Tiny Capsule", 2000.0, 1, 999)
    # Manually set book_rooms = total_rooms = 1
    test_db.execute("UPDATE rooms SET book_rooms = 1 WHERE type_room = 'Tiny Capsule'")

    success, msg = test_db.allot_room(res_email, res_pin, "Tiny Capsule")
    assert success is False
    assert "fully booked" in msg

    # Verify expenditure and room type did not change on failure
    res_rollback = test_db.get_resident(res_email)
    assert res_rollback.roomType == room_type
    assert res_rollback.expenditures == res_after.expenditures


# ====================================================================
# TEST D: Atomic Food Ordering
# ====================================================================
def test_d_atomic_food_ordering(client):
    c, test_db = client

    res_email = "aarav.mehta@student.in"
    res_pin = "1001"

    # Log in
    c.post("/success", data={"myemail": res_email, "pin": res_pin}, follow_redirects=True)

    # 1. Order food successfully
    food_name = "Masala Dosa"
    foods_before = [f for f in test_db.get_foods() if f.name == food_name][0]
    stock_before = foods_before.quantity
    res_before = test_db.get_resident(res_email)

    order_resp = c.post("/orderfoodnow", data={"pin": res_pin, "food": food_name, "quantity": "2"}, follow_redirects=True)
    assert order_resp.status_code == 200

    foods_after = [f for f in test_db.get_foods() if f.name == food_name][0]
    res_after = test_db.get_resident(res_email)

    assert foods_after.quantity == stock_before - 2
    assert res_after.expenditures == res_before.expenditures + (foods_before.price * 2)

    # 2. Reject order when requested quantity exceeds stock
    excess_qty = foods_after.quantity + 999
    success, msg = test_db.order_food(res_email, res_pin, food_name, excess_qty)
    assert success is False
    assert "Insufficient stock" in msg

    # Verify stock and expenditures remain unchanged
    foods_fail = [f for f in test_db.get_foods() if f.name == food_name][0]
    res_fail = test_db.get_resident(res_email)
    assert foods_fail.quantity == foods_after.quantity
    assert res_fail.expenditures == res_after.expenditures


# ====================================================================
# TEST E: Role-Based Authorization & Session Guards
# ====================================================================
def test_e_role_based_auth_guards(client):
    c, _ = client

    # Clear any active session
    c.get("/logout")

    # 1. Unauthenticated requests redirect to respective login portals
    resp_owner = c.get("/ownerhome")
    assert resp_owner.status_code == 302
    assert "/loginowner" in resp_owner.headers["Location"]

    resp_mgr = c.get("/managerhome")
    assert resp_mgr.status_code == 302
    assert "/loginmanager" in resp_mgr.headers["Location"]

    resp_res = c.get("/resident")
    assert resp_res.status_code == 302
    assert "/login" in resp_res.headers["Location"]

    # 2. Resident cannot access manager or owner routes
    c.post("/success", data={"myemail": "aarav.mehta@student.in", "pin": "1001"}, follow_redirects=True)
    cross_mgr = c.get("/managerhome")
    assert cross_mgr.status_code == 302
    assert "/resident" in cross_mgr.headers["Location"]

    cross_owner = c.get("/ownerhome")
    assert cross_owner.status_code == 302
    assert "/resident" in cross_owner.headers["Location"]

    # 3. Logout clears session completely
    c.get("/logout")
    resp_after_logout = c.get("/resident")
    assert resp_after_logout.status_code == 302
    assert "/login" in resp_after_logout.headers["Location"]


# ====================================================================
# TEST F: Password Hashing & Legacy Plain-Text Upgrade
# ====================================================================
def test_f_password_hashing_and_plain_upgrade(temp_db):
    # Insert a user with legacy plain text PIN directly
    legacy_email = "legacy.user@student.in"
    legacy_pin = "plainsecret123"

    temp_db.execute(
        "INSERT INTO residents (name, email, pin, room_no, room_type, expenditures) VALUES (%s, %s, %s, 0, 'None', 0.0)",
        ("Legacy User", legacy_email, legacy_pin)
    )

    # 1. Verify before login, stored PIN is plain text
    raw_row = temp_db.query("SELECT pin FROM residents WHERE email = %s", (legacy_email,))[0]
    assert raw_row[0] == legacy_pin
    assert not str(raw_row[0]).startswith(("pbkdf2:", "scrypt:", "argon2:"))

    # 2. Authenticate with correct password
    user = temp_db.get_resident(legacy_email, legacy_pin)
    assert user is not None

    # 3. Verify that the password was automatically upgraded to a secure hash
    upgraded_row = temp_db.query("SELECT pin FROM residents WHERE email = %s", (legacy_email,))[0]
    assert upgraded_row[0].startswith(("pbkdf2:", "scrypt:", "argon2:"))
    assert check_password_hash(upgraded_row[0], legacy_pin)

    # 4. Subsequent logins verify against the hash
    user_again = temp_db.get_resident(legacy_email, legacy_pin)
    assert user_again is not None

    # 5. Invalid password fails
    wrong_user = temp_db.get_resident(legacy_email, "wrongpassword")
    assert wrong_user is None


# ====================================================================
# TEST G: Idempotent Seeding
# ====================================================================
def test_g_idempotent_seeding(temp_db):
    # Counts after initial seed
    count_owners_1 = temp_db.query("SELECT COUNT(*) FROM owners")[0][0]
    count_managers_1 = temp_db.query("SELECT COUNT(*) FROM managers")[0][0]
    count_residents_1 = temp_db.query("SELECT COUNT(*) FROM residents")[0][0]

    assert count_owners_1 >= 1
    assert count_managers_1 >= 2
    assert count_residents_1 >= 16

    # Modify a resident's expenditures
    temp_db.execute("UPDATE residents SET expenditures = 99999 WHERE email = 'aarav.mehta@student.in'")

    # Run seed_if_empty again
    temp_db.seed_if_empty()

    # Counts must remain identical
    count_owners_2 = temp_db.query("SELECT COUNT(*) FROM owners")[0][0]
    count_managers_2 = temp_db.query("SELECT COUNT(*) FROM managers")[0][0]
    count_residents_2 = temp_db.query("SELECT COUNT(*) FROM residents")[0][0]

    assert count_owners_1 == count_owners_2
    assert count_managers_1 == count_managers_2
    assert count_residents_1 == count_residents_2

    # Modified record was NOT wiped
    res = temp_db.get_resident("aarav.mehta@student.in")
    assert res.expenditures == 99999.0


# ====================================================================
# TEST H: Production Database Failure Handling
# ====================================================================
def test_h_production_database_failure(monkeypatch):
    # Simulate Vercel environment without DATABASE_URL
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        Database()

    assert "Production deployment on Vercel requires" in str(exc_info.value)
    assert "Ephemeral SQLite in /tmp/hostel.db has been permanently disabled" in str(exc_info.value)
