# სერვერის გაშვება და კონფიგურაცია
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

# Flask აპლიკაციის შექმნა
app = Flask(__name__)
app.config["SECRET_KEY"] = "chatapdonttellpassword"  # გასაღების კოდი სესიებისთვის
socketio = SocketIO(app)   # Socket.IO ობიექტის შექმნა

rooms = {}  # კავშირის კოდების სია

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

# მთავარი გვერდი (home page)
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear() #სესიის დაქლეარება
     # POST მეთოდით ფორმის გადაცემა
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        
        # როდესაც სახელი არ არის შეყვანილი დაგვიბრუნოს რეთარნით მესიჯი
        if not name:
            return render_template("home.html", error="გთხოვთ შეიყვანოთ სახელი.", code=code, name=name)

        
        if join != False and not code:
            return render_template("home.html", error="გთხოვთ შეიყვანოთ ჩათის.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4) # გენერირებული უნიკალური კოდი
            rooms[room] = {"members": 0, "messages": []}
             # თუ კოდი არ ემთხვევა
        elif code not in rooms: 
            return render_template("home.html", error="ჩათი არ არსებობს.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room")) # room ფუნქციის გამოძახება
   

    return render_template("home.html")     # home.html შაბლონის ჩატვირთვა

# ჩათს გვერდი (room page)
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])


#მესიჯის გაგზავნა 
@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

# კავშირის მიღება
@socketio.on("connect")
def connect(auth):
    room = session.get("room") #მიმდინარე კოდის დაფისქსირება
    name = session.get("name") #ნინხნარებლის სახელი
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "შემოუერთდა ჩათს"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

# ჩათიდან გამოსვლა 
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")
   
    # აპლიკაციის გაშვება
if __name__ == "__main__":
    socketio.run(app, debug=True)