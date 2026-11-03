from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Exercise, RoutineExercise, WorkoutSet
from ..access import lock_user
from ..schemas import ExerciseCreate, ExerciseOut
from ..auth.auth import get_current_user

router = APIRouter(prefix="/exercises", tags=["exercises"])


# Lấy bài tập mặc định + bài tập của mình
@router.get("", response_model=List[ExerciseOut])
def get_exercises(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Exercise).filter(or_(Exercise.user_id == None, Exercise.user_id == user.id)).order_by(Exercise.name).all()


@router.post("", response_model=ExerciseOut)
def create_exercise(data: ExerciseCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    lock_user(db, user)
    check_duplicate(db, data.name, user)
    exercise = Exercise(name=data.name, muscle_group=data.muscle_group, equipment=data.equipment, user_id=user.id)
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def check_duplicate(db, name, user, exclude=None):
    query = db.query(Exercise).filter(
        or_(Exercise.user_id.is_(None), Exercise.user_id == user.id),
        func.lower(func.trim(Exercise.name)) == name.lower(),
    )
    if exclude is not None:
        query = query.filter(Exercise.id != exclude)
    if query.first():
        raise HTTPException(409, "Tên bài tập đã tồn tại trong danh sách của bạn")


def owned_exercise(db, exercise_id, user):
    exercise = db.query(Exercise).filter(
        Exercise.id == exercise_id, Exercise.user_id == user.id,
    ).with_for_update().first()
    if exercise is None:
        raise HTTPException(404, "Chỉ được sửa hoặc xoá bài tập riêng của bạn")
    return exercise


@router.put("/{exercise_id}", response_model=ExerciseOut)
def update_exercise(exercise_id: UUID, data: ExerciseCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    lock_user(db, user)
    exercise = owned_exercise(db, exercise_id, user)
    check_duplicate(db, data.name, user, exercise_id)
    for field, value in data.model_dump().items():
        setattr(exercise, field, value)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}")
def delete_exercise(exercise_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    exercise = owned_exercise(db, exercise_id, user)
    if (db.query(RoutineExercise).filter_by(exercise_id=exercise_id).first()
            or db.query(WorkoutSet).filter_by(exercise_id=exercise_id).first()):
        raise HTTPException(409, "Không thể xoá bài tập đang được dùng trong routine hoặc buổi tập")
    db.delete(exercise)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bài tập đang được sử dụng; không thể xoá")
    return {"message": "Đã xoá"}
