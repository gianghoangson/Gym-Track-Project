"""Shared access checks; locks protect writes without schema changes."""
from fastapi import HTTPException
from sqlalchemy import or_
from .models import Exercise, User


def lock_user(db, user):
    db.query(User).filter(User.id == user.id).with_for_update().first()


def accessible_exercise(db, exercise_id, user):
    exercise = db.query(Exercise).filter(
        Exercise.id == exercise_id,
        or_(Exercise.user_id.is_(None), Exercise.user_id == user.id),
    ).with_for_update().first()
    if exercise is None:
        raise HTTPException(404, "Bài tập không tồn tại hoặc bạn không có quyền sử dụng")
    return exercise


def validate_routine_exercises(db, items, user):
    # A consistent lock order avoids deadlocks between routine updates.
    for exercise_id in sorted({item.exercise_id for item in items}, key=str):
        accessible_exercise(db, exercise_id, user)
