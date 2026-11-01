// Hàm gọi API dùng chung (tự gắn token)
const API_URL = "http://localhost:8000";

async function callApi(path, method, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }

  const response = await fetch(API_URL + path, {
    method: method || "GET",
    headers: headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await response.json();
  if (!response.ok) {
    // nếu token hết hạn thì đăng nhập lại
    if (response.status === 401 || response.status === 403) {
      if (token) logout();
    }
    throw new Error(data.detail || "Có lỗi xảy ra");
  }
  return data;
}