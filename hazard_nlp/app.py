from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from sqlalchemy import create_engine, text
from functools import wraps

# Priority rules for hotspot detection
PRIORITY_RULES = {
    "Ministry": 1,
    "News": 1,
    "NGO": 1,
    "Local Verified Page": 1,
    "Influencer": 5,
    "Citizen": 10
}

# DB Connection (Supabase Postgres)
DATABASE_URL = "postgresql://postgres:Sih%402025@db.ywmbmspdxxqykxqjyazf.supabase.co:5432/postgres"
engine = create_engine(DATABASE_URL)

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change for production!

# ---------------- Role Decorator ----------------
def role_required(allowed_roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "role" not in session or session["role"] not in allowed_roles:
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated
    return wrapper

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT user_id, role FROM users WHERE username=:u AND password_hash=:p"),
                {"u": username, "p": password}  # NOTE: use password hashing in production!
            ).fetchone()

        if result:
            session["user_id"] = result.user_id
            session["role"] = result.role

            if result.role == "Citizen":
                return redirect(url_for("citizen_dashboard"))
            elif result.role == "Official":
                return redirect(url_for("official_dashboard"))
            elif result.role == "Analyst":
                return redirect(url_for("analyst_dashboard"))

        return "Invalid credentials!"

    return render_template("login.html")

# ---------------- CITIZEN ----------------
@app.route("/citizen/dashboard")
@role_required(["Citizen"])
def citizen_dashboard():
    return render_template("citizen_dashboard.html")

@app.route("/citizen/my-reports")
@role_required(["Citizen"])
def my_reports():
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT * FROM hazard_reports WHERE user_id=:uid"),
            {"uid": session["user_id"]}
        ).fetchall()
    return render_template("posts.html", rows=rows)

@app.route("/citizen/hotspots")
@role_required(["Citizen"])
def citizen_hotspots():
    """Simplified hotspot view for Citizens"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT account_type, COUNT(*) as total
            FROM social_media_posts
            GROUP BY account_type
        """))

        alerts_triggered = False
        for row in result:
            account_type = row.account_type
            total = row.total
            threshold = PRIORITY_RULES.get(account_type, None)
            if threshold and total >= threshold:
                alerts_triggered = True
                break

    return render_template("citizen_hotspots.html", alert=alerts_triggered)

# ---------------- OFFICIAL ----------------
@app.route("/official/dashboard")
@role_required(["Official"])
def official_dashboard():
    return render_template("official_dashboard.html")

@app.route("/official/reports")
@role_required(["Official"])
def all_reports():
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT * FROM hazard_reports ORDER BY submission_time DESC LIMIT 20")
        ).fetchall()
    return render_template("posts.html", rows=rows)

# ---------------- ANALYST ----------------
@app.route("/analyst/dashboard")
@role_required(["Analyst"])
def analyst_dashboard():
    return render_template("analyst_dashboard.html")

@app.route("/analyst/nlp-trends")
@role_required(["Analyst"])
def nlp_trends():
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT detected_keywords, COUNT(*) as freq FROM social_media_posts GROUP BY detected_keywords ORDER BY freq DESC LIMIT 10")
        ).fetchall()
    return render_template("posts.html", rows=rows)

# ---------------- HOTSPOTS FEATURE ----------------
@app.route("/hotspots/json")
@role_required(["Official", "Analyst"])
def hotspot_json():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT account_type, COUNT(*) as total
            FROM social_media_posts
            GROUP BY account_type
        """))

        hotspots = []
        for row in result:
            account_type = row.account_type
            total = row.total
            threshold = PRIORITY_RULES.get(account_type, None)
            status = "NO HOTSPOT"
            if threshold and total >= threshold:
                status = "HOTSPOT TRIGGERED"

            hotspots.append({
                "account_type": account_type,
                "total_posts": total,
                "threshold": threshold,
                "status": status
            })

    return jsonify(hotspots)

@app.route("/hotspots")
@role_required(["Official", "Analyst"])
def hotspot_dashboard():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT account_type, COUNT(*) as total
            FROM social_media_posts
            GROUP BY account_type
        """))

        hotspots = []
        for row in result:
            account_type = row.account_type
            total = row.total
            threshold = PRIORITY_RULES.get(account_type, None)
            status = "NO HOTSPOT"
            if threshold and total >= threshold:
                status = "HOTSPOT TRIGGERED"

            hotspots.append({
                "account_type": account_type,
                "total_posts": total,
                "threshold": threshold,
                "status": status
            })

    return render_template("hotspots.html", hotspots=hotspots)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

