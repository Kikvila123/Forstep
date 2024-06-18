# სერვერის გაშვება და კონფიგურაცია
from flask import Flask, render_template, request, session, redirect, url_for,Request
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy


 
app = Flask(__name__)
 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123asdASD@localhost/chat_app' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db.init_app(app)
class User(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(80), unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False) 
    def __repr__(self): 
        return f'<User {self.username}>'


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


@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.html'))

# მთავარი გვერდი (home page)
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear() #სესიის დაქლეარება
     # POST მეთოდით ფორმის გადაცემა
    if request.method == "POST":
        username = request.form['username']
        email = request.form["email"]
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
   

    return render_template("register.html")     # register.html შაბლონის ჩატვირთვა

@app.route("/users")
def users():
    cur = mysql.connection.cursor()
    users = cur.execute("SELECT *FROM useres")
    if users > 0:
        userDetails = cur.fetchall()

        return render_template("home.html", userDetails=userDetails)

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