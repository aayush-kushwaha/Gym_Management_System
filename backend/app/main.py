from datetime import datetime, timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from dotenv import load_dotenv
import os

from app import models, schemas, database, auth, utils
from .database import engine, Base

# Load environment variables
load_dotenv()

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gym Management System API",
    description="API for managing gym members, attendance, and payments",
    version="1.0.0"
)

# CORS middleware with configuration from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8501").split(","),
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
    # Check if phone number already exists
    if db.query(models.Member).filter(models.Member.phone == member.phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Get the latest member ID to generate member code
    latest_member = db.query(models.Member).order_by(models.Member.id.desc()).first()
    next_id = 1 if not latest_member else latest_member.id + 1
    
    # Create member with generated member code
    member_data = member.dict()
    member_data['member_code'] = f'TDFC{str(next_id).zfill(3)}'  # e.g., TDFC001
    
    db_member = models.Member(**member_data)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@app.get("/members/", response_model=List[schemas.Member])
def get_members(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    return db.query(models.Member).all()

# Public endpoints for member attendance
@app.post("/attendance/mark", response_model=schemas.AttendanceOut)
def mark_member_attendance(member_code: str, phone: str, db: Session = Depends(get_db)):
    print("Processing attendance request...")
    print(f"Member code: {member_code}, Phone: {phone}")
    
    # First verify the member exists and is active
    member = db.query(models.Member).filter(
        models.Member.member_code == member_code,
        models.Member.phone == phone
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if not member.membership_status:
        raise HTTPException(status_code=403, detail="Membership is inactive")
    
    # Check if attendance already marked for today
    today = datetime.now().date()
    existing_attendance = db.query(models.Attendance).filter(
        models.Attendance.member_id == member.id,
        func.date(models.Attendance.check_in_time) == today
    ).first()
    
    if existing_attendance:
        raise HTTPException(status_code=400, detail="Attendance already marked for today")
    
    # Create new attendance record
    attendance = models.Attendance(member_id=member.id)
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return attendance

@app.get("/members/verify_by_id/{member_code}", response_model=schemas.MemberBasic)
def verify_member_by_id(member_code: str, db: Session = Depends(get_db)):
    print(f"Verifying member by ID: {member_code}")
    member = db.query(models.Member).filter(models.Member.member_code == member_code).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@app.get("/members/verify/{name}", response_model=schemas.MemberBasic)
def verify_member(name: str, phone: str, db: Session = Depends(get_db)):
    print(f"Verifying member: {name}, {phone}")
    member = db.query(models.Member).filter(
        models.Member.name == name,
        models.Member.phone == phone
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@app.post("/admin/attendance/{member_id}", response_model=schemas.AttendanceOut)
def mark_attendance(member_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    attendance = models.Attendance(member_id=member_id)
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance

@app.get("/admin/attendance/{member_id}", response_model=List[schemas.AttendanceOut])
def get_member_attendance(member_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    return db.query(models.Attendance).filter(models.Attendance.member_id == member_id).order_by(models.Attendance.check_in_time.desc()).all()

@app.get("/attendance/today", response_model=List[schemas.AttendanceOut])
async def get_today_attendance(db: Session = Depends(get_db)):
    print("Processing today's attendance request...")
    try:
        today = datetime.now().date()
        print(f"Fetching attendance for date: {today}")
        
        attendances = db.query(models.Attendance).join(
            models.Member,
            models.Attendance.member_id == models.Member.id
        ).options(
            db.joinedload(models.Attendance.member)
        ).filter(
            func.date(models.Attendance.check_in_time) == today
        ).order_by(models.Attendance.check_in_time.desc()).all()
        
        print(f"Found {len(attendances)} attendance records")
        for attendance in attendances:
            print(f"Attendance: {attendance.__dict__}")
            print(f"Member: {attendance.member.__dict__ if attendance.member else 'No member'}")
        
        return attendances
    except Exception as e:
        print(f"Error in get_today_attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attendance/recent", response_model=List[schemas.AttendanceOut])
def get_recent_attendance(db: Session = Depends(get_db)):
    return db.query(models.Attendance).order_by(models.Attendance.check_in_time.desc()).limit(10).all()

@app.post("/payments/", response_model=schemas.Payment)
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    # Check if payment reference already exists
    existing_payment = db.query(models.Payment).filter(models.Payment.payment_reference == payment.payment_reference).first()
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment reference already exists")

    # Verify member exists and is active
    member = db.query(models.Member).filter(models.Member.id == payment.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if not member.membership_status:
        raise HTTPException(status_code=403, detail="Member's membership is inactive")

    # Create payment
    db_payment = models.Payment(**payment.dict())
    db.add(db_payment)
    
    # Update member's membership status
    member.membership_status = True
    
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