from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timezone

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    id: str = Field(alias="_id")
    first_name: str
    last_name: str
    email: EmailStr
    hashed_password: str
    completed_courses: List[str] = []
    preferences: dict = {"target_credits": 16}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    completed_courses: List[str]
    preferences: dict

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class CourseQuery(BaseModel):
    query: str
    major: str
    minor: Optional[str] = None
    academic_year: str
    graduation: str
    target_credits: int

class RecommendRequest(BaseModel):
    query: str
    k: int = 5
    subject: Optional[str] = None

class RecommendedCourse(BaseModel):
    course_code: str
    subject_prefix: str
    title: str
    description: str
    score: float

class RecommendResponse(BaseModel):
    results: List[RecommendedCourse]

class ScheduleRequest(BaseModel):
    course_codes: List[str]

class TimeSlot(BaseModel):
    days: List[str]
    startHour: float
    duration: float
    room: str

class ScheduledCourse(BaseModel):
    code: str
    section: str
    title: str
    description: str
    timeSlot: TimeSlot
    credits: int

class ScheduleResponse(BaseModel):
    courses: List[ScheduledCourse]
