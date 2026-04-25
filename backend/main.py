from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn
from datetime import datetime, timedelta, timezone
from typing import List
from contextlib import asynccontextmanager
import os

from database import get_db
from models import UserCreate, UserResponse, Token, CourseQuery, RecommendRequest, RecommendResponse
from auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user_email
)
from recommend import CourseRecommender

@asynccontextmanager
async def lifespan(app: FastAPI):
    emb_path = os.getenv("EMBEDDINGS_PATH", "/scraper/embeddings.npy")
    idx_path = os.getenv("COURSE_INDEX_PATH", "/scraper/course_index.json")
    try:
        print(f"[startup] Loading recommender from {emb_path} + {idx_path}…")
        app.state.recommender = CourseRecommender(emb_path, idx_path)
        print(f"[startup] Recommender ready ({app.state.recommender.emb.shape[0]} courses).")
    except Exception as e:
        print(f"[startup] Recommender failed to load: {e}")
    yield

app = FastAPI(
    title="NYU Course Search API",
    description="API for the Ultimate NYU Course Search Web App",
    version="1.0.0",
    lifespan=lifespan
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
        "preferences": {"target_credits": 16},
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

# --- SEMANTIC SEARCH MOCK ---
MOCK_COURSE_CATALOG = [
    {
        "code": "CSCI-UA 480", "section": "-001", "title": "Special Topics: Artificial Intelligence", 
        "description": "Introduction to AI, machine learning, and neural networks using Python. Covers deep learning basics.", 
        "tags": ["ai", "machine learning", "python", "computer science", "artificial intelligence", "tech"],
        "timeSlot": {"days": ["Mon", "Wed"], "startHour": 14, "duration": 1.5, "room": "Rm 101"},
        "credits": 4
    },
    {
        "code": "CSCI-UA 310", "section": "-004", "title": "Basic Algorithms", 
        "description": "Introduction to the study of algorithms. Presents two main themes: designing appropriate data structures and analyzing the efficiency of the algorithms.", 
        "tags": ["algorithm", "data structure", "logic", "programming", "code"],
        "timeSlot": {"days": ["Tue", "Thu"], "startHour": 10, "duration": 1.5, "room": "Rm 301"},
        "credits": 4
    },
    {
        "code": "MATH-UA 120", "section": "-002", "title": "Discrete Mathematics", 
        "description": "A first course in discrete mathematics. Sets, logic, relations, functions, combinations.", 
        "tags": ["math", "logic", "discrete", "numbers", "proofs"],
        "timeSlot": {"days": ["Mon", "Wed"], "startHour": 15.5, "duration": 1.5, "room": "Rm 204"},
        "credits": 4
    },
    {
        "code": "DS-UA 111", "section": "-005", "title": "Data Science for Everyone", 
        "description": "Introduction to data science, python programming, data visualization, and statistical modeling.", 
        "tags": ["data", "python", "statistics", "visualization", "analytics", "science"],
        "timeSlot": {"days": ["Tue", "Thu"], "startHour": 14, "duration": 1.5, "room": "Aud A"},
        "credits": 4
    },
    {
        "code": "BS-UA 101", "section": "-003", "title": "Business and Finance", 
        "description": "Introduction to corporate finance, markets, and business strategy. Learn how companies make money.", 
        "tags": ["business", "finance", "strategy", "money", "markets", "corporate"],
        "timeSlot": {"days": ["Fri"], "startHour": 9, "duration": 3.0, "room": "Aud B"},
        "credits": 4
    },
    {
        "code": "MKTG-UB 1", "section": "-001", "title": "Introduction to Marketing", 
        "description": "Explore consumer behavior, digital marketing, advertising, and brand management strategies.", 
        "tags": ["marketing", "business", "advertising", "digital", "brand", "consumers"],
        "timeSlot": {"days": ["Mon", "Wed"], "startHour": 11, "duration": 1.5, "room": "Tisch Hall 200"},
        "credits": 4
    },
    {
        "code": "PSYCH-UA 1", "section": "-008", "title": "Introduction to Psychology", 
        "description": "An overview of human behavior, cognitive psychology, neuroscience, and mental health.", 
        "tags": ["psychology", "mind", "behavior", "brain", "neuroscience", "health"],
        "timeSlot": {"days": ["Tue", "Thu"], "startHour": 15, "duration": 1.5, "room": "Meyer Hall 121"},
        "credits": 4
    },
    {
        "code": "ECON-UA 1", "section": "-012", "title": "Microeconomics", 
        "description": "Study of individual economic behavior, supply and demand, market structures, and pricing strategies.", 
        "tags": ["economics", "micro", "money", "supply", "demand", "market"],
        "timeSlot": {"days": ["Mon", "Wed"], "startHour": 9.5, "duration": 1.5, "room": "Silver 401"},
        "credits": 4
    },
    {
        "code": "BIOL-UA 11", "section": "-002", "title": "Principles of Biology I", 
        "description": "Introduction to cellular biology, genetics, molecular biology, and evolution.", 
        "tags": ["biology", "science", "genetics", "cells", "evolution", "life"],
        "timeSlot": {"days": ["Tue", "Thu"], "startHour": 8, "duration": 1.5, "room": "Silver 703"},
        "credits": 4
    },
    {
        "code": "ARTH-UA 10", "section": "-005", "title": "History of Western Art I", 
        "description": "Survey of Western art from prehistoric times to the Renaissance. Examines architecture, sculpture, and painting.", 
        "tags": ["art", "history", "culture", "painting", "sculpture", "renaissance"],
        "timeSlot": {"days": ["Fri"], "startHour": 11, "duration": 3.0, "room": "Silver 300"},
        "credits": 4
    },
    {
        "code": "CSCI-UA 201", "section": "-005", "title": "Computer Systems Organization", 
        "description": "Covers internal structure of computers, machine language programming, and system software.", 
        "tags": ["systems", "c", "assembly", "hardware", "software", "organization"],
        "timeSlot": {"days": ["Wed", "Fri"], "startHour": 14, "duration": 1.5, "room": "Aud A"},
        "credits": 4
    },
    {
        "code": "PHIL-UA 1", "section": "-004", "title": "Central Problems in Philosophy", 
        "description": "An introduction to philosophy through the examination of classical and contemporary texts. Topics include free will, knowledge, and ethics.", 
        "tags": ["philosophy", "ethics", "knowledge", "free will", "thinking", "logic"],
        "timeSlot": {"days": ["Tue", "Thu"], "startHour": 16.5, "duration": 1.5, "room": "Silver 410"},
        "credits": 4
    }
]

@app.post("/api/courses/recommend")
async def recommend_courses(
    query: CourseQuery,
    email: str = Depends(get_current_user_email),
    db=Depends(get_db)
):
    """
    Mock endpoint that simulates proxying the request to the Data Team's API.
    """
    # 1. Fetch user's transcript from DB
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    transcript = user.get("completed_courses", [])
    
    # 2. Build the exact payload for the Data Team
    data_api_payload = {
        "query": query.query,
        "major": query.major,
        "minor": query.minor,
        "academic_year": query.academic_year,
        "graduation": query.graduation,
        "target_credits": query.target_credits,
        "transcript": transcript
    }
    print(f"Sending payload to Data API: {data_api_payload}")
    
    # 3. (MOCK) Mocking the Data API's response
    q = query.query.lower()
    results = []
    
    for course in MOCK_COURSE_CATALOG:
        score = 0.0
        for tag in course["tags"]:
            if tag in q:
                score += 0.4
        if course["title"].lower() in q or q in course["title"].lower():
            score += 0.3
        for word in q.split():
            if len(word) > 3 and word in course["description"].lower():
                score += 0.1
                
        import random
        score += random.uniform(0.05, 0.20)
        score = min(score, 0.99)
        
        if score > 0.15:
            results.append({
                "code": course["code"],
                "section": course["section"],
                "title": course["title"],
                "description": course["description"],
                "score": round(score, 2),
                "timeSlot": course["timeSlot"],
                "credits": course["credits"]
            })
            
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results[:3]}

# --- RECOMMENDATION ROUTE (REAL ML) ---
@app.post("/api/recommend", response_model=RecommendResponse)
async def real_recommend_courses(req: RecommendRequest):
    """Top-k semantic course recommendations for a free-text query."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")
    if req.k < 1 or req.k > 50:
        raise HTTPException(status_code=400, detail="k must be in [1, 50]")
        
    if not hasattr(app.state, "recommender"):
        raise HTTPException(status_code=500, detail="Recommender model not loaded")
        
    results = app.state.recommender.recommend(
        query=req.query, k=req.k, subject=req.subject
    )
    return {"results": results}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
