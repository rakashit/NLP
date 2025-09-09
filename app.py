from flask import Flask, render_template
from sqlalchemy import create_engine, text

# DB Connection (Supabase Postgres)
DATABASE_URL = "postgresql://postgres:Sih%402025@db.ywmbmspdxxqykxqjyazf.supabase.co:5432/postgres"
engine = create_engine(DATABASE_URL)

app = Flask(__name__)

# ---------------- CITIZEN ----------------
@app.route("/citizen/dashboard")
def citizen_dashboard():
    return render_template("citizen_dashboard.html")

@app.route("/citizen/my-reports")
def my_reports():
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT * FROM hazard_reports WHERE user_id=1")  # demo user
        ).fetchall()
    return render_template("posts.html", rows=rows)

@app.route("/citizen/hotspots")
def citizen_hotspots():
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT city, state, COUNT(*) as total_reports,
                   SUM(CASE WHEN account_type='Ministry' THEN 1 ELSE 0 END) as ministry,
                   SUM(CASE WHEN account_type='News' THEN 1 ELSE 0 END) as news,
                   SUM(CASE WHEN account_type='NGO' THEN 1 ELSE 0 END) as ngo,
                   SUM(CASE WHEN account_type='Local Verified Page' THEN 1 ELSE 0 END) as local_verified,
                   SUM(CASE WHEN account_type='Influencer' THEN 1 ELSE 0 END) as influencers,
                   SUM(CASE WHEN account_type='Citizen' THEN 1 ELSE 0 END) as citizens
            FROM social_media_posts
            GROUP BY city, state
        """)).fetchall()

    alerts = []
    for row in rows:
        if (row.ministry >= 1 or row.news >= 1 or row.ngo >= 1 or
            row.local_verified >= 1 or row.influencers >= 5 or row.citizens >= 10):
            alerts.append(f"⚠️ ALERT in {row.city}, {row.state} — Possible Hazard Hotspot")

    if not alerts:
        alerts.append("✅ No current hotspots detected")

    return render_template("citizen_hotspots.html", alerts=alerts)

# ---------------- OFFICIAL ----------------
@app.route("/official/dashboard")
def official_dashboard():
    return render_template("official_dashboard.html")

@app.route("/official/reports")
def all_reports():
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT * FROM hazard_reports ORDER BY submission_time DESC LIMIT 20")
        ).fetchall()
    return render_template("posts.html", rows=rows)

@app.route("/hotspots")
def all_hotspots():
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT city, state, COUNT(*) as total_reports,
                   SUM(CASE WHEN account_type='Ministry' THEN 1 ELSE 0 END) as ministry,
                   SUM(CASE WHEN account_type='News' THEN 1 ELSE 0 END) as news,
                   SUM(CASE WHEN account_type='NGO' THEN 1 ELSE 0 END) as ngo,
                   SUM(CASE WHEN account_type='Local Verified Page' THEN 1 ELSE 0 END) as local_verified,
                   SUM(CASE WHEN account_type='Influencer' THEN 1 ELSE 0 END) as influencers,
                   SUM(CASE WHEN account_type='Citizen' THEN 1 ELSE 0 END) as citizens
            FROM social_media_posts
            GROUP BY city, state
        """)).fetchall()

    return render_template("posts.html", rows=rows)

# ---------------- ANALYST ----------------
@app.route("/analyst/dashboard")
def analyst_dashboard():
    return render_template("analyst_dashboard.html")

@app.route("/analyst/nlp-trends")
def nlp_trends():
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT detected_keywords, COUNT(*) as freq FROM social_media_posts GROUP BY detected_keywords ORDER BY freq DESC LIMIT 10")
        ).fetchall()
    return render_template("posts.html", rows=rows)

if __name__ == "__main__":
    app.run(debug=True)
    
