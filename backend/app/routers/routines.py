from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Routine, RoutineExercise
from ..schemas import RoutineCreate, RoutineOut
from ..auth.auth import get_current_user

router = APIRouter(prefix="/routines", tags=["routines"])


@router.get("", response_model=List[RoutineOut])
def get_routines(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Routine).filter(Routine.user_id == user.id).all()


@router.post("", response_model=RoutineOut)
def create_routine(data: RoutineCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    routine = Routine(name=data.name, user_id=user.id)
    for index, item in enumerate(data.exercises):
        routine.exercises.append(RoutineExercise(exercise_id=item.exercise_id, order_index=index, target_sets=item.target_sets))
    db.add(routine)
    db.commit()
    db.refresh(routine)
    return routine


@router.delete("/{routine_id}")
def delete_routine(routine_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    routine = db.query(Routine).filter(Routine.id == routine_id, Routine.user_id == user.id).first()
    if routine is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy routine")
    db.delete(routine)
    db.commit()
    return {"message": "Đã xoá"}
