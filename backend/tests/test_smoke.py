"""HTTP smoke tests using a disposable SQLite database, never backend/.env.

Run: python -B backend/tests/test_smoke.py
PostgreSQL-specific row-lock concurrency still needs PostgreSQL testing.
"""
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class SmokeTests(unittest.TestCase):
    requests_made = 0

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="gym-smoke-")
        cls.env = patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///" + str(Path(cls.temp.name) / "test.sqlite"),
            "SECRET_KEY": secrets.token_hex(32), "ALGORITHM": "HS256",
        })
        cls.env.start()
        # Disable dotenv before either database.py or auth.py is imported.
        cls.dotenv = patch("dotenv.load_dotenv", return_value=False)
        cls.dotenv.start()
        from app.database import engine
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        from app.main import app
        import uvicorn
        cls.socket = socket.socket()
        cls.socket.bind(("127.0.0.1", 0))
        cls.url = "http://127.0.0.1:" + str(cls.socket.getsockname()[1])
        cls.server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
        cls.thread = threading.Thread(target=cls.server.run, kwargs={"sockets": [cls.socket]}, daemon=True)
        cls.thread.start()
        for _ in range(100):
            if cls.server.started:
                break
            time.sleep(0.05)
        if not cls.server.started:
            raise RuntimeError("Temporary test server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.thread.join(timeout=10)
        cls.socket.close()
        from app.database import engine
        engine.dispose()
        cls.dotenv.stop()
        cls.env.stop()
        cls.temp.cleanup()
        print(f"\n{cls.requests_made} isolated HTTP requests checked.")

    def api(self, method, path, token=None, body=None, status=200):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        req = Request(self.url + path, method=method, headers=headers,
                      data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(req, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read().decode()
            self.assertEqual(response.status, status, f"{method} {path}: {raw}")
        type(self).requests_made += 1
        return json.loads(raw) if raw else None

    def account(self):
        email = str(uuid4()) + "@example.com"
        data = {"email": email, "password": "test-password"}
        self.api("POST", "/users/register", body=data)
        return self.api("POST", "/users/login", body=data)["access_token"]

    def exercise(self, token, name=None):
        return self.api("POST", "/exercises", token, {"name": name or str(uuid4())})

    def routine(self, token, *exercises):
        return self.api("POST", "/routines", token, {
            "name": " Push Day ", "exercises": [{"exercise_id": e["id"], "target_sets": i + 1}
                                                    for i, e in enumerate(exercises)],
        })

    def test_authentication_and_legacy_password(self):
        self.api("POST", "/users/register", body={"email": "bad", "password": "secret"}, status=422)
        self.api("POST", "/users/register", body={"email": "short@example.com", "password": "123"}, status=422)
        self.api("POST", "/users/register", body={"email": "blank@example.com", "password": "      "}, status=422)
        data = {"email": " MixedCase@Example.com ", "password": "secret"}
        self.api("POST", "/users/register", body=data)
        self.api("POST", "/users/register", body={**data, "email": "mixedcase@example.com"}, status=400)
        self.api("POST", "/users/login", body={**data, "password": "wrong"}, status=401)
        self.assertIn("access_token", self.api("POST", "/users/login", body=data))
        self.api("GET", "/exercises", token="invalid", status=401)
        # HTTPBearer's missing-token response varies across FastAPI releases.
        try:
            urlopen(self.url + "/exercises")
            self.fail("Unauthenticated request accepted")
        except HTTPError as error:
            self.assertIn(error.code, (401, 403))
        from app.database import SessionLocal
        from app.models import User
        from app.auth.auth import hash_password
        with SessionLocal() as db:
            db.add(User(email="Old@Example.com", password_hash=hash_password("abc")))
            db.commit()
        self.assertIn("access_token", self.api("POST", "/users/login", body={"email": " old@example.com ", "password": "abc"}))

    def test_exercise_crud_and_protection(self):
        a, b = self.account(), self.account()
        default = next(e for e in self.api("GET", "/exercises", a) if e["name"] == "Bench Press")
        e = self.exercise(a, "  My Row  ")
        self.assertEqual(e["name"], "My Row")
        self.api("POST", "/exercises", a, {"name": "my row"}, status=409)
        self.api("POST", "/exercises", a, {"name": " bench press "}, status=409)
        self.api("POST", "/exercises", a, {"name": "  "}, status=422)
        self.api("PUT", "/exercises/" + e["id"], b, {"name": "stolen"}, status=404)
        self.api("DELETE", "/exercises/" + e["id"], b, status=404)
        self.api("PUT", "/exercises/" + default["id"], a, {"name": "bad"}, status=404)
        self.api("DELETE", "/exercises/" + default["id"], a, status=404)
        self.api("PUT", "/exercises/" + e["id"], a, {"name": "Squat"}, status=409)
        changed = self.api("PUT", "/exercises/" + e["id"], a, {"name": " Updated Row ", "muscle_group": " Back ", "equipment": " "})
        self.assertEqual((changed["name"], changed["muscle_group"], changed["equipment"]), ("Updated Row", "Back", None))
        self.assertNotIn(e["id"], [x["id"] for x in self.api("GET", "/exercises", b)])
        self.api("DELETE", "/exercises/" + e["id"], a)

    def test_routine_crud_order_and_validation(self):
        a, b = self.account(), self.account()
        e1, e2, private = self.exercise(a), self.exercise(a), self.exercise(b)
        routine = self.routine(a, e1, e2)
        path = "/routines/" + routine["id"]
        self.assertEqual(routine["name"], "Push Day")
        self.assertEqual([e["order_index"] for e in routine["exercises"]], [0, 1])
        self.assertEqual(self.api("GET", path, a)["id"], routine["id"])
        self.assertEqual(self.api("GET", "/routines", b), [])
        self.api("GET", path, b, status=404)
        self.api("DELETE", path, b, status=404)
        body = {"name": "Edited", "exercises": [{"exercise_id": e2["id"], "target_sets": 3}, {"exercise_id": e1["id"], "target_sets": 2}]}
        self.api("PUT", path, b, body, status=404)
        result = self.api("PUT", path, a, body)
        self.assertEqual([e["exercise_id"] for e in result["exercises"]], [e2["id"], e1["id"]])
        for bad in [[], [{"exercise_id": e1["id"], "target_sets": 0}], [body["exercises"][0]] * 2]:
            self.api("POST", "/routines", a, {"name": "Bad", "exercises": bad}, status=422)
        self.api("POST", "/routines", a, {**body, "name": " "}, status=422)
        for eid in [private["id"], str(uuid4())]:
            bad = {"name": "Bad", "exercises": [{"exercise_id": eid, "target_sets": 1}]}
            self.api("POST", "/routines", a, bad, status=404)
            self.api("PUT", path, a, bad, status=404)
        self.assertEqual(self.api("GET", path, a)["name"], "Edited")
        self.api("DELETE", "/exercises/" + e1["id"], a, status=409)
        self.api("DELETE", path, a)
        self.api("GET", path, a, status=404)
        self.api("DELETE", "/exercises/" + e1["id"], a)

    def test_workout_lifecycle_and_statistics(self):
        a, b = self.account(), self.account()
        bench = next(e for e in self.api("GET", "/exercises", a) if e["name"] == "Bench Press")
        private = self.exercise(b)
        w = self.api("POST", "/workouts", a, {})
        path = "/workouts/" + w["id"]
        self.assertEqual(self.api("POST", "/workouts", a, {})["id"], w["id"])
        self.assertEqual(self.api("GET", "/workouts/active", a)["id"], w["id"])
        self.assertIsNone(self.api("GET", "/workouts/active", b))
        self.assertEqual(self.api("GET", "/workouts", a), [])
        self.assertEqual(self.api("GET", "/workouts/stats/dashboard", a)["total_workouts"], 0)
        self.api("GET", path, b, status=404)
        self.api("DELETE", path, b, status=404)
        self.api("POST", path + "/finish", b, status=404)
        for eid in [private["id"], str(uuid4())]:
            self.api("POST", path + "/sets", a, {"exercise_id": eid}, status=404)
        for bad in [{"weight": -1}, {"reps": -1}, {"reps": 1.5}, {"weight": "Infinity"}]:
            self.api("POST", path + "/sets", a, {"exercise_id": bench["id"], **bad}, status=422)
        sets = [self.api("POST", path + "/sets", a, {"exercise_id": bench["id"]}) for _ in range(3)]
        self.api("DELETE", "/workouts/sets/" + sets[1]["id"], a)
        last = self.api("POST", path + "/sets", a, {"exercise_id": bench["id"], "weight": 999, "reps": 10})
        self.assertEqual(last["set_number"], 4)
        sp = "/workouts/sets/" + sets[0]["id"]
        self.api("PUT", sp, b, {"weight": 5}, status=404)
        self.api("DELETE", sp, b, status=404)
        self.api("PUT", sp, a, {"reps": -2}, status=422)
        self.api("PUT", sp, a, {"weight": 50, "reps": 10, "is_completed": True})
        self.api("PUT", "/workouts/sets/" + sets[2]["id"], a, {"weight": 100, "reps": 1, "is_completed": True})
        result = self.api("POST", path + "/finish", a)
        self.assertEqual(result["total_volume"], 600)
        self.assertIsNotNone(result["end_time"])
        self.assertEqual([s["set_number"] for s in result["sets"]], [1, 3, 4])
        for body in [{"weight": 5}, {"reps": 3}, {"is_completed": False}]:
            self.api("PUT", sp, a, body, status=409)
        self.api("DELETE", sp, a, status=409)
        self.api("POST", path + "/sets", a, {"exercise_id": bench["id"]}, status=409)
        self.api("POST", path + "/finish", a, status=409)
        self.assertEqual(self.api("GET", path, a), result)
        stats = self.api("GET", "/workouts/stats/dashboard", a)
        self.assertEqual(stats["total_workouts"], 1)
        self.assertEqual(stats["per_month"], {w["start_time"][:7]: 1})
        self.assertEqual(stats["best_1rm"]["Bench Press"], 100)
        self.assertEqual(len(self.api("GET", "/workouts", a)), 1)
        self.assertEqual(self.api("GET", "/workouts", b), [])
        self.assertIsNone(self.api("GET", "/workouts/active", a))
        self.api("DELETE", path, a)
        self.assertEqual(self.api("GET", "/workouts", a), [])
        from app.database import SessionLocal
        from app.models import WorkoutSet
        with SessionLocal() as db:
            self.assertEqual(db.query(WorkoutSet).filter_by(workout_id=UUID(w["id"])).count(), 0)

    def test_routine_workout_snapshot_cancel_and_references(self):
        a, b = self.account(), self.account()
        e1, e2 = self.exercise(a), self.exercise(a)
        routine = self.routine(a, e1, e2)
        self.api("POST", "/workouts", b, {"routine_id": routine["id"]}, status=404)
        w = self.api("POST", "/workouts", a, {"routine_id": routine["id"]})
        self.assertEqual(w["name"], "Push Day")
        self.assertEqual([s["exercise_id"] for s in w["sets"]], [e1["id"], e2["id"], e2["id"]])
        self.assertEqual([s["set_number"] for s in w["sets"]], [1, 2, 3])
        self.api("DELETE", "/routines/" + routine["id"], a)
        self.assertEqual(self.api("GET", "/workouts/" + w["id"], a)["sets"], w["sets"])
        self.api("DELETE", "/exercises/" + e1["id"], a, status=409)
        self.api("DELETE", "/workouts/" + w["id"], a)
        self.assertIsNone(self.api("GET", "/workouts/active", a))
        self.api("DELETE", "/exercises/" + e1["id"], a)

    def test_seed_restores_only_missing_defaults(self):
        from app.database import SessionLocal
        from app.models import Exercise
        from app.main import DEFAULT_EXERCISES, seed_default_exercises
        with SessionLocal() as db:
            row = db.query(Exercise).filter_by(name="Plank", user_id=None).one()
            db.delete(row)
            db.query(Exercise).filter_by(name="Pull Up", user_id=None).one().name = " pull up "
            db.commit()
        seed_default_exercises()
        seed_default_exercises()
        with SessionLocal() as db:
            names = [e.name.strip().lower() for e in db.query(Exercise).filter_by(user_id=None)]
        self.assertEqual(len(names), len(DEFAULT_EXERCISES))
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("plank", names)

    def test_legacy_exercise_can_be_listed_and_repaired(self):
        # New-input validation must not prevent listing old records for repair.
        token = self.account()
        from app.database import SessionLocal
        from app.models import Exercise
        from app.auth.auth import SECRET_KEY, ALGORITHM
        from jose import jwt
        user_id = UUID(jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"])
        with SessionLocal() as db:
            exercise = Exercise(name=" ", user_id=user_id)
            db.add(exercise)
            db.commit()
            eid = str(exercise.id)
        self.assertIn(eid, [e["id"] for e in self.api("GET", "/exercises", token)])
        self.api("PUT", "/exercises/" + eid, token, {"name": "Repaired exercise"})
        self.api("DELETE", "/exercises/" + eid, token)


if __name__ == "__main__":
    unittest.main(verbosity=2)
