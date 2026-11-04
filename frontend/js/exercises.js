checkLogin();
showNav();
let exerciseList = [];
let editingExerciseId = null;

async function loadExercises() {
  exerciseList = await callApi("/exercises");
  document.getElementById("list").innerHTML = exerciseList.map(e =>
    "<tr><td>" + escapeHtml(e.name) + "</td><td>" + escapeHtml(e.muscle_group) +
    "</td><td>" + escapeHtml(e.equipment) + "</td><td>" +
    (e.user_id ? '<button class="light" onclick="editExercise(\'' + e.id + '\')">Sửa</button> ' +
      '<button class="light" onclick="deleteExercise(\'' + e.id + '\')">Xoá</button>' : "Mặc định") +
    "</td></tr>"
  ).join("");
}

function resetExerciseForm() {
  editingExerciseId = null;
  document.getElementById("exerciseForm").reset();
  document.getElementById("exerciseFormTitle").textContent = "Thêm bài tập mới";
  document.getElementById("saveExerciseBtn").textContent = "Thêm";
  document.getElementById("cancelEdit").hidden = true;
}

function editExercise(id) {
  const exercise = exerciseList.find(e => e.id === id);
  if (!exercise || !exercise.user_id) return;
  editingExerciseId = id;
  document.getElementById("name").value = exercise.name;
  document.getElementById("muscle").value = exercise.muscle_group || "";
  document.getElementById("equipment").value = exercise.equipment || "";
  document.getElementById("exerciseFormTitle").textContent = "Sửa bài tập";
  document.getElementById("saveExerciseBtn").textContent = "Lưu";
  document.getElementById("cancelEdit").hidden = false;
  document.getElementById("name").focus();
}

async function saveExercise(event) {
  event.preventDefault();
  const button = document.getElementById("saveExerciseBtn");
  if (button.disabled) return;
  const id = editingExerciseId;
  const body = {
    name: document.getElementById("name").value.trim(),
    muscle_group: document.getElementById("muscle").value.trim(),
    equipment: document.getElementById("equipment").value.trim(),
  };
  button.disabled = true;
  await runUiAction(async () => {
    if (!body.name) throw new Error("Tên bài tập không được để trống");
    await callApi("/exercises" + (id ? "/" + id : ""), id ? "PUT" : "POST", body);
    resetExerciseForm();
    await loadExercises();
  });
  button.disabled = false;
}

function deleteExercise(id) {
  if (!confirm("Xoá bài tập riêng này?")) return;
  return runUiAction(async () => {
    await callApi("/exercises/" + id, "DELETE");
    if (editingExerciseId === id) resetExerciseForm();
    await loadExercises();
  });
}

runUiAction(loadExercises);
