# Ultimate NYU Course Search Web App

An advanced course search web application built for NYU students, designed to find the best courses by integrating data from **NYU Albert** and **RateMyProfessor**.

## Features

- **Personalized Search:** Filter by Major/Minor status, Current academic year, Expected Graduation Date, and Course Sequence.
- **Smart Retrieval:** Merges NYU Albert course data with RateMyProfessor ratings (utilizing Fuzzy String Matching for professor names).
- **Top K Recommendations:** Recommends the best courses based on a weighted algorithm (combining professor rating, difficulty, and other metrics).

## Tech Stack

- **Frontend:** Next.js (App Router, TypeScript, TailwindCSS)
- **Backend:** FastAPI (Python, Uvicorn, RapidFuzz for string matching)
- **Database:** MongoDB (Motor for async operations)
- **Infrastructure:** Docker & Docker Compose

## Repository Structure

```
LLUS_Hackathon/
├── frontend/           # Next.js Application
├── backend/            # FastAPI Application
├── docker-compose.yml  # Orchestration for local development
└── README.md           # Project Documentation
```

## Setup & Running Locally

This project uses Docker Compose to easily orchestrate the frontend, backend, and database.

### Prerequisites
- Docker & Docker Compose installed on your machine.

### Running the App

1. Clone the repository and navigate to the root directory.
2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
3. Access the services:
   - **Frontend (Next.js):** http://localhost:3000
   - **Backend API (FastAPI Swagger UI):** http://localhost:8000/docs
   - **MongoDB:** `mongodb://localhost:27017`

## Development Notes
- The Next.js app uses TailwindCSS for styling.
- The FastAPI backend uses `rapidfuzz` for joining professor names between Albert and RateMyProf.
- Ensure to configure the correct CORS settings in `backend/main.py` when deploying to production.
