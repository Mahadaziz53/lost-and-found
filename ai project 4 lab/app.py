"""
AI Lost & Found Intelligence System
====================================
Production-ready Flask web application with AI-powered matching engine.
Includes Authentication, Role-based Access Control, and a beautiful UI.
"""

import os
import re
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

from database import init_db, get_db_connection
from matching import MatchingEngine

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# ── App Configuration ──────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ai-lost-found-secret-2024")

UPLOAD_FOLDER      = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

matcher = MatchingEngine()
bcrypt = Bcrypt(app)

# ── Authentication Setup ───────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "danger"

class User(UserMixin):
    def __init__(self, id, name, email, role, password_hash):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user["id"], user["name"], user["email"], user["role"], user["password_hash"])
    return None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("You do not have permission to access that page.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ── Custom Jinja2 Filters ──────────────────────────────────────────────────
@app.template_filter('is_phone')
def is_phone(value) -> bool:
    if not value: return False
    cleaned = re.sub(r'[\s\-\.\(\)\+]', '', str(value))
    return cleaned.isdigit() and len(cleaned) >= 7

@app.template_filter('is_email')
def is_email(value) -> bool:
    return bool(value and '@' in str(value))

@app.template_filter('clean_phone')
def clean_phone(value) -> str:
    return re.sub(r'[\s\-\.\(\)]', '', str(value or ''))

@app.template_filter('wa_number')
def wa_number(value) -> str:
    return re.sub(r'[^\d]', '', str(value or ''))

# ── Helpers ────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_image(file) -> str | None:
    if file and file.filename and allowed_file(file.filename):
        ext         = secure_filename(file.filename).rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        save_path   = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(save_path)
        return os.path.join("uploads", unique_name).replace("\\", "/")
    return None

# ── Authentication Routes ──────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        # Validation
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")
            
        if not re.match(r"[^@]+@gmail\.com$", email):
            flash("Email must be a valid @gmail.com address.", "danger")
            return render_template("register.html", name=name, email=email)
            
        if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
            flash("Password must be at least 8 characters long and include both letters and numbers.", "danger")
            return render_template("register.html", name=name, email=email)
            
        conn = get_db_connection()
        existing_user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            conn.close()
            flash("Email already registered.", "danger")
            return render_template("register.html", name=name)
            
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                     (name, email, hashed_pw, "user"))
        conn.commit()
        conn.close()
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
        
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = "remember" in request.form
        
        conn = get_db_connection()
        user_data = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user_data and bcrypt.check_password_hash(user_data["password_hash"], password):
            user = User(user_data["id"], user_data["name"], user_data["email"], user_data["role"], user_data["password_hash"])
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash("Login successful!", "success")
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash("Invalid email or password.", "danger")
            
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# ── Landing Page & Dashboard ─────────────────────────────────────────────
@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template("landing.html")

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    conn = get_db_connection()
    lost_count = conn.execute("SELECT COUNT(*) FROM lost_items").fetchone()[0]
    found_count = conn.execute("SELECT COUNT(*) FROM found_items").fetchone()[0]
    recent_lost = conn.execute("SELECT * FROM lost_items ORDER BY timestamp DESC LIMIT 4").fetchall()
    recent_found = conn.execute("SELECT * FROM found_items ORDER BY timestamp DESC LIMIT 4").fetchall()
    conn.close()
    return render_template("index.html",
                           lost_count=lost_count, found_count=found_count,
                           recent_lost=recent_lost, recent_found=recent_found)

# ── Admin Panel ────────────────────────────────────────────────────────────
@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    lost_count = conn.execute("SELECT COUNT(*) FROM lost_items").fetchone()[0]
    found_count = conn.execute("SELECT COUNT(*) FROM found_items").fetchone()[0]
    
    users = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 5").fetchall()
    lost_items = conn.execute("SELECT * FROM lost_items ORDER BY timestamp DESC LIMIT 5").fetchall()
    found_items = conn.execute("SELECT * FROM found_items ORDER BY timestamp DESC LIMIT 5").fetchall()
    conn.close()
    
    return render_template("admin/dashboard.html",
                           users_count=users_count, lost_count=lost_count, found_count=found_count,
                           users=users, lost_items=lost_items, found_items=found_items)

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete_item/<item_type>/<int:item_id>", methods=["POST"])
@admin_required
def delete_item(item_type, item_id):
    table = "lost_items" if item_type == "lost" else "found_items"
    conn = get_db_connection()
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash(f"{item_type.capitalize()} item deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

# ── Lost Items ─────────────────────────────────────────────────────────────
@app.route("/lost")
@login_required
def lost_items():
    conn  = get_db_connection()
    items = conn.execute("SELECT * FROM lost_items ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("lost_items.html", items=items)

@app.route("/report-lost", methods=["GET", "POST"])
@login_required
def report_lost():
    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location    = request.form.get("location", "").strip()
        contact     = request.form.get("contact", "").strip()

        if not title or not description or not location:
            flash("Please fill in all required fields.", "danger")
            return render_template("report_lost.html")

        image_path = save_uploaded_image(request.files.get("image"))

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO lost_items (user_id, title,description,location,image_path,contact,timestamp) VALUES (?,?,?,?,?,?,?)",
            (current_user.id, title, description, location, image_path, contact,
             datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        item_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        flash("Lost item reported successfully! Our AI is searching for matches…", "success")
        return redirect(url_for("view_matches", item_id=item_id, item_type="lost"))

    return render_template("report_lost.html")


# ── Found Items ────────────────────────────────────────────────────────────
@app.route("/found")
@login_required
def found_items():
    conn  = get_db_connection()
    items = conn.execute("SELECT * FROM found_items ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("found_items.html", items=items)

@app.route("/report-found", methods=["GET", "POST"])
@login_required
def report_found():
    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location    = request.form.get("location", "").strip()
        contact     = request.form.get("contact", "").strip()

        if not title or not description or not location:
            flash("Please fill in all required fields.", "danger")
            return render_template("report_found.html")

        image_path = save_uploaded_image(request.files.get("image"))

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO found_items (user_id, title,description,location,image_path,contact,timestamp) VALUES (?,?,?,?,?,?,?)",
            (current_user.id, title, description, location, image_path, contact,
             datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        item_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        flash("Found item reported successfully! Our AI is searching for matches…", "success")
        return redirect(url_for("view_matches", item_id=item_id, item_type="found"))

    return render_template("report_found.html")


# ── AI Matching ────────────────────────────────────────────────────────────
@app.route("/matches")
@login_required
def matches_overview():
    conn            = get_db_connection()
    # Limit to user's items for general users
    if current_user.role == 'admin':
        lost_items_all = conn.execute("SELECT * FROM lost_items").fetchall()
    else:
        lost_items_all = conn.execute("SELECT * FROM lost_items WHERE user_id = ?", (current_user.id,)).fetchall()
        
    found_items_all = conn.execute("SELECT * FROM found_items").fetchall()
    conn.close()

    all_matches = []
    for lost in lost_items_all:
        results = matcher.find_matches(dict(lost), [dict(f) for f in found_items_all])
        for m in results[:2]:
            all_matches.append({"lost": dict(lost), "match": m})

    all_matches.sort(key=lambda x: x["match"]["score"], reverse=True)
    return render_template("matches.html", all_matches=all_matches[:20])

@app.route("/matches/<item_type>/<int:item_id>")
@login_required
def view_matches(item_type, item_id):
    conn = get_db_connection()
    if item_type == "lost":
        source     = conn.execute("SELECT * FROM lost_items  WHERE id=?", (item_id,)).fetchone()
        candidates = conn.execute("SELECT * FROM found_items").fetchall()
    else:
        source     = conn.execute("SELECT * FROM found_items WHERE id=?", (item_id,)).fetchone()
        candidates = conn.execute("SELECT * FROM lost_items").fetchall()
    conn.close()

    if not source:
        flash("Item not found.", "danger")
        return redirect(url_for("index"))

    # Security check - ensure user owns the item or is admin
    if current_user.role != 'admin' and source["user_id"] != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("index"))

    matches = matcher.find_matches(dict(source), [dict(c) for c in candidates])
    return render_template("match_results.html",
                           source=dict(source), matches=matches, item_type=item_type)

# ── Search ─────────────────────────────────────────────────────────────────
@app.route("/search")
@login_required
def search():
    query         = request.args.get("q", "").strip()
    results_lost  = []
    results_found = []
    if query:
        like = f"%{query}%"
        conn = get_db_connection()
        results_lost  = conn.execute(
            "SELECT * FROM lost_items  WHERE title LIKE ? OR description LIKE ? OR location LIKE ?",
            (like, like, like)).fetchall()
        results_found = conn.execute(
            "SELECT * FROM found_items WHERE title LIKE ? OR description LIKE ? OR location LIKE ?",
            (like, like, like)).fetchall()
        conn.close()
    return render_template("search.html", query=query,
                           results_lost=results_lost, results_found=results_found)


# ── Error Handlers ─────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(413)
def file_too_large(e):
    flash("Uploaded file is too large. Maximum size is 16 MB.", "danger")
    return redirect(request.referrer or url_for("index"))

@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500

# ── Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
