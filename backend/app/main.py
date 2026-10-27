from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Thêm bài tập mặc định nếu database còn trống
db = SessionLocal()
if db.query(Exercise).filter(Exercise.user_id == None).count() == 0:
    for name, muscle, equipment in DEFAULT_EXERCISES:
        db.add(Exercise(name=name, muscle_group=muscle, equipment=equipment))
    db.commit()
db.close()
