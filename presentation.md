# NYUSEARCH - Hackathon Presentation Outline

## 1. Introduction (The Problem)
- **Hook:** Every semester, NYU students spend hours struggling with Albert to figure out what classes they need to take and how to build a clash-free schedule.
- **Pain Points:** 
  - Manually checking degree requirements is tedious.
  - Figuring out what courses you've already taken vs. what you still need requires jumping between different tabs.
  - Building a schedule manually often results in time conflicts and frustration.

## 2. Our Solution: NYUSEARCH
- **What it is:** A smart, all-in-one academic planner that automates the entire registration workflow.
- **Value Proposition:** From uploading your transcript to generating the perfect weekly schedule, we reduce hours of stress into just a few clicks.

## 3. Live Demo Flow (Features)

**Step 1: Automated Transcript Parsing**
- *Action:* Go to the Dashboard and upload an NYU Albert Transcript (PDF).
- *Highlight:* Instead of manually typing 30+ courses, our custom Python parser (`pdfplumber` + Regex) instantly extracts the student's completed courses (e.g., CSCI-UA 101, MATH-UA 120).

**Step 2: Intelligent Progress Tracking**
- *Action:* Show the "Classes Taken" and "Classes To Take" sections on the Dashboard.
- *Highlight:* The system automatically cross-references the student's completed courses with their major requirements to instantly show what's left to graduate.

**Step 3: Course Discovery & Search**
- *Action:* Navigate to the "Recommend" or "Courses" tab.
- *Highlight:* Type in a course name or code (e.g., "CSCI-UA 201"). Our text-based search instantly pulls up the exact matching courses with descriptions and credit info. Click "Add to Schedule".

**Step 4: Smart Schedule Generation**
- *Action:* Proceed to generate the schedule.
- *Highlight:* Show the interactive calendar UI. Emphasize that the backend calculates clash-free time slots and renders them beautifully from 8 AM to 10 PM, handling everything automatically.

## 4. Technical Stack
- **Frontend:** Next.js (React), Tailwind CSS, Lucide Icons (Glassmorphism UI, Responsive Design)
- **Backend:** FastAPI (Python), Motor (Async MongoDB)
- **Data & Parsing:** Python (`pdfplumber`, regex) for parsing NYU Albert transcripts and mapping degree requirements.
- **Infrastructure:** Dockerized containers for seamless deployment.

## 5. Future Roadmap
- Integration with RateMyProfessors for professor quality scores.
- Real-time seat availability scraping.
- Semantic AI search to recommend electives based on career interests.

## 6. Q&A / Thank You
- "Thank you for listening! We are excited to make NYU registration stress-free. Any questions?"
