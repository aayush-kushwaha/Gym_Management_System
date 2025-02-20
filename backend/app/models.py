from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Member(Base):
    __tablename__ = "members"
    __table_args__ = (
        Index('idx_member_phone', 'phone'),
        Index('idx_member_status', 'membership_status'),
        Index('idx_member_name', 'name'),
        Index('idx_member_member_code', 'member_code'),
    )

    id = Column(Integer, primary_key=True, index=True)
    member_code = Column(String, unique=True, index=True)  # For alphanumeric IDs like TDFC03
    name = Column(String, index=True)
    phone = Column(String, unique=True)
    membership_type = Column(String)  # monthly/quarterly/yearly
    membership_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)  # For soft delete
    attendances = relationship("Attendance", back_populates="member")
    payments = relationship("Payment", back_populates="member")

class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        Index('idx_attendance_member', 'member_id'),
        Index('idx_attendance_date', 'check_in_time'),
    )

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    check_in_time = Column(DateTime(timezone=True), server_default=func.now())
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    member = relationship("Member", back_populates="attendances")

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index('idx_payment_member', 'member_id'),
        Index('idx_payment_date', 'payment_date'),
        Index('idx_payment_reference', 'payment_reference'),
    )

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    amount = Column(Float)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    next_due_date = Column(DateTime(timezone=True))
    payment_reference = Column(String, unique=True, index=True)
    member = relationship("Member", back_populates="payments")

class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = (
        Index('idx_admin_username', 'username'),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
