checkLogin();
showNav();

let exercises = [];   // danh sách bài tập
let workout = null;   // buổi tập đang diễn ra
let timerId = null;   // id của setInterval

function exerciseName(id) {
  for (const e of exercises) {
    if (e.id === id) return e.name;
  }
  return "?";
}

// Chạy khi mở trang
async function init() {
  exercises = await callApi("/exercises");

  // đổ danh sách bài tập vào ô chọn
  let options = "";
  for (const e of exercises) {
    options += '<option value="' + e.id + '">' + e.name + "</option>";
  }
  document.getElementById("exerciseSelect").innerHTML = options;

  // đổ danh sách routine
  const routines = await callApi("/routines");
  let routineOptions = "";
  for (const r of routines) {
    routineOptions += '<option value="' + r.id + '">' + r.name + "</option>";
  }
  document.getElementById("routineSelect").innerHTML = routineOptions || "<option value=''>(chưa có routine)</option>";

  // nếu đang có buổi tập dở thì mở lại
  const savedId = localStorage.getItem("workoutId");
  if (savedId) {
    try {
      workout = await callApi("/workouts/" + savedId);
      if (workout.end_time) {
        localStorage.removeItem("workoutId");
        workout = null;
      }
    } catch (error) {
      localStorage.removeItem("workoutId");
    }
  }
  showScreen();
}

// Hiện màn hình phù hợp
function showScreen() {
  if (workout) {
    document.getElementById("startBox").style.display = "none";
    document.getElementById("workoutBox").style.display = "block";
    showSets();
  } else {
    document.getElementById("startBox").style.display = "block";
    document.getElementById("workoutBox").style.display = "none";
  }
}

async function startWorkout() {
  workout = await callApi("/workouts", "POST", {});
  localStorage.setItem("workoutId", workout.id);
  showScreen();
}

async function startFromRoutine() {
  const routineId = document.getElementById("routineSelect").value;
  if (!routineId) {
    alert("Bạn chưa có routine nào");
    return;
  }
  workout = await callApi("/workouts", "POST", { routine_id: routineId });
  localStorage.setItem("workoutId", workout.id);
  showScreen();
}

// Hiện danh sách set
function showSets() {
  let html = "";
  for (const s of workout.sets) {
    const rowClass = s.is_completed ? "done" : "";
    html += '<tr class="' + rowClass + '">';
    html += "<td>" + exerciseName(s.exercise_id) + "</td>";
    html += "<td>" + s.set_number + "</td>";
    html += '<td><input type="number" style="width:70px" value="' + s.weight + '" onchange="changeSet(\'' + s.id + "', 'weight', this.value)\"></td>";
    html += '<td><input type="number" style="width:70px" value="' + s.reps + '" onchange="changeSet(\'' + s.id + "', 'reps', this.value)\"></td>";
    html += "<td>" + estimate1RM(s.weight, s.reps) + "</td>";
    html += "<td>";
    html += "<button onclick=\"completeSet('" + s.id + "', " + !s.is_completed + ')">' + (s.is_completed ? "Bỏ" : "Xong") + "</button> ";
    html += "<button class=\"light\" onclick=\"deleteSet('" + s.id + "')\">Xoá</button>";
    html += "</td></tr>";
  }
  document.getElementById("sets").innerHTML = html;
}

// Tải lại buổi tập từ server rồi hiện lại
async function reload() {
  workout = await callApi("/workouts/" + workout.id);
  showSets();
}

async function addSet() {
  const body = {
    exercise_id: document.getElementById("exerciseSelect").value,
    weight: Number(document.getElementById("weight").value),
    reps: Number(document.getElementById("reps").value),
  };
  await callApi("/workouts/" + workout.id + "/sets", "POST", body);
  await reload();
}

async function changeSet(setId, field, value) {
  const body = {};
  body[field] = Number(value);
  await callApi("/workouts/sets/" + setId, "PUT", body);
  await reload();
}

async function completeSet(setId, done) {
  await callApi("/workouts/sets/" + setId, "PUT", { is_completed: done });
  await reload();
  if (done) {
    startTimer();  // hoàn thành set thì bắt đầu đếm giờ nghỉ
  }
}

async function deleteSet(setId) {
  await callApi("/workouts/sets/" + setId, "DELETE");
  await reload();
}

// Đồng hồ đếm ngược thời gian nghỉ
function startTimer() {
  let seconds = Number(document.getElementById("restSeconds").value) || 60;
  const timerBox = document.getElementById("timer");
  timerBox.style.display = "block";
  clearInterval(timerId);

  timerBox.textContent = "Nghỉ: " + seconds + " giây";
  timerId = setInterval(function () {
    seconds = seconds - 1;
    if (seconds <= 0) {
      clearInterval(timerId);
      timerBox.textContent = "Hết giờ nghỉ, tập set tiếp!";
    } else {
      timerBox.textContent = "Nghỉ: " + seconds + " giây";
    }
  }, 1000);
}

async function finishWorkout() {
  const result = await callApi("/workouts/" + workout.id + "/finish", "POST");
  localStorage.removeItem("workoutId");
  alert("Xong! Tổng volume: " + result.total_volume + " kg");
  window.location.href = "history.html";
}

async function cancelWorkout() {
  if (confirm("Huỷ buổi tập này?")) {
    await callApi("/workouts/" + workout.id, "DELETE");
    localStorage.removeItem("workoutId");
    workout = null;
    showScreen();
  }
}

init();
