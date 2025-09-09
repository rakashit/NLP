import pandas as pd
from rake_nltk import Rake
import nltk
from sqlalchemy import create_engine, text
from collections import defaultdict

# Download necessary NLTK resources
nltk.download("stopwords")
nltk.download("punkt")
nltk.download("punkt_tab")

# -------------------------------
# Database Connection
# -------------------------------
DATABASE_URL = "postgresql://postgres:Sih%402025@db.ywmbmspdxxqykxqjyazf.supabase.co:5432/postgres"
engine = create_engine(DATABASE_URL)

# -------------------------------
# Priority Rules
# -------------------------------
PRIORITY_RULES = {
    "Ministry": 1,
    "News": 1,
    "NGO": 1,
    "Local Verified Page": 1,
    "Influencer": 5,
    "Citizen": 10
}

# -------------------------------
# Ensure Hotspots Table Exists
# -------------------------------
with engine.begin() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS hotspots (
        hotspot_id SERIAL PRIMARY KEY,
        keyword VARCHAR(255),
        event_type VARCHAR(50),
        trigger_source VARCHAR(50),
        post_count INT,
        detected_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """))

# -------------------------------
# Processing Function
# -------------------------------
def process_social_media_posts(csv_path):
    df = pd.read_csv(csv_path)

    r = Rake()
    hotspots = []
    counter = defaultdict(lambda: defaultdict(int))  # {keyword: {account_type: count}}

    with engine.begin() as conn:
        for _, row in df.iterrows():
            content = str(row["text"])
            account_type = str(row.get("account_type", "Citizen"))  # default fallback
            event_type = str(row.get("event_type", "Other"))

            # Extract keywords
            r.extract_keywords_from_text(content)
            keywords = r.get_ranked_phrases()
            keywords_text = ", ".join(keywords) if keywords else "None"

            # Insert into DB
            conn.execute(text("""
                INSERT INTO social_media_posts
                (platform, original_post_id, author_handle, account_type, content, detected_keywords, event_type, source_url)
                VALUES (:platform, :original_post_id, :author_handle, :account_type, :content, :detected_keywords, :event_type, :source_url)
            """), {
                "platform": row.get("platform", "Twitter"),
                "original_post_id": row.get("id", None),
                "author_handle": row.get("author", None),
                "account_type": account_type,
                "content": content,
                "detected_keywords": keywords_text,
                "event_type": event_type,
                "source_url": row.get("url", None),
            })

            # -------------------------------
            # Hotspot Logic
            # -------------------------------
            threshold = PRIORITY_RULES.get(account_type, None)

            # Case 1: Immediate trigger (Ministry/News/NGO/Verified Page)
            if threshold == 1:
                conn.execute(text("""
                    INSERT INTO hotspots (keyword, event_type, trigger_source, post_count)
                    VALUES (:keyword, :event_type, :trigger_source, :post_count)
                """), {
                    "keyword": keywords_text,
                    "event_type": event_type,
                    "trigger_source": account_type,
                    "post_count": 1
                })
                hotspots.append(f"🔥 HOTSPOT TRIGGERED by {account_type}: {keywords_text}")

            # Case 2: Aggregated trigger (Influencers ≥5, Citizens ≥10)
            elif threshold and keywords:
                for kw in keywords:
                    counter[kw][account_type] += 1
                    if counter[kw][account_type] >= threshold:
                        conn.execute(text("""
                            INSERT INTO hotspots (keyword, event_type, trigger_source, post_count)
                            VALUES (:keyword, :event_type, :trigger_source, :post_count)
                        """), {
                            "keyword": kw,
                            "event_type": event_type,
                            "trigger_source": account_type,
                            "post_count": counter[kw][account_type]
                        })
                        hotspots.append(f"🔥 HOTSPOT TRIGGERED ({account_type} x{counter[kw][account_type]}): {kw}")
                        counter[kw][account_type] = -9999  # prevent duplicate trigger

    return hotspots

# -------------------------------
# Run the Script
# -------------------------------
if __name__ == "__main__":
    csv_path = "D:/New folder/hazard_nlp/data/train.csv"   # 👈 change if needed
    results = process_social_media_posts(csv_path)

    print("\n🔥 Hotspot Triggers:")
    for r in results:
        print(r)
