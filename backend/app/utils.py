from datetime import datetime
import pytz

def get_nepal_timezone():
    return pytz.timezone('Asia/Kathmandu')

def get_current_nepal_time():
    nepal_tz = get_nepal_timezone()
    return datetime.now(nepal_tz)

def convert_to_nepal_time(dt):
    if dt.tzinfo is None:
        # If the datetime is naive, assume it's in UTC
        dt = pytz.UTC.localize(dt)
    nepal_tz = get_nepal_timezone()
    return dt.astimezone(nepal_tz)

def format_nepal_time(dt):
    nepal_time = convert_to_nepal_time(dt)
    return nepal_time.strftime('%I:%M %p')

def check_attendance_status(db, member_id):
    from .models import Attendance
    from sqlalchemy import func
    
    # Get current Nepal time
    nepal_now = get_current_nepal_time()
    
    # Convert to Nepal timezone for comparison
    today_nepal = nepal_now.date()
    
    # Query existing attendance for today in Nepal time
    existing_attendance = db.query(Attendance).filter(
        Attendance.member_id == member_id,
        func.date(func.timezone('Asia/Kathmandu', Attendance.check_in_time)) == today_nepal
    ).first()
    
    if existing_attendance:
        # Convert existing check-in time to Nepal time
        check_in_nepal_time = format_nepal_time(existing_attendance.check_in_time)
        return True, check_in_nepal_time
    
    return False, None