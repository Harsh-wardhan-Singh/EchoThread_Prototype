EchoThread AI Agent Instruction File
0. CONTEXT (READ FIRST)

You are working on a hackathon prototype project (15–16 hours build constraint).

This is NOT a production system.
This is NOT a full MVP.

Your goal is:

Build a working, stable, demo-ready prototype
Prioritize clarity, reliability, and demo flow
Avoid overengineering
1. PROJECT OVERVIEW

Project Name: EchoThread

EchoThread is a mental health intelligence system for colleges that includes:

Anonymous public posting system
Private emotional diary tracking
AI-based sentiment analysis
Counselor escalation system
Institutional analytics ("Campus Pulse Engine")
2. ARCHITECTURE (IMPORTANT)
High-Level Architecture

Frontend (React + Vite + TailwindCSS v3)
↓
Backend (FastAPI)
↓
AI Layer (LLaMA / fallback logic)
↓
Database (MongoDB or in-memory fallback)

Expected Folder Structure

echoThread/
├── frontend/
│ └── src/
│ ├── components/
│ ├── pages/
│ ├── services/
│ ├── data/
│ ├── App.jsx
│ ├── main.jsx
│ └── index.css
│
├── backend/
│ ├── main.py
│ ├── routes/
│ ├── services/
│ ├── utils/
│ ├── db.py
│ └── data/

3. FILE RESPONSIBILITIES
FRONTEND
pages/
Login.jsx → email + OTP + role detection
Diary.jsx → user input + AI sentiment analysis
Feed.jsx → anonymous posts (NO sentiment labels)
PulseDashboard.jsx → aggregated analytics
CounselorDashboard.jsx → flagged posts view
components/
PostCard.jsx → displays post content ONLY (no sentiment)
Navbar.jsx → shows role + navigation
PulseChart.jsx → graphs (Chart.js)
services/
api.js → all backend API calls
data/
mockData.js → fallback data (posts, analytics)
App.jsx
Controls routing:
student flow
counselor flow
BACKEND
routes/
auth.py → OTP + role logic
ai.py → sentiment endpoint (/analyze)
post.py → create + fetch posts
pulse.py → analytics endpoint
services/
sentiment.py → LLaMA-based or fallback sentiment
risk.py → simple LOW/MEDIUM/HIGH logic
utils/
otp.py → OTP generation + verification
db.py
MongoDB connection
data/
fake_data.py → fallback dataset
4. TECHNOLOGY STACK (STRICT)

Frontend:

React (Vite)
TailwindCSS v3
Axios
Chart.js

Backend:

FastAPI (Python)
Uvicorn

AI:

HuggingFace InferenceClient
Model: meta-llama/Meta-Llama-3-8B-Instruct
Fallback: rule-based sentiment

Database:

MongoDB (Atlas preferred)
OR in-memory fallback
5. AUTHENTICATION SYSTEM

We are using a hybrid OTP system:

Student Login:
Email must end with: .hrc.ac.in
OTP is generated and verified
Fallback OTP allowed: 123456
Counselor Login:
Email: counselor@hrc.ac.in
OTP bypass allowed
Accept OTP: 999999
IMPORTANT:
UI must always show "OTP sent"
Do NOT expose internal logic
6. AI SYSTEM
Primary:
Use LLaMA via HuggingFace
Task:
Classify:
sentiment → positive / neutral / negative
emotion → stress / anxiety / calm etc.
Fallback:
Simple keyword-based classification
7. CRITICAL DESIGN RULES
DO NOT:
Overengineer
Add microservices
Build real-time chat
Add unnecessary features
DO:
Keep system simple
Ensure all flows work
Use mock data where needed
8. IMPLEMENTATION INSTRUCTIONS

You must follow this workflow STRICTLY:

Step 1:

Analyze the existing codebase fully

Understand all files
Map them to intended architecture
Identify missing connections
Step 2:

Compare current implementation with expected architecture

Identify gaps
Identify broken flows
DO NOT change structure unnecessarily
Step 3:

Start connecting systems

Order:

Backend runs successfully
Frontend runs successfully
Connect API (frontend ↔ backend)
Add database connection
Integrate AI sentiment
Connect UI flows
Step 4:

After EACH step:

Test functionality
Verify outputs
Check for errors
Fix immediately
9. STRICT RULES
DO NOT MODIFY:
Existing structure unnecessarily
File naming conventions
DO:
Extend existing files
Connect missing logic
Add minimal required code
10. INTERACTION RULES

You MUST:

Ask before making assumptions
Ask for missing files if needed
Ask for clarification if unclear
Never guess architecture
11. HACKATHON CONSTRAINT

This project must be:

Buildable within 15–16 hours
Demo-friendly
Stable
Visually convincing

NOT:

Fully scalable
Fully secure
Production-ready
12. FINAL GOAL

A working system where:

Frontend runs
Backend runs
APIs connect
Database connects
AI gives output
Demo flow works end-to-end
13. SUCCESS CRITERIA

You are successful if:

User can log in
User can write diary
AI responds
User can post
Feed shows posts
Pulse dashboard displays data
Counselor view works