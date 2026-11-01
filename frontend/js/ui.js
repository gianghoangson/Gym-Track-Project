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
  if (reps <= 1) return weight;
  return Math.round(weight * (1 + reps / 30));
}