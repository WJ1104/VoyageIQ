<div align="center">
 
<br />
 
```
 ██╗   ██╗ ██████╗ ██╗   ██╗ █████╗  ██████╗ ███████╗██╗ ██████╗
 ██║   ██║██╔═══██╗╚██╗ ██╔╝██╔══██╗██╔════╝ ██╔════╝██║██╔═══██╗
 ██║   ██║██║   ██║ ╚████╔╝ ███████║██║  ███╗█████╗  ██║██║   ██║
 ╚██╗ ██╔╝██║   ██║  ╚██╔╝  ██╔══██║██║   ██║██╔══╝  ██║██║▄▄ ██║
  ╚████╔╝ ╚██████╔╝   ██║   ██║  ██║╚██████╔╝███████╗██║╚██████╔╝
   ╚═══╝   ╚═════╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚══▀▀═╝
```
 
### AI-Powered Travel Intelligence Platform
 
**Predict flights · Plan trips · Master your budget**
 
<br />
 
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-black?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![Backend](https://img.shields.io/badge/Backend-Python%20%2B%20FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Database](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite)](https://sqlite.org)
[![Language](https://img.shields.io/badge/Backend%20Language-Python%203.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![Styling](https://img.shields.io/badge/Styling-Tailwind%20CSS-06B6D4?style=for-the-badge&logo=tailwindcss)](https://tailwindcss.com)
 
<br />
 
</div>
 
---
 
##  Table of Contents
 
- [About the Project](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Running the Project](#-running-the-project)
- [API Reference](#-api-reference)
- [Deployment](#-deployment)
 
---
 
##  About the Project
 
VoyageIQ is an AI-powered travel intelligence platform that takes the stress out of trip planning. Instead of jumping between five different apps to book flights, plan hotels, manage a budget, and find restaurants — VoyageIQ does it all in one place.
 
The platform uses machine learning to predict when flight prices are about to rise, generates personalised budget plans based on your destination and group size, and builds complete day-by-day itineraries with flights, accommodation, food, and activities.
 
> **This is a monorepo** — the frontend and backend both live inside this single repository.

**Current backend:** the local MVP supports account registration and login, private trip management, and saved starter budget plans. Flight search, price prediction, bookings, and AI planning are later integrations.
 
---
 
##  Features
 
| Feature | Description |
|---|---|
|  **Flight Prediction** | ML model predicts whether a fare will rise or fall — tells you the best time to book |
|  **Smart Budget Planner** | Enter your total budget and get a category-by-category breakdown for any trip |
|  **Trip Planner** | Drag-and-drop itinerary builder covering flights, hotels, food, and activities |
|  **AI Assistant** | Chat with GPT-4 to plan entire trips in natural language |
|  **Price Alerts** | Set a target fare and get notified the moment it drops |
 
---
 
## 🛠 Tech Stack
 
### Frontend
| Tool | Purpose |
|---|---|
| Next.js 14 (App Router) | React framework with SSR and file-based routing |
| TypeScript | Static typing across the entire codebase |
| Tailwind CSS | Utility-first CSS styling |
| Zustand | Lightweight global state management |
| Axios | HTTP client for backend API calls |
| Recharts | Data visualisation (price charts, budget breakdowns) |
| Mapbox GL JS | Interactive maps |
 
### Backend
| Tool | Purpose |
|---|---|
| Python 3.11 | Primary backend language |
| FastAPI | High-performance REST API framework with auto-generated docs |
| SQLite | Local database for the backend MVP |
| PyJWT + bcrypt | Authentication and password hashing |
| Duffel API (test mode) | Simulated flight search and pricing for development |
| python-dotenv | Environment variable management |
| httpx | Async HTTP client for external service calls |
 
### DevOps
| Tool | Purpose |
|---|---|
| GitHub Actions | CI — lints and builds every PR automatically |
| Vercel | Frontend hosting (auto-deploys on push to main) |
| Render | Backend hosting (auto-deploys on push to main) |
| PostgreSQL | Planned production database; local MVP currently uses SQLite |
 
---
 
##  Getting Started
 
### Prerequisites
 
Make sure you have these installed before starting:
 
- **Python 3.11+** — [python.org](https://python.org)
- **Node.js v20+** — [nodejs.org](https://nodejs.org) *(frontend only)*
- **Git** — [git-scm.com](https://git-scm.com)
- **Git Bash** (Windows only) — installed with Git above
- **VS Code or PyCharm** — your code editor
 
### 1. Clone the Repository
 
```bash
git clone https://github.com/YOUR-USERNAME/voyageiq.git
cd VoyageIQ
```
 
### 2. Switch to the Dev Branch
 
```bash
git checkout dev
```
 
>  Always work on `dev` — never directly on `main`.
 
### 3. Set Up the Backend
 
```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```
 
### 4. Set Up the Frontend
 
```bash
cd ../frontend
npm install
```
 
### 5. Set Up Environment Files
 
```bash
# Backend
cd ../backend && cp .env.example .env

# Frontend
cd ../frontend && cp .env.local.example .env.local
```
 
Open each file and fill in the values — ask the lead for real API keys.
 
### 6. Set Up the Database
 
The backend creates its local SQLite database and tables automatically the first time it starts. The database file is `backend/voyageiq.db`.
 
### 7. Start the Project
 
```bash
# Start the backend (from the backend/ folder)
uvicorn app.main:app --reload --port 4000

# Start the frontend (from the frontend/ folder, in a separate terminal)
npm run dev
```
 
| App | URL |
|---|---|
|  Frontend | http://localhost:3000 |
|  Backend | http://localhost:4000 |
| API Docs (Swagger) | http://localhost:4000/docs |
|  Health check | http://localhost:4000/api/health |
 
---
 
##  Running the Project
 
```bash
# Backend — from the backend/ folder (make sure your venv is activated)
uvicorn app.main:app --reload --port 4000

# Frontend — from the frontend/ folder
npm run dev
```
 
>  **Tip:** Open two terminal windows — one for the backend and one for the frontend — and run them side by side.
 
---
 
##  API Reference
 
See **[API.md](./API.md)** for the full endpoint contract.
 
Quick overview:
 
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create a new account |
| `POST` | `/api/auth/login` | Log in and receive a JWT token |
| `GET` | `/api/flights/search` | Search Duffel test offers by route and date |
| `POST` | `/api/budget/calculate` | Generate a budget breakdown |
| `POST` | `/api/trips/{trip_id}/budget` | Save a budget plan to a trip |
| `GET` | `/api/trips/{trip_id}/budget` | Retrieve a trip's saved budget plan |
| `GET` | `/api/trips` | Get all trips for the logged-in user |
| `POST` | `/api/trips` | Create a new trip |
| `GET` | `/api/trips/{id}` | Get one trip |
| `PUT` | `/api/trips/{id}` | Update a trip |
| `DELETE` | `/api/trips/{id}` | Delete a trip |
| `GET` | `/api/trips/{id}/items` | List all itinerary items for a trip |
| `POST` | `/api/trips/{id}/items` | Add an item to a trip |
| `PUT` | `/api/trips/{id}/items/{item_id}` | Update an itinerary item |
| `DELETE` | `/api/trips/{id}/items/{item_id}` | Remove an itinerary item |
| `GET` | `/api/health` | Confirm the backend is running |
 
>  FastAPI auto-generates interactive API docs. With the backend running, visit **http://localhost:4000/docs** to explore and test every endpoint in your browser.
 
---
 
##  Deployment
 
| App | Platform | Trigger |
|---|---|---|
|  Frontend | [Vercel](https://vercel.com) | Auto-deploys when `main` is updated |
|  Backend | [Render](https://render.com) | Auto-deploys when `main` is updated |
|  Database | SQLite locally | Use a hosted PostgreSQL database before production deployment |
 
### Deploy Settings
 
**Vercel (Frontend)**
- Root Directory: `frontend`
- Framework: Next.js
 
The current backend is for local development. Before deploying it, switch the SQLite database to hosted PostgreSQL and configure a production `JWT_SECRET` and external service credentials.
 
>  Never push directly to `main`. Merge `dev` → `main` only when a version is stable and tested.
 
---
 
<div align="center">
 
Made with ☕ by the VoyageIQ team
 
</div>
