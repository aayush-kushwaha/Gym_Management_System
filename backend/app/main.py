from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database, auth
from .database import engine
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import func

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = database.get_db()
    try:
        yield next(db)
    finally:
        next(db, None)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get current admin
async def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    admin = db.query(models.Admin).filter(models.Admin.username == token_data.username).first()
    if admin is None:
        raise credentials_exception
    return admin

@app.post("/members/", response_model=schemas.Member)
def create_member(member: schemas.MemberCreate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    db_member = models.Member(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@app.get("/members/", response_model=List[schemas.Member])
def get_members(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    return db.query(models.Member).all()

@app.post("/attendance/", response_model=schemas.Attendance)
def mark_attendance(member_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    db_attendance = models.Attendance(member_id=member_id)
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

@app.get("/attendance/{member_id}", response_model=List[schemas.Attendance])
def get_member_attendance(member_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    return db.query(models.Attendance).filter(models.Attendance.member_id == member_id).all()

@app.get("/attendance/today", response_model=List[schemas.Attendance])
def get_today_attendance(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    today = datetime.now().date()
    return db.query(models.Attendance).filter(
        func.date(models.Attendance.check_in_time) == today
    ).all()

@app.get("/attendance/recent", response_model=List[schemas.Attendance])
def get_recent_attendance(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    return db.query(models.Attendance).order_by(models.Attendance.check_in_time.desc()).limit(5).all()

@app.post("/payments/", response_model=schemas.Payment)
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    db_payment = models.Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@app.post("/admin/register", response_model=schemas.Admin)
def create_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    # Check if admin already exists
    db_admin = db.query(models.Admin).filter(models.Admin.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new admin with hashed password
    hashed_password = auth.get_password_hash(admin.password)
    db_admin = models.Admin(username=admin.username, hashed_password=hashed_password)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

@app.post("/admin/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = auth.authenticate_admin(db, form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": admin.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/admin/me", response_model=schemas.Admin)
async def read_admin_me(current_admin: models.Admin = Depends(get_current_admin)):
    return current_admin