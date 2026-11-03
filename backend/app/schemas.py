# Pydantic: kiểm tra dữ liệu gửi lên / trả về
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower()


class UserCreate(UserLogin):
    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Email không hợp lệ")
        return value

    @field_validator("password")
    @classmethod
    def valid_password(cls, value):
        if not value.strip() or len(value) < 6:
            raise ValueError("Mật khẩu mới cần ít nhất 6 ký tự")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Mật khẩu không được vượt quá 72 byte UTF-8")
        return value


class Token(BaseModel):
    access_token: str


class ExerciseCreate(BaseModel):
    name: str
    muscle_group: Optional[str] = None
    equipment: Optional[str] = None

    @field_validator("name")
    @classmethod
    def required_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Tên không được để trống")
        return value

    @field_validator("muscle_group", "equipment")
    @classmethod
    def optional_text(cls, value):
        # These fields are optional in the existing form.
        return value.strip() or None if value is not None else None


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    muscle_group: Optional[str] = None
    equipment: Optional[str] = None
    user_id: Optional[UUID] = None


class RoutineExerciseCreate(BaseModel):
    exercise_id: UUID
    target_sets: int = Field(default=3, gt=0)


class RoutineCreate(BaseModel):
    name: str
    exercises: List[RoutineExerciseCreate] = Field(min_length=1)

    _name = field_validator("name")(ExerciseCreate.required_name.__func__)

    @field_validator("exercises")
    @classmethod
    def unique_exercises(cls, value):
        if len({item.exercise_id for item in value}) != len(value):
            raise ValueError("Mỗi bài tập chỉ được xuất hiện một lần trong routine")
        return value


class RoutineExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    exercise_id: UUID
    target_sets: int
    order_index: int


class RoutineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    exercises: List[RoutineExerciseOut] = Field(default_factory=list)


class SetCreate(BaseModel):
    exercise_id: UUID
    weight: float = Field(default=0, ge=0, allow_inf_nan=False)
    reps: int = Field(default=0, ge=0)


class SetUpdate(BaseModel):
    weight: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    reps: Optional[int] = Field(default=None, ge=0)
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
    sets: List[SetOut] = Field(default_factory=list)
