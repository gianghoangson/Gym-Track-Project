
function saveToken(token) {
  localStorage.setItem("token", token);
}

function getToken() {
  return localStorage.getItem("token");
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("workoutId");
  window.location.href = "login.html";
}

// Gọi ở đầu mỗi trang: chưa đăng nhập thì chuyển về login
function checkLogin() {
  if (getToken() === null) {
    window.location.href = "login.html";
  }
}