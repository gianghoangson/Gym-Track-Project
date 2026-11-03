from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import Base, engine, SessionLocal
from .models import Exercise
from .routers import users, exercises, routines, workouts

# Tạo bảng nếu chưa có (đơn giản, không cần Alembic để bắt đầu)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gym Tracker")

# Cho phép frontend (chạy ở cổng khác) gọi API
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(users.router)
app.include_router(exercises.router)
app.include_router(routines.router)
app.include_router(workouts.router)

# Bài tập mặc định: (tên, nhóm cơ, dụng cụ)
DEFAULT_EXERCISES = [
    ("Bench Press", "Chest", "Barbell"),
    ("Squat", "Legs", "Barbell"),
    ("Deadlift", "Back", "Barbell"),
    ("Overhead Press", "Shoulders", "Barbell"),
    ("Barbell Row", "Back", "Barbell"),
    ("Pull Up", "Back", "Bodyweight"),
    ("Bicep Curl", "Arms", "Dumbbell"),
    ("Tricep Pushdown", "Arms", "Cable"),
    ("Leg Press", "Legs", "Machine"),
    ("Plank", "Core", "Bodyweight"),
]

def seed_default_exercises():
    with SessionLocal() as db:
        # Serialise seeding across PostgreSQL workers without a schema change.
        if db.bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(7340921)"))
        names = {e.name.strip().lower() for e in db.query(Exercise).filter(Exercise.user_id.is_(None))}
        for name, muscle, equipment in DEFAULT_EXERCISES:
            if name.lower() not in names:
                db.add(Exercise(name=name, muscle_group=muscle, equipment=equipment))
                names.add(name.lower())
        db.commit()


seed_default_exercises()
