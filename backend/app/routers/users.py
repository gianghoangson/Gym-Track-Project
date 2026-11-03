from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserLogin, Token
from ..auth.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(func.lower(func.trim(User.email)) == data.email).first():
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")
    user = User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Email đã được đăng ký")
    return {"message": "Đăng ký thành công"}


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    # Case-insensitive lookup also supports legacy mixed-case email accounts.
    users = db.query(User).filter(func.lower(func.trim(User.email)) == data.email).all()
    user = next((item for item in users if verify_password(data.password, item.password_hash)), None)
    if user is None:
        raise HTTPException(status_code=401, detail="Sai email hoặc mật khẩu")
    return {"access_token": create_token(user.id)}
