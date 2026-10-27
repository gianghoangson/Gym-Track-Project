from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Exercise
from ..schemas import ExerciseCreate, ExerciseOut
from ..auth.auth import get_current_user

router = APIRouter(prefix="/exercises", tags=["exercises"])


# Lấy bài tập mặc định + bài tập của mình
@router.get("", response_model=List[ExerciseOut])
def get_exercises(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Exercise).filter(or_(Exercise.user_id == None, Exercise.user_id == user.id)).order_by(Exercise.name).all()


@router.post("", response_model=ExerciseOut)
def create_exercise(data: ExerciseCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    exercise = Exercise(name=data.name, muscle_group=data.muscle_group, equipment=data.equipment, user_id=user.id)
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise
