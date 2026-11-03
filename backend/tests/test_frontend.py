"""Optional real-browser smoke check (requires Playwright + Chromium).

Run: python -B backend/tests/test_frontend.py
Uses test_smoke's disposable database and redirects browser API requests to it.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from uuid import uuid4

from test_smoke import SmokeTests
from playwright.sync_api import sync_playwright, expect


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    SmokeTests.setUpClass()
    root = Path(__file__).resolve().parents[2]
    static = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root / "frontend")))
    thread = threading.Thread(target=static.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:" + str(static.server_address[1])
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            # API_URL remains unchanged in the application. Only this test reroutes it.
            page.route("http://localhost:8000/**", lambda route: route.continue_(
                url=SmokeTests.url + route.request.url.removeprefix("http://localhost:8000")))
            page.on("dialog", lambda dialog: dialog.accept())
            page.goto(base + "/login.html")
            page.locator("#switchBtn").click()
            page.locator("#email").fill(str(uuid4()) + "@example.com")
            page.locator("#password").fill("test-password")
            page.locator("#submitBtn").click()
            page.wait_for_url("**/index.html")
            expect(page.locator("#total")).to_have_text("0")

            page.goto(base + "/exercises.html")
            expect(page.locator("#list tr")).to_have_count(10)
            page.locator("#name").fill("Browser Row")
            page.locator("#saveExerciseBtn").click()
            row = page.locator("#list tr").filter(has_text="Browser Row")
            expect(row).to_have_count(1)
            row.get_by_role("button", name="Sửa", exact=True).click()
            page.locator("#name").fill("Browser Row Edited")
            page.locator("#saveExerciseBtn").click()
            expect(page.locator("#list")).to_contain_text("Browser Row Edited")
            # Duplicate errors must be readable and preserve form input.
            page.locator("#name").fill("bench press")
            page.locator("#saveExerciseBtn").click()
            expect(page.locator("#error")).to_contain_text("đã tồn tại")
            expect(page.locator("#error")).not_to_contain_text("[object Object]")
            page.locator("#name").fill("Unused Browser Exercise")
            page.locator("#saveExerciseBtn").click()
            unused = page.locator("#list tr").filter(has_text="Unused Browser Exercise")
            unused.get_by_role("button", name="Xoá", exact=True).click()
            expect(unused).to_have_count(0)
            expect(page.locator("#list tr").filter(has_text="Bench Press").get_by_role("button")).to_have_count(0)

            page.goto(base + "/workout.html")
            expect(page.locator("#exerciseSelect option")).to_have_count(11)
            page.get_by_role("button", name="Tạo routine", exact=True).click()
            page.locator("#routineName").fill("Browser Routine")
            rows = page.locator("#routineRows tr")
            rows.nth(0).locator("select").select_option(label="Bench Press")
            rows.nth(0).locator("input").fill("1")
            page.get_by_role("button", name="Thêm bài tập", exact=True).click()
            rows.nth(1).locator("select").select_option(label="Browser Row Edited")
            rows.nth(1).locator("input").fill("2")
            rows.nth(1).get_by_role("button", name="Lên", exact=True).click()
            page.locator("#saveRoutineBtn").click()
            expect(page.locator("#routineList")).to_contain_text("Browser Routine")
            page.locator("#routineList").get_by_role("button", name="Sửa", exact=True).click()
            expect(rows.nth(0).locator("select option:checked")).to_have_text("Browser Row Edited")
            page.locator("#routineName").fill("Updated Routine")
            rows.nth(0).locator("input").fill("1")
            page.locator("#saveRoutineBtn").click()
            expect(page.locator("#routineSelect option:checked")).to_have_text("Updated Routine")
            page.locator("#startBox").get_by_role("button", name="Bắt đầu", exact=True).click()
            expect(page.locator("#sets tr")).to_have_count(2)
            expect(page.locator("#sets tr").nth(0)).to_contain_text("Browser Row Edited")

            # Missing localStorage ID must not lose the active server workout.
            page.evaluate("localStorage.removeItem('workoutId')")
            page.reload()
            expect(page.locator("#sets tr")).to_have_count(2)
            assert page.evaluate("Boolean(localStorage.getItem('workoutId'))")
            # Routine deletion does not delete copied workout sets.
            page.locator("#routineList").get_by_role("button", name="Xoá", exact=True).click()
            expect(page.locator("#routineList")).to_contain_text("Chưa có routine")
            expect(page.locator("#sets tr")).to_have_count(2)
            # Referenced exercises cannot be deleted through the UI.
            page.goto(base + "/exercises.html")
            page.locator("#list tr").filter(has_text="Browser Row Edited").get_by_role("button", name="Xoá", exact=True).click()
            expect(page.locator("#error")).to_contain_text("Không thể xoá")
            page.goto(base + "/workout.html")
            expect(page.locator("#sets tr")).to_have_count(2)
            # Complete Bench Press at one rep; other routine set stays incomplete.
            bench = page.locator("#sets tr").filter(has_text="Bench Press")
            bench.locator("input").nth(0).fill("100")
            bench.locator("input").nth(0).press("Tab")
            expect(bench.locator("input").nth(0)).to_have_value("100")
            page.wait_for_function("workout.sets.some(s => s.weight === 100)")
            bench.locator("input").nth(1).fill("1")
            bench.locator("input").nth(1).press("Tab")
            page.wait_for_function("workout.sets.some(s => s.reps === 1)")
            expect(bench.locator("td").nth(4)).to_have_text("100")
            bench.get_by_role("button", name="Xong", exact=True).click()
            expect(bench).to_have_class("done")
            expect(page.locator("#timer")).to_be_visible()
            page.get_by_role("button", name="Kết thúc buổi tập", exact=True).click()
            page.wait_for_url("**/history.html")
            expect(page.locator("#list")).to_contain_text("100 kg × reps")
            expect(page.locator("#list")).to_contain_text("Bench Press: 100 kg x 1")
            expect(page.locator("#list")).not_to_contain_text("Browser Row Edited")
            page.goto(base + "/index.html")
            expect(page.locator("#total")).to_have_text("1")
            expect(page.locator("#rm tr").filter(has_text="Bench Press")).to_contain_text("100 kg")
            page.goto(base + "/history.html")
            page.locator("#list").get_by_role("button", name="Xoá", exact=True).click()
            expect(page.locator("#list")).to_contain_text("Chưa có buổi tập nào")
            page.goto(base + "/workout.html")
            page.get_by_role("button", name="Bắt đầu buổi tập trống", exact=True).click()
            expect(page.locator("#workoutBox")).to_be_visible()
            page.get_by_role("button", name="Huỷ buổi tập", exact=True).click()
            expect(page.locator("#startBox")).to_be_visible()
            assert not page.evaluate("localStorage.getItem('workoutId')")
            assert errors == [], errors
            browser.close()
        print("Browser smoke passed: registration, exercise CRUD/errors, routine CRUD/order, recovery, timer, finish, history, dashboard and cancel.")
    finally:
        static.shutdown()
        static.server_close()
        thread.join(timeout=5)
        SmokeTests.tearDownClass()


if __name__ == "__main__":
    main()
