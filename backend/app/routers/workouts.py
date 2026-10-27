from datetime import datetime
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Workout, WorkoutSet, Routine, Exercise
from ..schemas import WorkoutStart, WorkoutOut, SetCreate, SetUpdate, SetOut
from ..auth.auth import get_current_user

router = APIRouter(prefix="/workouts", tags=["workouts"])
MAIN_LIFTS = ["Bench Press", "Squat", "Deadlift"]


def find_workout(db, workout_id, user):
    workout = db.query(Workout).filter(Workout.id == workout_id, Workout.user_id == user.id).first()
    if workout is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy buổi tập")
    return workout


# Bắt đầu buổi tập (trống, hoặc theo routine)
@router.post("", response_model=WorkoutOut)
def start_workout(data: WorkoutStart, db: Session = Depends(get_db), user=Depends(get_current_user)):
    workout = Workout(user_id=user.id, name="Workout")
    if data.routine_id:
        routine = db.query(Routine).filter(Routine.id == data.routine_id, Routine.user_id == user.id).first()
        if routine is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy routine")
        workout.name = routine.name
        number = 1
        for item in routine.exercises:
            for i in range(item.target_sets):
                workout.sets.append(WorkoutSet(exercise_id=item.exercise_id, set_number=number))
                number += 1
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


# Lịch sử: các buổi tập đã kết thúc, mới nhất trước
@router.get("", response_model=List[WorkoutOut])
def get_history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Workout).filter(Workout.user_id == user.id, Workout.end_time != None).order_by(Workout.start_time.desc()).all()


# Số liệu cho dashboard (phải đặt TRƯỚC route /{workout_id})
@router.get("/stats/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(get_current_user)):
    workouts = db.query(Workout).filter(Workout.user_id == user.id, Workout.end_time != None).all()

    # số buổi tập mỗi tháng
    per_month = {}
    for w in workouts:
        month = w.start_time.strftime("%Y-%m")
        per_month[month] = per_month.get(month, 0) + 1

    # 1RM ước tính (công thức Epley) cao nhất của 3 bài chính
    best_1rm = {}
    for name in MAIN_LIFTS:
        best_1rm[name] = 0
    for w in workouts:
        for s in w.sets:
            if not s.is_completed or s.reps <= 0:
                continue
            exercise = db.query(Exercise).filter(Exercise.id == s.exercise_id).first()
            if exercise.name in MAIN_LIFTS:
                one_rm = s.weight * (1 + s.reps / 30)
                if one_rm > best_1rm[exercise.name]:
                    best_1rm[exercise.name] = round(one_rm, 1)

    return {"total_workouts": len(workouts), "per_month": per_month, "best_1rm": best_1rm}


@router.get("/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return find_workout(db, workout_id, user)


# Thêm 1 set vào buổi tập
@router.post("/{workout_id}/sets", response_model=SetOut)
def add_set(workout_id: UUID, data: SetCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    workout = find_workout(db, workout_id, user)
    new_set = WorkoutSet(workout_id=workout.id, exercise_id=data.exercise_id, weight=data.weight,
                         reps=data.reps, set_number=len(workout.sets) + 1)
    db.add(new_set)
    db.commit()
    db.refresh(new_set)
    return new_set


# Sửa set (đổi weight/reps hoặc đánh dấu hoàn thành)
@router.put("/sets/{set_id}", response_model=SetOut)
def update_set(set_id: UUID, data: SetUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = db.query(WorkoutSet).filter(WorkoutSet.id == set_id).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy set")
    find_workout(db, s.workout_id, user)  # kiểm tra set này là của user
    if data.weight is not None:
        s.weight = data.weight
    if data.reps is not None:
        s.reps = data.reps
    if data.is_completed is not None:
        s.is_completed = data.is_completed
    db.commit()
    db.refresh(s)
    return s


@router.delete("/sets/{set_id}")
def delete_set(set_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = db.query(WorkoutSet).filter(WorkoutSet.id == set_id).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy set")
    find_workout(db, s.workout_id, user)
    db.delete(s)
    db.commit()
    return {"message": "Đã xoá"}


# Kết thúc buổi tập: ghi giờ kết thúc + tính tổng volume (weight x reps)
@router.post("/{workout_id}/finish", response_model=WorkoutOut)
def finish_workout(workout_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    workout = find_workout(db, workout_id, user)
    workout.end_time = datetime.now()
    total = 0
    for s in workout.sets:
        if s.is_completed:
            total += s.weight * s.reps
    workout.total_volume = total
    db.commit()
    db.refresh(workout)
    return workout


@router.delete("/{workout_id}")
def delete_workout(workout_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db.delete(find_workout(db, workout_id, user))
    db.commit()
    return {"message": "Đã xoá"}
