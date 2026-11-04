// Hàm gọi API dùng chung (tự gắn token)
const API_URL = "http://localhost:8000";

async function callApi(path, method, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }

  let response;
  try {
    response = await fetch(API_URL + path, {
      method: method || "GET",
      headers: headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (_) {
    throw new Error("Không kết nối được API. Hãy kiểm tra máy chủ và thử lại.");
  }

  const text = await response.text();
  let data;
  let validJson = true;
  try { data = text ? JSON.parse(text) : null; }
  catch (_) { data = null; validJson = false; }
  if (!response.ok) {
    // nếu token hết hạn thì đăng nhập lại
    if (response.status === 401) {
      if (token) logout();
    }
    const error = new Error(apiErrorMessage(data && data.detail, response.status));
    error.status = response.status;
    throw error;
  }
  if (!validJson) throw new Error("API trả về dữ liệu không hợp lệ");
  return data;
}

function apiErrorMessage(detail, status) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map(item => {
      const field = Array.isArray(item.loc) ? item.loc.filter(x => x !== "body").join(".") : "";
      return (field ? field + ": " : "") + (typeof item.msg === "string" ? item.msg : "Giá trị không hợp lệ");
    }).join("; ");
  }
  return status === 403 ? "Bạn không có quyền thực hiện thao tác này" : "Yêu cầu thất bại (" + status + ")";
}