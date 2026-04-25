from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="NYU Course Search API",
    description="API for the Ultimate NYU Course Search Web App",
    version="1.0.0"
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchQuery(BaseModel):
    major: str | None = None
    minor: str | None = None
    academic_year: str | None = None
    expected_graduation_date: str | None = None
    course_seq: str | None = None

@app.get("/")
def read_root():
    return {"message": "Welcome to the NYU Course Search API"}

@app.post("/api/search")
def search_courses(query: SearchQuery):
    # TODO: Implement Albert and RateMyProfessor joining logic here
    # Example mock response
    return {
        "status": "success",
        "query": query,
        "results": [
            {
                "course_name": "Introduction to Computer Science",
                "professor": "John Doe",
                "rating": 4.8,
                "difficulty": 2.5,
                "score": 0.95
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
