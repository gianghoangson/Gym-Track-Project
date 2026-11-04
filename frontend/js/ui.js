// Các hàm giao diện dùng chung

// Hiện thanh menu ở đầu trang
function showNav() {
  document.getElementById("nav").innerHTML =
    '<a href="index.html">Dashboard</a>' +
    '<a href="workout.html">Workout</a>' +
    '<a href="history.html">History</a>' +
    '<a href="exercises.html">Exercises</a>' +
    '<a href="#" onclick="logout()">Logout</a>';
}

// Ngày dạng dd/mm/yyyy
function formatDate(text) {
  return new Date(text).toLocaleDateString("vi-VN");
}

// Số phút giữa 2 mốc thời gian
function minutesBetween(start, end) {
  return Math.round((new Date(end) - new Date(start)) / 60000);
}

// 1RM ước tính (công thức Epley)
function estimate1RM(weight, reps) {
  if (reps <= 0) return 0;
  const value = reps === 1 ? weight : weight * (1 + reps / 30);
  return Math.round(value * 10) / 10;
}

// Escape user-provided strings before inserting them into existing HTML tables.
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function showError(message) {
  let box = document.getElementById("error");
  if (!box) {
    box = document.createElement("div");
    box.id = "error";
    document.querySelector(".container h1").after(box);
  }
  box.className = message ? "error" : "";
  box.setAttribute("role", "alert");
  box.textContent = message || "";
}

async function runUiAction(action) {
  showError("");
  try { return await action(); }
  catch (error) { showError(error.message || "Có lỗi xảy ra"); }
}
