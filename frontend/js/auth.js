function setSession({ access_token, role, name }) {
  localStorage.setItem("aa_token", access_token);
  localStorage.setItem("aa_role", role);
  localStorage.setItem("aa_name", name);
}

function clearSession() {
  localStorage.removeItem("aa_token");
  localStorage.removeItem("aa_role");
  localStorage.removeItem("aa_name");
}

function getUserRole() {
  return localStorage.getItem("aa_role") || "";
}

function getUserName() {
  return localStorage.getItem("aa_name") || "";
}

function requireAuthOrRedirect() {
  const token = localStorage.getItem("aa_token");
  if (!token) window.location.href = "/login.html";
}

async function handleLogin(e) {
  e.preventDefault();
  const msg = document.getElementById("loginMsg");
  msg.textContent = "";
  const form = e.target;
  const email = form.email.value;
  const password = form.password.value;

  try {
    const data = await API.request("/auth/login", { method: "POST", body: { email, password }, auth: false });
    setSession(data);
    window.location.href = data.role === "supervisor" ? "/supervisor_dashboard.html" : "/user_dashboard.html";
  } catch (err) {
    msg.textContent = err.message;
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const msg = document.getElementById("registerMsg");
  msg.textContent = "";

  const form = e.target;
  const body = {
    name: form.name.value,
    email: form.email.value,
    password: form.password.value,
    role: form.role.value,
  };

  try {
    await API.request("/auth/register", { method: "POST", body, auth: false });
    const data = await API.request("/auth/login", {
      method: "POST",
      body: { email: body.email, password: body.password },
      auth: false,
    });
    setSession(data);
    window.location.href = data.role === "supervisor" ? "/supervisor_dashboard.html" : "/user_dashboard.html";
  } catch (err) {
    msg.textContent = err.message;
  }
}

function wireLogout() {
  const btn = document.getElementById("logoutBtn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    clearSession();
    window.location.href = "/login.html";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  if (loginForm) loginForm.addEventListener("submit", handleLogin);

  const registerForm = document.getElementById("registerForm");
  if (registerForm) registerForm.addEventListener("submit", handleRegister);

  wireLogout();
});
