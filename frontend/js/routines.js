let routines = [];
let editingRoutineId = null;

async function loadRoutines() {
  routines = await callApi("/routines");
  const selected = document.getElementById("routineSelect").value;
  document.getElementById("routineSelect").innerHTML = routines.map(r =>
    '<option value="' + r.id + '">' + escapeHtml(r.name) + '</option>'
  ).join("") || "<option value=''>Chưa có routine</option>";
  if (routines.some(r => r.id === selected)) document.getElementById("routineSelect").value = selected;
  document.getElementById("routineList").innerHTML = routines.length ?
    '<table><thead><tr><th>Tên</th><th>Bài tập theo thứ tự</th><th></th></tr></thead><tbody>' + routines.map(r =>
      '<tr><td>' + escapeHtml(r.name) + '</td><td>' + r.exercises.map(item =>
        escapeHtml(exerciseName(item.exercise_id)) + ' — ' + item.target_sets + ' set'
      ).join('<br>') + '</td><td><button class="light" onclick="editRoutine(\'' + r.id + '\')">Sửa</button> ' +
      '<button class="light" onclick="deleteRoutine(\'' + r.id + '\')">Xoá</button></td></tr>'
    ).join('') + '</tbody></table>' : '<p>Chưa có routine.</p>';
}

function closeRoutineForm() {
  document.getElementById("routineForm").hidden = true;
  editingRoutineId = null;
}

function newRoutine() {
  editingRoutineId = null;
  document.getElementById("routineName").value = "";
  document.getElementById("routineRows").replaceChildren();
  document.getElementById("routineForm").hidden = false;
  addRoutineRow();
}

function editRoutine(id) {
  const routine = routines.find(r => r.id === id);
  if (!routine) return;
  newRoutine();
  editingRoutineId = id;
  document.getElementById("routineName").value = routine.name;
  document.getElementById("routineRows").replaceChildren();
  routine.exercises.forEach(item => addRoutineRow(item));
}

function addRoutineRow(item = {}) {
  const row = document.createElement("tr");
  row.innerHTML = '<td><select required aria-label="Bài tập"></select></td>' +
    '<td><input type="number" min="1" step="1" required aria-label="Số set"></td>' +
    '<td><button type="button" class="light" data-move="up">Lên</button> ' +
    '<button type="button" class="light" data-move="down">Xuống</button> ' +
    '<button type="button" class="light" data-remove>Xoá</button></td>';
  const select = row.querySelector("select");
  exercises.forEach(e => select.add(new Option(e.name, e.id)));
  if (item.exercise_id) select.value = item.exercise_id;
  row.querySelector("input").value = item.target_sets ?? 3;
  row.querySelector('[data-move="up"]').onclick = () => {
    if (row.previousElementSibling) row.parentElement.insertBefore(row, row.previousElementSibling);
  };
  row.querySelector('[data-move="down"]').onclick = () => {
    if (row.nextElementSibling) row.parentElement.insertBefore(row.nextElementSibling, row);
  };
  row.querySelector("[data-remove]").onclick = () => row.remove();
  document.getElementById("routineRows").append(row);
}

async function saveRoutine(event) {
  event.preventDefault();
  const button = document.getElementById("saveRoutineBtn");
  if (button.disabled) return;
  const id = editingRoutineId;
  const body = {
    name: document.getElementById("routineName").value.trim(),
    exercises: Array.from(document.querySelectorAll("#routineRows tr"), row => ({
      exercise_id: row.querySelector("select").value,
      target_sets: Number(row.querySelector("input").value),
    })),
  };
  button.disabled = true;
  await runUiAction(async () => {
    if (!body.name) throw new Error("Tên routine không được để trống");
    if (!body.exercises.length) throw new Error("Chọn ít nhất một bài tập");
    if (new Set(body.exercises.map(e => e.exercise_id)).size !== body.exercises.length)
      throw new Error("Không chọn trùng bài tập trong routine");
    if (body.exercises.some(e => !e.exercise_id || !Number.isInteger(e.target_sets) || e.target_sets <= 0))
      throw new Error("Chọn bài tập hợp lệ và số set nguyên dương");
    await callApi("/routines" + (id ? "/" + id : ""), id ? "PUT" : "POST", body);
    closeRoutineForm();
    await loadRoutines();
  });
  button.disabled = false;
}

function deleteRoutine(id) {
  if (!confirm("Xoá routine này? Các buổi tập đã tạo sẽ được giữ nguyên.")) return;
  return runUiAction(async () => {
    await callApi("/routines/" + id, "DELETE");
    if (editingRoutineId === id) closeRoutineForm();
    await loadRoutines();
  });
}
