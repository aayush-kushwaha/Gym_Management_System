from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, database, auth, utils
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

# Public endpoints for member attendance
@app.post("/attendance/mark", response_model=schemas.Attendance)
def mark_member_attendance(member_id: int, phone: str, db: Session = Depends(get_db)):
    # Verify member exists and phone matches
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if member.phone != phone:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not member.membership_status:
        raise HTTPException(status_code=403, detail="Membership is inactive")

    # Check if attendance already marked today using Nepal time
    has_attendance, check_in_time = utils.check_attendance_status(db, member_id)
    if has_attendance:
        raise HTTPException(
            status_code=400,
            detail=f"Attendance already marked at {check_in_time}"
        )

    # Mark new attendance
    db_attendance = models.Attendance(member_id=member_id)
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

@app.get("/members/verify_by_id/{member_id}", response_model=schemas.MemberBasic)
def verify_member_by_id(member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return member

@app.get("/members/verify/{name}", response_model=schemas.MemberBasic)
def verify_member(name: str, phone: str, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(
        models.Member.name == name,
        models.Member.phone == phone
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found or invalid credentials")
    
    return member

@app.post("/attendance/", response_model=schemas.Attendance)
def mark_attendance(member_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    db_attendance = models.Attendance(member_id=member_id)
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

@app.get("/attendance/{member_id}", response_model=List[schemas.Attendance])
def get_member_attendance(member_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    return db.query(models.Attendance).filter(models.Attendance.member_id == member_id).order_by(models.Attendance.check_in_time.desc()).all()

@app.get("/attendance/today", response_model=List[schemas.Attendance])
def get_today_attendance(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    print("Processing today's attendance request...")
    today = datetime.now().date()
    attendances = db.query(models.Attendance).options(db.joinedload(models.Attendance.member)).filter(
        func.date(models.Attendance.check_in_time) == today
    ).order_by(models.Attendance.check_in_time.desc()).all()
    print(f"Found {len(attendances)} attendance records for today")
    for attendance in attendances:
        print(f"Attendance record: ID={attendance.id}, Member ID={attendance.member_id}, Check-in={attendance.check_in_time}")
    return attendances

@app.get("/attendance/recent", response_model=List[schemas.Attendance])
def get_recent_attendance(db: Session = Depends(get_db)):
    return db.query(models.Attendance).options(db.joinedload(models.Attendance.member)).order_by(models.Attendance.check_in_time.desc()).limit(5).all()

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