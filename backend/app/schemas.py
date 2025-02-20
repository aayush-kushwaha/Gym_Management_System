from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MemberBase(BaseModel):
    name: str
    phone: str
    membership_type: str
    member_code: str

class MemberCreate(MemberBase):
    pass

class Member(MemberBase):
    id: int
    membership_status: bool
    created_at: datetime

    class Config:
        orm_mode = True

class MemberBasic(BaseModel):
    id: int
    member_code: str
    name: str
    phone: str
    membership_status: bool

    class Config:
        orm_mode = True

class AttendanceBase(BaseModel):
    member_id: int

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceOut(BaseModel):
    id: int
    member_id: int
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    member: Optional[MemberBasic] = None

    class Config:
        orm_mode = True

class PaymentBase(BaseModel):
    member_id: int
    amount: float
    next_due_date: datetime
    payment_reference: str

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    payment_date: datetime

    class Config:
        orm_mode = True

class AdminBase(BaseModel):
    username: str

class AdminCreate(AdminBase):
    password: str

class Admin(AdminBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None