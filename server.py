from flask import Flask, redirect, url_for, render_template, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import sqlite3
import os
import uuid

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = "dev-secret-key"  # production'da env variable olmalı

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# -------------------------------------------------
# DATABASE
# -------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            user_type TEXT CHECK(user_type IN ('customer','kurye')),
            plate TEXT,
            profile_image TEXT
        )
    """)
    db.commit()

init_db()

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("user_type") != role:
                flash("Bu sayfaya erişim yetkiniz yok", "error")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return decorated
    return wrapper

# -------------------------------------------------
# PAGES
# -------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/gonder")
@login_required
@role_required("customer")
def send():
    return render_template("send.html")

@app.route("/takip")
@login_required
def track():
    return render_template("track.html")

@app.route("/kurye-ol")
@login_required
@role_required("customer")
def courier():
    return render_template("courier.html")

# -------------------------------------------------
# AUTH
# -------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if not user or not check_password_hash(user["password"], password):
            flash("Email veya şifre yanlış", "error")
            return redirect(url_for("login"))

        session.update({
            "user_id": user["id"],
            "user_name": user["fullname"],
            "email": user["email"],
            "phone": user["phone"],
            "user_type": user["user_type"],
            "user_plate": user["plate"],
            "profile_image": user["profile_image"]
        })

        return redirect(url_for("profile"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")
        password_repeat = request.form.get("password_repeat")
        phone = request.form.get("phone")
        user_type = request.form.get("user_type")
        plate = request.form.get("plate") if user_type == "kurye" else None

        if password != password_repeat:
            flash("Şifreler eşleşmiyor", "error")
            return redirect(url_for("register"))

        db = get_db()
        if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            flash("Bu email zaten kayıtlı", "error")
            return redirect(url_for("register"))

        profile_image = os.path.join(UPLOAD_FOLDER, "default.jpg")
        file = request.files.get("profile_image")

        if file and file.filename and allowed_file(file.filename):
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            profile_image = path

        db.execute("""
            INSERT INTO users (fullname, email, password, phone, user_type, plate, profile_image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fullname,
            email,
            generate_password_hash(password),
            phone,
            user_type,
            plate,
            profile_image
        ))
        db.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

# -------------------------------------------------
# PROFILE
# -------------------------------------------------
@app.route("/profile")
@login_required
def profile():
    user = {
        "name": session.get("user_name"),
        "email": session.get("email"),
        "phone": session.get("phone"),
        "image": session.get("profile_image"),
        "plate": session.get("user_plate")
    }

    user_type = session.get("user_type")

    past_orders = [
        {"id": 1, "date": "2025-11-15", "status": "Teslim Edilecek"},
        {"id": 2, "date": "2025-12-01", "status": "Teslim Edilecek"}
    ]

    if user_type == "kurye":
        for o in past_orders:
            o["status"] = "Teslimatlar"

    return render_template(
        "profile.html",
        user=user,
        past_orders=past_orders,
        user_type=user_type
    )

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        phone = request.form.get("phone")

        session["user_name"] = fullname
        session["email"] = email
        session["phone"] = phone

        db = get_db()
        db.execute("""
            UPDATE users SET fullname = ?, email = ?, phone = ?
            WHERE id = ?
        """, (fullname, email, phone, session["user_id"]))

        file = request.files.get("profile_image")
        if file and file.filename and allowed_file(file.filename):
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)

            session["profile_image"] = path
            db.execute(
                "UPDATE users SET profile_image = ? WHERE id = ?",
                (path, session["user_id"])
            )

        db.commit()
        return redirect(url_for("profile"))

    return render_template("edit_profile.html")

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
