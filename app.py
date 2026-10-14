import os
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from db import (
    db, Id, workers, Foods, Rooms,
    RequestResidence, RequestJobs, OrderedFoods,
    ManagerUser, OwnerUser
)

# Set directories
root_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(root_dir, "templates")
if not os.path.exists(template_dir):
    template_dir = os.path.join(root_dir, "templtes")
static_dir = os.path.join(root_dir, "static")

app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir,
    static_url_path="/static"
)
app.secret_key = os.environ.get("SECRET_KEY", "hostel-management-secret-key-2026-secure")

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(static_dir, filename)

# Helper financial calculations
def totalexpenditures():
    residents = db.get_residents()
    return sum(float(r.expenditures) for r in residents)

def totalsalaries():
    staff = db.get_workers()
    return sum(float(w.salary) for w in staff)

# -------------------------------------------------------------
# LANDING & LOGOUT
# -------------------------------------------------------------
@app.route("/")
def Page():
    return render_template("mainLoginPage.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------------------------------------------
# OWNER ROUTES
# -------------------------------------------------------------
@app.route("/loginowner")
def login1():
    return render_template("Owner/loginOwner.html")

@app.route("/ownerhome")
def owner():
    owner_user = db.get_owner()
    owner_email = owner_user.email if owner_user else "rajesh.sharma@hostel.in"
    residents = db.get_residents()
    staff = db.get_workers()
    return render_template(
        "Owner/owner.html",
        variable=owner_email,
        residents=len(residents),
        workers=len(staff),
        totalincome=totalexpenditures(),
        totalsalary=totalsalaries()
    )

@app.route("/createAccountManager")
def createManager():
    owner_user = db.get_owner()
    return render_template("Owner/registerManager.html", variable=owner_user.email if owner_user else "")

@app.route("/sendMessage")
def msgOwner():
    owner_user = db.get_owner()
    return render_template("Owner/sendMessageToManager.html", variable=owner_user.email if owner_user else "")

@app.route("/recieveMessage")
@app.route("/receiveMessage")
def recMessage():
    owner_user = db.get_owner()
    raw_msgs = db.get_messages()
    messages = []
    for m in raw_msgs:
        parts = m.split(",")
        if len(parts) >= 2:
            messages.append({"text": parts[0], "sender": parts[1]})
        else:
            messages.append({"text": m, "sender": "user"})
    return render_template("Owner/recieveMessageOwner.html", variable=owner_user.email if owner_user else "", messages=messages)

@app.route("/residentsDetail")
def ownerResidents():
    owner_user = db.get_owner()
    residents = db.get_residents()
    return render_template("Owner/residentDetail.html", variable=owner_user.email if owner_user else "", MyList=residents)

@app.route("/workersDetail")
def ownerWorkers():
    owner_user = db.get_owner()
    staff = db.get_workers()
    return render_template("Owner/workersDetail.html", variable=owner_user.email if owner_user else "", MyList=staff)

@app.route("/room")
def ownerRooms():
    owner_user = db.get_owner()
    rooms = db.get_rooms()
    return render_template("Owner/roomsDetail.html", variable=owner_user.email if owner_user else "", MyList=rooms)

@app.route("/sendMessageByOwner", methods=['POST', 'GET'])
def smsowner():
    owner_user = db.get_owner()
    if request.method == 'POST':
        sms = request.form.get('sms', '')
        if sms:
            db.add_message(sms, "owner")
    return render_template("Owner/sendMessageToManager.html", variable=owner_user.email if owner_user else "")

@app.route("/owner", methods=['POST', 'GET'])
def ownerLogin():
    if request.method == 'POST':
        pin = request.form.get('pin', '')
        email = request.form.get('myemail', '')
        owner_user = db.get_owner(email, pin)
        if owner_user:
            session['owner_email'] = owner_user.email
            session['user_role'] = 'owner'
            residents = db.get_residents()
            staff = db.get_workers()
            return render_template(
                "Owner/owner.html",
                variable=owner_user.email,
                residents=len(residents),
                workers=len(staff),
                totalincome=totalexpenditures(),
                totalsalary=totalsalaries()
            )
        else:
            return render_template("Owner/loginOwner.html")
    return render_template("Owner/loginOwner.html")

@app.route("/profileowner")
def profile1():
    owner_user = db.get_owner()
    if not owner_user:
        owner_user = OwnerUser("Rajesh Sharma", "rajesh.sharma@hostel.in", "12345")
    return render_template("Owner/profileOwner.html", email=owner_user.email, name=owner_user.name, pin=owner_user.pin)

@app.route("/profilemanagerOwner")
def profile2():
    managers = db.get_managers()
    mgr = managers[0] if managers else ManagerUser("Vikram Patel", "vikram.patel@hostel.in", "1111")
    return render_template("Owner/profileManager.html", email=mgr.email, name=mgr.name, pin=mgr.pin)

@app.route("/signupmanager", methods=['POST', 'GET'])
def signupmgr():
    owner_user = db.get_owner()
    if request.method == 'POST':
        name = request.form.get('name1', '') + " " + request.form.get('name2', '')
        email = request.form.get('email', '')
        pin = request.form.get('password', '')
        db.add_manager(name.strip(), email.strip(), pin.strip())
        residents = db.get_residents()
        staff = db.get_workers()
        return render_template(
            "Owner/owner.html",
            variable=owner_user.email if owner_user else "",
            residents=len(residents),
            workers=len(staff),
            totalincome=totalexpenditures(),
            totalsalary=totalsalaries()
        )
    return render_template("Owner/registerManager.html", variable=owner_user.email if owner_user else "")

@app.route("/registerMyOwner")
def regOwner():
    return render_template("Owner/registerOwner.html")

@app.route("/myregisterOwner", methods=['POST', 'GET'])
def myregOwner():
    if request.method == 'POST':
        name = request.form.get('name1', '') + " " + request.form.get('name2', '')
        email = request.form.get('email', '')
        pin = request.form.get('password', '')
        db.register_owner(name.strip(), email.strip(), pin.strip())
        return render_template("Owner/loginOwner.html")
    return render_template("Owner/registerOwner.html")

@app.route("/forgotpinowner")
def forgotpinowner():
    return render_template("Owner/forgotpinowner.html")

@app.route("/changepasswordowner")
def changePassOwner():
    owner_user = db.get_owner()
    return render_template("Owner/changeownerpin.html", variable=owner_user.email if owner_user else "")

@app.route("/changePinMyOwner", methods=['POST', 'GET'])
def changePinOwner():
    owner_user = db.get_owner()
    if request.method == 'POST':
        old = request.form.get('oldpin', '')
        new = request.form.get('newpin', '')
        if owner_user and owner_user.pin == old:
            db.update_owner_pin(owner_user.email, new)
            return render_template("Owner/loginOwner.html")
    return render_template("Owner/changeownerpin.html", variable=owner_user.email if owner_user else "")

@app.route("/frogotPinOwner", methods=['POST', 'GET'])
def forgotPinOwnerAction():
    if request.method == 'POST':
        email = request.form.get('myemail', '')
        new_pin = request.form.get('pin', '')
        owner_user = db.get_owner(email)
        if owner_user:
            db.update_owner_pin(email, new_pin)
            return render_template("Owner/loginOwner.html")
    return render_template("Owner/forgotpinowner.html")

# -------------------------------------------------------------
# MANAGER ROUTES
# -------------------------------------------------------------
@app.route("/loginmanager")
def login2():
    return render_template("Manager/loginManager.html")

@app.route("/managerhome")
def managerHome():
    email = session.get('manager_email')
    mgr = db.get_manager(email) if email else db.get_manager()
    mgr_email = mgr.email if mgr else "vikram.patel@hostel.in"
    residents = db.get_residents()
    staff = db.get_workers()
    foods = db.get_foods()
    rooms = db.get_rooms()
    return render_template(
        "Manager/manager.html",
        variable=mgr_email,
        totalresidents=len(residents),
        totalworkers=len(staff),
        totalfoods=len(foods),
        types=len(rooms)
    )

@app.route("/manager", methods=['POST', 'GET'])
def managerLogin():
    if request.method == 'POST':
        pin = request.form.get('pin', '')
        email = request.form.get('myemail', '')
        mgr = db.get_manager(email, pin)
        if mgr:
            session['manager_email'] = mgr.email
            session['manager_name'] = mgr.name
            session['user_role'] = 'manager'
            residents = db.get_residents()
            staff = db.get_workers()
            foods = db.get_foods()
            rooms = db.get_rooms()
            return render_template(
                "Manager/manager.html",
                variable=mgr.email,
                totalresidents=len(residents),
                totalworkers=len(staff),
                totalfoods=len(foods),
                types=len(rooms)
            )
        else:
            return render_template("Manager/loginManager.html")
    return render_template("Manager/loginManager.html")

@app.route("/profilemanager")
def profileMgr():
    email = session.get('manager_email')
    mgr = db.get_manager(email) if email else db.get_manager()
    if not mgr:
        mgr = ManagerUser("Vikram Patel", "vikram.patel@hostel.in", "1111")
    return render_template("Manager/profileManager.html", email=mgr.email, name=mgr.name, pin=mgr.pin)

@app.route("/sendMessageManager")
def sendMsgMgr():
    email = session.get('manager_email', "vikram.patel@hostel.in")
    return render_template("Manager/sendMessageToOwner.html", variable=email)

@app.route("/sendMessageByManager", methods=['POST', 'GET'])
def sendMsgByMgr():
    email = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        sms = request.form.get('sms', '')
        if sms:
            db.add_message(sms, "admin")
    return render_template("Manager/sendMessageToOwner.html", variable=email)

@app.route("/recieveMessageManager")
@app.route("/receiveMessageManager")
def recMsgMgr():
    email = session.get('manager_email', "vikram.patel@hostel.in")
    raw_msgs = db.get_messages()
    messages = []
    for m in raw_msgs:
        parts = m.split(",")
        if len(parts) >= 2:
            messages.append({"text": parts[0], "sender": parts[1]})
        else:
            messages.append({"text": m, "sender": "user"})
    return render_template("Manager/recieveMessageManager.html", variable=email, messages=messages)

@app.route("/createAccountresident")
def createResidentPage():
    return render_template("Manager/registerResident.html")

@app.route("/registerResident", methods=['POST', 'GET'])
def registerResident():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        name = request.form.get('name1', '') + " " + request.form.get('name2', '')
        email = request.form.get('email', '')
        pin = request.form.get('password', '')
        db.add_resident(name.strip(), email.strip(), pin.strip())
        residents = db.get_residents()
        staff = db.get_workers()
        foods = db.get_foods()
        rooms = db.get_rooms()
        return render_template(
            "Manager/manager.html",
            variable=email_mgr,
            totalresidents=len(residents),
            totalworkers=len(staff),
            totalfoods=len(foods),
            types=len(rooms)
        )
    return render_template("Manager/registerResident.html")

@app.route("/addWorker")
def addWorkerPage():
    return render_template("Manager/WorkerAdd.html")

@app.route("/addworker", methods=['POST', 'GET'])
def addWorkerAction():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        name = request.form.get('name1', '') + " " + request.form.get('name2', '')
        job = request.form.get('job', '')
        salary = request.form.get('salary', 0)
        db.add_worker(name.strip(), job.strip(), salary)
        staff = db.get_workers()
        return render_template("Manager/workersDetail.html", variable=email_mgr, MyList=staff)
    return render_template("Manager/WorkerAdd.html")

@app.route("/addFood")
def addFoodPage():
    return render_template("Manager/foodAdd.html")

@app.route("/addFastFood", methods=['POST', 'GET'])
def addFoodAction():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        name = request.form.get('name1', '') + " " + request.form.get('name2', '')
        quantity = request.form.get('quantity', 0)
        price = request.form.get('price', 0)
        db.add_food(name.strip(), price, quantity)
        foods = db.get_foods()
        return render_template("Manager/foodDetail.html", variable=email_mgr, MyList=foods)
    return render_template("Manager/foodAdd.html")

@app.route("/residents")
def managerResidents():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    residents = db.get_residents()
    return render_template("Manager/residentDetail.html", variable=email_mgr, MyList=residents)

@app.route("/deleteResident", methods=['POST', 'GET'])
def deleteResident():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        name = request.form.get('name', '')
        pin = request.form.get('pin', '')
        db.delete_resident(name, pin)
    residents = db.get_residents()
    return render_template("Manager/residentDetail.html", variable=email_mgr, MyList=residents)

@app.route("/workers")
def managerWorkers():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    staff = db.get_workers()
    return render_template("Manager/workersDetail.html", variable=email_mgr, MyList=staff)

@app.route("/deleteWorker", methods=['POST', 'GET'])
def deleteWorker():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        name = request.form.get('name', '')
        job = request.form.get('job', '')
        db.delete_worker(name, job)
    staff = db.get_workers()
    return render_template("Manager/workersDetail.html", variable=email_mgr, MyList=staff)

@app.route("/Rooms")
def managerRooms():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    rooms = db.get_rooms()
    return render_template("Manager/roomsDetail.html", variable=email_mgr, MyList=rooms)

@app.route("/deleteRoom", methods=['POST', 'GET'])
def deleteRoom():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        type_r = request.form.get('typeroom', '')
        db.delete_room(type_r)
    rooms = db.get_rooms()
    return render_template("Manager/roomsDetail.html", variable=email_mgr, MyList=rooms)

@app.route("/foods")
def managerFoods():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    foods = db.get_foods()
    return render_template("Manager/foodDetail.html", variable=email_mgr, MyList=foods)

@app.route("/deleteFood", methods=['POST', 'GET'])
def deleteFood():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        name = request.form.get('foodname', '')
        db.delete_food(name)
    foods = db.get_foods()
    return render_template("Manager/foodDetail.html", variable=email_mgr, MyList=foods)

@app.route("/complains")
@app.route("/complaints")
def managerComplaints():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    raw_comp = db.get_complaints()
    complaints = []
    for c in raw_comp:
        parts = c.split(",")
        if len(parts) >= 2:
            complaints.append({"text": parts[0], "sender": parts[1]})
        else:
            complaints.append({"text": c, "sender": "Student"})
    return render_template("Manager/recievedComplains.html", variable=email_mgr, complains=complaints)

@app.route("/requestsResidents")
def managerResidenceReqs():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    requests = db.get_residence_requests()
    return render_template("Manager/requestResidence.html", variable=email_mgr, MyList=requests)

@app.route("/deleteResidentapply", methods=['POST', 'GET'])
def deleteResidentApply():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        email = request.form.get('email', '')
        db.delete_residence_request(email)
    requests = db.get_residence_requests()
    return render_template("Manager/requestResidence.html", variable=email_mgr, MyList=requests)

@app.route("/requestsJobs")
def managerJobReqs():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    requests = db.get_job_requests()
    return render_template("Manager/requestsJobs.html", variable=email_mgr, MyList=requests)

@app.route("/deleteJob", methods=['POST', 'GET'])
def deleteJobAction():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        email = request.form.get('email', '')
        db.delete_job_request(email)
    requests = db.get_job_requests()
    return render_template("Manager/requestsJobs.html", variable=email_mgr, MyList=requests)

@app.route("/changinRoom")
@app.route("/changingRoom")
def addRoomPage():
    return render_template("Manager/Rooms.html")

@app.route("/addanewmyRoom", methods=['POST', 'GET'])
def addNewRoom():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == "POST":
        type_r = request.form.get('typeR', '')
        price_r = request.form.get('priceR', 0)
        total_r = request.form.get('totalR', 0)
        starting_r = request.form.get('startingR', 0)
        db.add_room(type_r, price_r, total_r, starting_r)
        residents = db.get_residents()
        staff = db.get_workers()
        foods = db.get_foods()
        rooms = db.get_rooms()
        return render_template(
            "Manager/manager.html",
            variable=email_mgr,
            totalresidents=len(residents),
            totalworkers=len(staff),
            totalfoods=len(foods),
            types=len(rooms)
        )
    return render_template("Manager/Rooms.html")

@app.route("/changepasswordmanager")
def changePassMgr():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    return render_template("Manager/changemanagerpin.html", variable=email_mgr)

@app.route("/forgotmanagerpin")
def forgotPinMgr():
    return render_template("Manager/forgotpinmanager.html")

@app.route("/changePinMyManager", methods=['POST', 'GET'])
def changePinMgrAction():
    email_mgr = session.get('manager_email', "vikram.patel@hostel.in")
    if request.method == 'POST':
        old = request.form.get('oldpin', '')
        new = request.form.get('newpin', '')
        mgr = db.get_manager(email_mgr, old)
        if mgr:
            db.update_manager_pin(email_mgr, new)
            return render_template("Manager/loginManager.html")
    return render_template("Manager/changemanagerpin.html", variable=email_mgr)

@app.route("/frogotPinManager", methods=['POST', 'GET'])
def forgotPinMgrAction():
    if request.method == 'POST':
        email = request.form.get('myemail', '')
        new_pin = request.form.get('pin', '')
        mgr = db.get_manager(email)
        if mgr:
            db.update_manager_pin(email, new_pin)
            return render_template("Manager/loginManager.html")
    return render_template("Manager/forgotpinmanager.html")

# -------------------------------------------------------------
# RESIDENT ROUTES
# -------------------------------------------------------------
@app.route("/login")
@app.route("/loginresident")
@app.route("/loginResident")
def residentLoginPage():
    return render_template("Resident/loginResident.html")

@app.route("/success", methods=['POST', 'GET'])
def residentLogin():
    if request.method == 'POST':
        pin = request.form.get('pin', '')
        email = request.form.get('myemail', '')
        resident = db.get_resident(email, pin)
        if resident:
            session['resident_email'] = resident.email
            session['resident_name'] = resident.name
            session['resident_pin'] = resident.pin
            session['user_role'] = 'resident'
            complaint_count = db.get_complaints_count_for_resident(resident.name)
            return render_template(
                "Resident/resident.html",
                variable=resident.email,
                roomtype=resident.roomType,
                roomno=resident.roomNo,
                expen=resident.expenditures,
                yourcomplains=complaint_count
            )
        else:
            return render_template("Resident/loginResident.html")
    return render_template("Resident/loginResident.html")

@app.route("/resident")
def residentDashboard():
    email = session.get('resident_email')
    pin = session.get('resident_pin')
    resident = db.get_resident(email, pin) if email else None
    if not resident:
        # Fallback to first resident for demo convenience
        residents = db.get_residents()
        resident = residents[0] if residents else Id("Aarav Mehta", "aarav.mehta@student.in", "1001", 101, "Single Deluxe", 12000)
    complaint_count = db.get_complaints_count_for_resident(resident.name)
    return render_template(
        "Resident/resident.html",
        variable=resident.email,
        roomtype=resident.roomType,
        roomno=resident.roomNo,
        expen=resident.expenditures,
        yourcomplains=complaint_count
    )

@app.route("/profileresident")
def profileResident():
    email = session.get('resident_email')
    resident = db.get_resident(email) if email else db.get_residents()[0]
    return render_template("Resident/profileResident.html", email=resident.email, name=resident.name, pin=resident.pin)

@app.route("/getRoom")
def residentGetRoom():
    email = session.get('resident_email', "aarav.mehta@student.in")
    rooms = db.get_rooms()
    return render_template("Resident/allotmentofRoom.html", variable=email, roomlist=rooms)

@app.route("/getnewRoom", methods=['POST', 'GET'])
def residentAllotRoom():
    if request.method == 'POST':
        email = request.form.get('myemail', '')
        pin = request.form.get('pin', '')
        room_type = request.form.get('room', '')
        success = db.allot_room(email, pin, room_type)
        if success:
            resident = db.get_resident(email, pin)
            complaint_count = db.get_complaints_count_for_resident(resident.name)
            return render_template(
                "Resident/resident.html",
                variable=resident.email,
                roomtype=resident.roomType,
                roomno=resident.roomNo,
                expen=resident.expenditures,
                yourcomplains=complaint_count
            )
    email = session.get('resident_email', "aarav.mehta@student.in")
    rooms = db.get_rooms()
    return render_template("Resident/allotmentofRoom.html", variable=email, roomlist=rooms)

@app.route("/orderfood")
def residentOrderFoodPage():
    email = session.get('resident_email', "aarav.mehta@student.in")
    foods = db.get_foods()
    return render_template("Resident/orderFood.html", variable=email, foodList=foods)

@app.route("/orderfoodnow", methods=['POST', 'GET'])
def residentOrderFoodAction():
    if request.method == 'POST':
        email = request.form.get('email', '')
        pin = request.form.get('pin', '')
        food_name = request.form.get('food', '')
        quantity = request.form.get('quantity', 1)
        db.order_food(email, pin, food_name, quantity)
        resident = db.get_resident(email, pin)
        if resident:
            orders = db.get_ordered_foods_for_resident(resident.name, resident.pin)
            return render_template("Resident/orderedfoods.html", variable=resident.email, foodList=orders)
    email = session.get('resident_email', "aarav.mehta@student.in")
    foods = db.get_foods()
    return render_template("Resident/orderFood.html", variable=email, foodList=foods)

@app.route("/orderfooddetail")
def residentOrderFoodDetail():
    email = session.get('resident_email')
    resident = db.get_resident(email) if email else db.get_residents()[0]
    orders = db.get_ordered_foods_for_resident(resident.name, resident.pin)
    return render_template("Resident/orderedfoods.html", variable=resident.email, foodList=orders)

@app.route("/foodDetail")
def residentFoodDetail():
    email = session.get('resident_email', "aarav.mehta@student.in")
    foods = db.get_foods()
    return render_template("Resident/foodDetails.html", variable=email, MyList=foods)

@app.route("/sendComplains")
@app.route("/sendComplaints")
def residentSendComplaints():
    email = session.get('resident_email', "aarav.mehta@student.in")
    return render_template("Resident/sendComplains.html", variable=email)

@app.route("/sendComplain", methods=['POST', 'GET'])
@app.route("/sendComplaint", methods=['POST', 'GET'])
def residentSendComplaintAction():
    email = session.get('resident_email', "aarav.mehta@student.in")
    resident = db.get_resident(email)
    name = resident.name if resident else "Aarav Mehta"
    if request.method == 'POST':
        sms = request.form.get('sms', '')
        if sms:
            db.add_complaint(sms, name)
    return render_template("Resident/sendComplains.html", variable=email)

@app.route("/forgotpinresident")
def residentForgotPin():
    email = session.get('resident_email', "aarav.mehta@student.in")
    return render_template("Resident/changeresidentpin.html", variable=email)

@app.route("/changepinresident")
def residentChangePin():
    email = session.get('resident_email', "aarav.mehta@student.in")
    return render_template("Resident/forgot-pin-resident.html", variable=email)

@app.route("/changePinMyResident", methods=['POST', 'GET'])
def changePinResidentAction():
    email = session.get('resident_email', "aarav.mehta@student.in")
    if request.method == 'POST':
        old = request.form.get('oldpin', '')
        new = request.form.get('newpin', '')
        resident = db.get_resident(email, old)
        if resident:
            db.update_resident_pin(email, new)
            return render_template("Resident/loginResident.html")
    return render_template("Resident/changeresidentpin.html", variable=email)

@app.route("/frogotPinResident", methods=['POST', 'GET'])
def forgotPinResidentAction():
    if request.method == 'POST':
        email = request.form.get('myemail', '')
        new_pin = request.form.get('pin', '')
        resident = db.get_resident(email)
        if resident:
            db.update_resident_pin(email, new_pin)
            return render_template("Resident/loginResident.html")
    return render_template("Resident/forgot-pin-resident.html")

# -------------------------------------------------------------
# PUBLIC / APPLICANT ROUTES
# -------------------------------------------------------------
@app.route("/peoplehome")
def publicHome():
    return render_template("people.html")

@app.route("/applyresidence")
def publicApplyResidence():
    return render_template("ResidenceApply.html")

@app.route("/applyjob")
def publicApplyJob():
    return render_template("ApplyJob.html")

@app.route("/applyResidence", methods=['POST', 'GET'])
def publicApplyResidenceAction():
    if request.method == "POST":
        name = request.form.get('name1', '') + " " + request.form.get('name2', '')
        email = request.form.get('email', '')
        pin = request.form.get('pin', '')
        db.add_residence_request(name.strip(), email.strip(), pin.strip())
        return render_template("people.html")
    return render_template("ResidenceApply.html")

@app.route("/applyJob", methods=['POST', 'GET'])
def publicApplyJobAction():
    if request.method == "POST":
        name = request.form.get('name1', '') + " " + request.form.get('name2', '')
        email = request.form.get('email', '')
        job = request.form.get('job', '')
        db.add_job_request(name.strip(), email.strip(), job.strip())
        return render_template("people.html")
    return render_template("ApplyJob.html")

# -------------------------------------------------------------
# VERCEL SERVERLESS & LOCAL ENTRYPOINT
# -------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
