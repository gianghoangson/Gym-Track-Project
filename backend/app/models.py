# Các bảng trong database
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    muscle_group = Column(String)
    equipment = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # để trống = bài tập mặc định


class Routine(Base):
    __tablename__ = "routines"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, nullable=False)
    exercises = relationship("RoutineExercise", cascade="all, delete", order_by="RoutineExercise.order_index")


class RoutineExercise(Base):
    __tablename__ = "routine_exercises"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    routine_id = Column(UUID(as_uuid=True), ForeignKey("routines.id"))
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id"))
    order_index = Column(Integer, default=0)
    target_sets = Column(Integer, default=3)


class Workout(Base):
    __tablename__ = "workouts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, default="Workout")
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)  # trống = đang tập
    total_volume = Column(Float, default=0)
    sets = relationship("WorkoutSet", cascade="all, delete", order_by="WorkoutSet.set_number")


class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id"))
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id"))
    set_number = Column(Integer, default=1)
    weight = Column(Float, default=0)
    reps = Column(Integer, default=0)
    rpe = Column(Float)
    is_completed = Column(Boolean, default=False)
