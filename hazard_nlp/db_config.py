# db_config.py
from sqlalchemy import create_engine

# Supabase connection string
DB_URL = "postgresql://postgres:Sih%402025@db.ywmbmspdxxqykxqjyazf.supabase.co:5432/postgres"

# Create SQLAlchemy engine
engine = create_engine(DB_URL, echo=True)  # echo=True prints SQL logs
