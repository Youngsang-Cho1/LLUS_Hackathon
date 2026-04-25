from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

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
    preferences: dict = {"target_credits": 16, "max_workload": 4.5}
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
