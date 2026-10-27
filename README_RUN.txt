Backend:
  cd backend && python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  (edit .env, create the database "gym_tracker" in PostgreSQL)
  alembic revision --autogenerate -m "init"
  alembic upgrade head
  uvicorn app.main:app --reload        # Swagger UI: http://localhost:8000/docs

Frontend:
  cd frontend && python -m http.server 5500   # open http://localhost:5500/login.html
