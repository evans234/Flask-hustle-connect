from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os, uuid, threading, time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecret"
UPLOAD_FOLDER = "file_drop"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

chat_rooms = {}
room_passwords = {}
uploaded_files = []

# Auto-delete thread
def delete_file_later(filename, delay=600):
    time.sleep(delay)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form["username"]
        room_id = request.form["room_id"]
        password = request.form.get("password", "")

        if room_id in room_passwords and room_passwords[room_id] != password:
            flash("Wrong password!")
            return redirect(url_for("index"))
        elif room_id not in room_passwords and password:
            room_passwords[room_id] = password

        return redirect(url_for("chat", room_id=room_id, username=username))
    return render_template("index.html")

@app.route("/chat/<room_id>")
def chat(room_id):
    username = request.args.get("username", "anon")
    messages = chat_rooms.get(room_id, [])
    return render_template("room.html", room_id=room_id, messages=messages, username=username)

@app.route("/chat/<room_id>", methods=["POST"])
def send_message(room_id):
    username = request.args.get("username", "anon")
    msg = request.form["message"]
    chat_rooms.setdefault(room_id, []).append((username, msg))
    return redirect(url_for("chat", room_id=room_id, username=username))

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    filename = secure_filename(f.filename)
    unique = str(uuid.uuid4()) + "_" + filename
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique)
    f.save(save_path)
    uploaded_files.append(unique)
    threading.Thread(target=delete_file_later, args=(unique,)).start()
    return f"✅ File uploaded. Share this: /download/{unique}"

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/admin")
def admin_dashboard():
    password = request.args.get("password", "")
    if password != "admin123":
        return "❌ Access Denied", 403

    files = []
    for f in os.listdir(app.config["UPLOAD_FOLDER"]):
        files.append((f, url_for("download_file", filename=f)))

    rooms = list(chat_rooms.keys())
    return render_template("admin.html", files=files, rooms=rooms)

# Optional AI endpoint (requires OpenAI API Key)
@app.route("/ai", methods=["GET", "POST"])
def ai_chat():
    if request.method == "POST":
        question = request.form["question"]
        answer = f"[🤖 AI reply not enabled in this demo]"
        return render_template("ai.html", question=question, answer=answer)
    return render_template("ai.html", question="", answer="")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
