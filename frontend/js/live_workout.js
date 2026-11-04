checkLogin();
showNav();
let exercises = [];
let workout = null;
let timerId = null;
let workoutQueue = Promise.resolve();

function exerciseName(id) {
  return exercises.find(e => e.id === id)?.name || "?";
}

function rememberWorkout() {
  if (workout && !workout.end_time) localStorage.setItem("workoutId", workout.id);
  else localStorage.removeItem("workoutId");
}

async function init() {
  exercises = await callApi("/exercises");
  const select = document.getElementById("exerciseSelect");
  select.replaceChildren();
  exercises.forEach(e => select.add(new Option(e.name, e.id)));
  await loadRoutines();
  // The server is authoritative, including after logout or lost browser state.
  workout = await callApi("/workouts/active");
  rememberWorkout();
  showScreen();
}

function stopTimer() {
  clearInterval(timerId);
  timerId = null;
  document.getElementById("timer").style.display = "none";
}

function showScreen() {
  document.getElementById("startBox").style.display = workout ? "none" : "block";
  document.getElementById("workoutBox").style.display = workout ? "block" : "none";
  const finished = Boolean(workout?.end_time);
  document.getElementById("setControls").hidden = finished;
  document.getElementById("workoutActions").hidden = finished;
  document.getElementById("finishedNotice").hidden = !finished;
  if (!workout || finished) stopTimer();
  if (workout) showSets();
}

function workoutAction(action) {
  workoutQueue = workoutQueue.then(() => runUiAction(async () => {
    try { await action(); }
    catch (error) {
      // A different tab may have finished or deleted the workout.
      if (workout && (error.status === 409 || error.status === 404)) {
        try {
          workout = await callApi("/workouts/" + workout.id);
        } catch (loadError) {
          if (loadError.status === 404) workout = await callApi("/workouts/active");
        }
        rememberWorkout();
        showScreen();
      }
      throw error;
    }
  }));
  return workoutQueue;
}

function requireActive() {
  if (!workout || workout.end_time) throw new Error("Không có buổi tập đang hoạt động");
}

function startWorkout(routineId = null) {
  return workoutAction(async () => {
    const active = await callApi("/workouts/active");
    workout = active || await callApi("/workouts", "POST", routineId ? {routine_id: routineId} : {});
    rememberWorkout();
    showScreen();
    if (active) alert("Đã khôi phục buổi tập đang hoạt động.");
  });
}

function startFromRoutine() {
  const id = document.getElementById("routineSelect").value;
  if (!id) { showError("Bạn chưa chọn routine nào"); return; }
  return startWorkout(id);
}

function showSets() {
  const finished = Boolean(workout.end_time);
  document.getElementById("sets").innerHTML = workout.sets.map(s => {
    let html = '<tr class="' + (s.is_completed ? "done" : "") + '"><td>' + escapeHtml(exerciseName(s.exercise_id)) + '</td><td>' + s.set_number + '</td>';
    for (const field of ["weight", "reps"]) {
      html += finished ? '<td>' + s[field] + '</td>' :
        '<td><input type="number" min="0" step="' + (field === "weight" ? "any" : "1") + '" style="width:70px" value="' + s[field] +
        '" onchange="changeSet(\'' + s.id + '\', \'' + field + '\', this.value)"></td>';
    }
    html += '<td>' + estimate1RM(s.weight, s.reps) + '</td><td>';
    if (!finished) {
      html += '<button onclick="completeSet(\'' + s.id + '\', ' + !s.is_completed + ')">' + (s.is_completed ? "Bỏ" : "Xong") + '</button> ';
      html += '<button class="light" onclick="deleteSet(\'' + s.id + '\')">Xoá</button>';
    }
    return html + '</td></tr>';
  }).join("");
}

async function reload() {
  workout = await callApi("/workouts/" + workout.id);
  rememberWorkout();
  showScreen();
}

function validNumber(value, integer = false) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0 || (integer && !Number.isInteger(number)))
    throw new Error(integer ? "Reps phải là số nguyên không âm" : "Mức tạ phải là số không âm");
  return number;
}

function addSet() {
  const exerciseId = document.getElementById("exerciseSelect").value;
  const weight = document.getElementById("weight").value;
  const reps = document.getElementById("reps").value;
  return workoutAction(async () => {
    requireActive();
    if (!exerciseId) throw new Error("Chọn một bài tập");
    await callApi("/workouts/" + workout.id + "/sets", "POST", {
      exercise_id: exerciseId, weight: validNumber(weight), reps: validNumber(reps, true),
    });
    await reload();
  });
}

function changeSet(setId, field, value) {
  return workoutAction(async () => {
    requireActive();
    try {
      await callApi("/workouts/sets/" + setId, "PUT", {[field]: validNumber(value, field === "reps")});
    } catch (error) { showSets(); throw error; }
    await reload();
  });
}

function completeSet(setId, done) {
  return workoutAction(async () => {
    requireActive();
    await callApi("/workouts/sets/" + setId, "PUT", {is_completed: done});
    await reload();
    if (done && !workout.end_time) startTimer();
  });
}

function deleteSet(setId) {
  return workoutAction(async () => {
    requireActive();
    await callApi("/workouts/sets/" + setId, "DELETE");
    await reload();
  });
}

function startTimer() {
  let seconds = Number(document.getElementById("restSeconds").value) || 60;
  if (!Number.isFinite(seconds) || seconds < 0 || !Number.isInteger(seconds)) {
    showError("Thời gian nghỉ phải là số nguyên không âm");
    return;
  }
  const timerBox = document.getElementById("timer");
  timerBox.style.display = "block";
  clearInterval(timerId);
  timerBox.textContent = "Nghỉ: " + seconds + " giây";
  timerId = setInterval(() => {
    seconds -= 1;
    if (seconds <= 0) {
      clearInterval(timerId);
      timerBox.textContent = "Hết giờ nghỉ, tập set tiếp!";
    } else timerBox.textContent = "Nghỉ: " + seconds + " giây";
  }, 1000);
}

function finishWorkout() {
  return workoutAction(async () => {
    requireActive();
    workout = await callApi("/workouts/" + workout.id + "/finish", "POST");
    rememberWorkout();
    showScreen();
    alert("Xong! Tổng volume: " + workout.total_volume + " kg × reps");
    window.location.href = "history.html";
  });
}

function cancelWorkout() {
  if (!confirm("Huỷ buổi tập này?")) return;
  return workoutAction(async () => {
    requireActive();
    await callApi("/workouts/" + workout.id, "DELETE");
    workout = await callApi("/workouts/active");
    rememberWorkout();
    stopTimer();
    showScreen();
  });
}

workoutQueue = runUiAction(init);
