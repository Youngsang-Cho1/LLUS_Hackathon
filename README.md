# Ultimate NYU Course Search & Academic Planner

An AI-powered academic planning tool designed for NYU students. Beyond simple course searching, this app analyzes your **unofficial transcript** to identify missing requirements and recommends the best courses to take next by integrating **NYU Albert** data with **RateMyProfessor** ratings.

---

## Key Features

### AI Transcript Analysis
- **Automatic Parsing:** Upload your NYU unofficial transcript (PDF/Text) to automatically extract completed courses, grades, and cumulative GPA.
- **Requirement Tracking:** Real-time calculation of remaining Core, Major, and Minor requirements.

### Smart Course Recommendations
- **Prerequisite Validation:** Filter out courses you aren't eligible for yet; priority is given to courses where all prerequisites are met.
- **Professor Insights:** Integrated **RateMyProfessor** scores (Difficulty, Rating, Take-Again %) using fuzzy name matching.
- **Top K Ranking:** A weighted algorithm recommends the "best" courses based on your academic track and professor quality.

### Advanced Search
- Semantic search across the entire NYU CAS course catalog using vector embeddings.
- Filter by major, academic year, and specific tracks (e.g., Computer Science - CS Track).

---

## Tech Stack

- **Frontend:** [Next.js 15+](https://nextjs.org/) (App Router, TypeScript, TailwindCSS)
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11, Uvicorn)
- **Database:** [MongoDB](https://www.mongodb.com/) (Motor for async I/O)
- **AI/ML:** 
  - `RapidFuzz` for professor name matching.
  - `Sentence-Transformers` for course description embeddings.
- **Infrastructure:** [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)

---

## Repository Structure

```text
LLUS_Hackathon/
├── frontend/           # Next.js Application (Port 3000)
├── backend/            # FastAPI Application (Port 8000)
├── scraper/            # Python scripts for NYU Albert & RMP scraping + Transcript parsing
├── docker-compose.yml  # Multi-container orchestration
└── README.md           # You are here!
```

---

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Youngsang-Cho1/LLUS_Hackathon.git
   cd LLUS_Hackathon
   ```

2. **Launch the entire stack:**
   ```bash
   docker-compose up --build
   ```

3. **Access the app:**
   - **Web UI:** [http://localhost:3000](http://localhost:3000)
   - **API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Database UI (Mongo Express):** [http://localhost:8082](http://localhost:8082)

---

## Development & Scraper

To run a manual scrape or refresh the course index:
```bash
docker-compose --profile run run scraper python scrape_cas.py
```

To run the recommendation engine logic locally with a transcript:
```bash
docker-compose --profile run run scraper python recommend.py /app/path/to/transcript.pdf
```

---

## Authors & License
Built for the **NYU LLUS Hackathon**.
