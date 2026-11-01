checkLogin();
showNav();

async function loadDashboard() {
  const data = await callApi("/workouts/stats/dashboard");

  document.getElementById("total").textContent = data.total_workouts;

  // Số buổi tập mỗi tháng
  let monthHtml = "";
  for (const month in data.per_month) {
    monthHtml += "<tr><td>" + month + "</td><td>" + data.per_month[month] + "</td></tr>";
  }
  document.getElementById("months").innerHTML = monthHtml || "<tr><td colspan='2'>Chưa có buổi tập nào</td></tr>";

  // 1RM của 3 bài chính
  let rmHtml = "";
  for (const name in data.best_1rm) {
    rmHtml += "<tr><td>" + name + "</td><td>" + data.best_1rm[name] + " kg</td></tr>";
  }
  document.getElementById("rm").innerHTML = rmHtml;
}

loadDashboard();