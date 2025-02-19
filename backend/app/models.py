from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String, unique=True)
    membership_type = Column(String)  # monthly/quarterly/yearly
    membership_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    attendances = relationship("Attendance", back_populates="member")
    payments = relationship("Payment", back_populates="member")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    check_in_time = Column(DateTime(timezone=True), server_default=func.now())
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    member = relationship("Member", back_populates="attendances")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    amount = Column(Float)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    next_due_date = Column(DateTime(timezone=True))
    payment_reference = Column(String, unique=True, index=True)
    member = relationship("Member", back_populates="payments")

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
