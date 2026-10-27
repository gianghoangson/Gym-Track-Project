# Kết nối tới PostgreSQL
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()  # đọc file .env

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Mỗi request sẽ mở 1 session, xong thì đóng lại
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
