# 🏋️‍♂️ Gym Tracker

Gym Tracker is a web application designed to manage gym schedules and track personal progress. Inspired by Hevy, it focuses entirely on personal tracking by removing social features. The system is built on a RESTful API architecture, ensuring complete separation between the frontend and backend.

## 🌟 Key Features

*   **Live Workout Tracking:** Start an empty workout or select a routine, and log individual sets with weight and reps.
*   **Automatic Rest Timers:** Marking a set as complete automatically triggers a countdown timer for your rest period.
*   **Volume Calculation:** Finishing a workout automatically calculates the total volume (weight lifted) and logs the end time.
*   **Custom Exercises & Routines:** Create custom exercises (or use defaults) and build reusable workout templates.
*   **Dashboard Analytics:** View your monthly workout frequency and track changes in your 1RM (One Rep Max) for main lifts like Bench Press, Squat, and Deadlift.

## 💻 Tech Stack

*   **Backend:** Python with FastAPI for high performance, async support, and automatic Swagger UI generation.
*   **Database:** PostgreSQL, integrated using SQLAlchemy as the ORM and Alembic for database version control (migrations).
*   **Frontend:** Vanilla HTML, CSS, and JavaScript interacting with the backend via the `fetch()` API.

## 📂 Project Structure

### Backend

The backend is organized into domain-specific modules:

```text
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # PostgreSQL connection setup (Engine, SessionLocal)
│   ├── models.py               # SQLAlchemy classes (Entities)
│   ├── schemas.py              # Pydantic models for data validation
│   ├── auth/                   # JWT Token handling and password hashing (Passlib, Jose)
│   └── routers/                # API Endpoints
│       ├── users.py           
│       ├── exercises.py        # GET exercises, POST custom exercises
│       ├── routines.py         # CRUD operations for workout templates
│       └── workouts.py         # POST start workout, PUT update sets, GET history
├── alembic/                    # Database migration version control
├── requirements.txt           
└── .env                        # Stores DATABASE_URL, SECRET_KEY, ALGORITHM
```

### Frontend

The frontend is a lightweight Single Page Application (SPA) or Multi-Page structure utilizing DOM manipulation:

```text
frontend/
├── index.html                  # Dashboard with summary statistics and charts
├── workout.html                # Live workout tracking interface
├── history.html                # Workout history log
├── exercises.html              # Exercise dictionary and custom exercise creation
├── login.html                  # User authentication
├── css/
│   ├── style.css               # Global reset, typography, and CSS variables
│   ├── components.css          # Styling for buttons, forms, cards, and modals
│   └── workout.css             # Specific styles for the live workout screen (timer, sets)
└── js/
    ├── api.js                  # fetch() abstraction layer with Bearer token handling
    ├── auth.js                 # JWT token management in local/session storage
    ├── ui.js                   # Dynamic HTML rendering functions
    ├── dashboard.js            # Chart rendering and overview data fetching
    └── live_workout.js         # Core logic: timers, 1RM estimation, and set completion
```

## 🗄️ Database Schema

The PostgreSQL database utilizes the following core tables:

*   **`users`**: Stores user information including `id` (UUID), `email`, and `password_hash`.
*   **`exercises`**: Houses both default and custom exercises, categorized by `muscle_group` and `equipment`.
*   **`routines`**: Stores workout templates created by users.
*   **`routine_exercises`**: Links exercises to specific routines, defining `order_index` and `target_sets`.
*   **`workouts`**: Records actual workout sessions with `start_time`, `end_time`, and `total_volume`.
*   **`workout_sets`**: Details individual sets within a workout, tracking `weight`, `reps`, `rpe`, and `is_completed` status.

## 🚀 Getting Started

1.  **Set up the Database:** Ensure PostgreSQL is running. Configure your `.env` file in the `backend/` directory with your database credentials. Run migrations using Alembic (`alembic upgrade head`).
2.  **Run the Backend:** Install Python dependencies from `requirements.txt` and start the FastAPI server.
3.  **Run the Frontend:** Serve the `frontend/` directory using any basic local web server (e.g., Live Server or Python's `http.server`).
