from db_config import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT post_id, content, detected_keywords FROM social_media_posts ORDER BY post_id DESC LIMIT 5"))
    for row in result:
        print(row)
