from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn
from datetime import datetime, timedelta
from typing import List

from database import get_db
from models import UserCreate, UserResponse, Token
from auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user_email
)

app = FastAPI(
    title="NYU Course Search API",
    description="API for the Ultimate NYU Course Search Web App",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the NYU Course Search API"}

# --- AUTHENTICATION ROUTES ---

@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db=Depends(get_db)):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user document
    hashed_pwd = get_password_hash(user.password)
    user_doc = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "hashed_password": hashed_pwd,
        "completed_courses": [],
        "preferences": {"target_credits": 16, "max_workload": 4.5},
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Return response
    return UserResponse(
        id=str(result.inserted_id),
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        completed_courses=[],
        preferences=user_doc["preferences"]
    )

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/user/me", response_model=UserResponse)
async def read_users_me(email: str = Depends(get_current_user_email), db=Depends(get_db)):
    user = await db.users.find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(user["_id"]),
        first_name=user["first_name"],
        last_name=user["last_name"],
        email=user["email"],
        completed_courses=user.get("completed_courses", []),
        preferences=user.get("preferences", {})
    )

# --- TRANSCRIPT / DATA ROUTES ---

@app.post("/api/user/transcript")
async def upload_transcript(
    file: UploadFile = File(...), 
    email: str = Depends(get_current_user_email),
    db=Depends(get_db)
):
    """
    Dummy endpoint that simulates an AI extraction from a PDF/Image transcript.
    In reality, we would pass 'file' to an OCR/Vision AI tool.
    For now, it updates the user's completed courses with mock data.
    """
    # Mock AI Extraction
    extracted_courses = ["CSCI-UA 101", "CSCI-UA 201", "MATH-UA 120", "CORE-UA 101"]
    
    # Update DB
    await db.users.update_one(
        {"email": email},
        {"$addToSet": {"completed_courses": {"$each": extracted_courses}}}
    )
    
    return {
        "status": "success", 
        "message": f"Successfully extracted and saved {len(extracted_courses)} courses from {file.filename}.",
        "added_courses": extracted_courses
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
