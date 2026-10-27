# Pydantic: kiểm tra dữ liệu gửi lên / trả về
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str


class ExerciseCreate(BaseModel):
    name: str
    muscle_group: Optional[str] = None
    equipment: Optional[str] = None


class ExerciseOut(ExerciseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class RoutineExerciseCreate(BaseModel):
    exercise_id: UUID
    target_sets: int = 3


class RoutineCreate(BaseModel):
    name: str
    exercises: List[RoutineExerciseCreate] = []


class RoutineExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    exercise_id: UUID
    target_sets: int


class RoutineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    exercises: List[RoutineExerciseOut] = []


class SetCreate(BaseModel):
    exercise_id: UUID
    weight: float = 0
    reps: int = 0


class SetUpdate(BaseModel):
    weight: Optional[float] = None
    reps: Optional[int] = None
    is_completed: Optional[bool] = None


class SetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    exercise_id: UUID
    set_number: int
    weight: float
    reps: int
    is_completed: bool


class WorkoutStart(BaseModel):
    routine_id: Optional[UUID] = None


class WorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    total_volume: float
    sets: List[SetOut] = []
