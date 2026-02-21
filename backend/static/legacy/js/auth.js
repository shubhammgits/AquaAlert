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

function _decodeJwtPayload(token) {
  try {
    const parts = String(token || "").split(".");
    if (parts.length < 2) return null;
    let b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    while (b64.length % 4) b64 += "=";
    const json = atob(b64);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function ensureSessionFromToken() {
  const token = localStorage.getItem("aa_token");
  if (!token) return;

  const role = localStorage.getItem("aa_role");
  if (role) return;

  const payload = _decodeJwtPayload(token);
  if (payload && payload.role) {
    localStorage.setItem("aa_role", String(payload.role));
  }
}

function getUserRole() {
  ensureSessionFromToken();
  return localStorage.getItem("aa_role") || "";
}

function getUserName() {
  return localStorage.getItem("aa_name") || "";
}

function requireAuthOrRedirect() {
  const token = localStorage.getItem("aa_token");
  if (!token) window.location.href = "/login.html";
  ensureSessionFromToken();
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
    if (data.role === "supervisor") window.location.href = "/supervisor_dashboard.html";
    else if (data.role === "worker") window.location.href = "/worker_dashboard.html";
    else window.location.href = "/user_dashboard.html";
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
    phone: form.phone ? form.phone.value : "",
    district: form.district ? form.district.value : "",
    state: form.state ? form.state.value : "",
    city: form.city ? form.city.value : "",
  };

  try {
    await API.request("/auth/register", { method: "POST", body, auth: false });
    const data = await API.request("/auth/login", {
      method: "POST",
      body: { email: body.email, password: body.password },
      auth: false,
    });
    setSession(data);
    if (data.role === "supervisor") window.location.href = "/supervisor_dashboard.html";
    else if (data.role === "worker") window.location.href = "/worker_dashboard.html";
    else window.location.href = "/user_dashboard.html";
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

function applyRoleHint() {
  const params = new URLSearchParams(window.location.search);
  const hintedRole = (params.get("role") || "").trim();

  const registerForm = document.getElementById("registerForm");
  if (registerForm && hintedRole) {
    const roleSel = registerForm.querySelector("select[name='role']");
    if (roleSel) roleSel.value = hintedRole;
  }

  const loginPageRegisterLink = document.querySelector("a[href='/register.html']");
  if (loginPageRegisterLink && hintedRole) {
    loginPageRegisterLink.setAttribute("href", `/register.html?role=${encodeURIComponent(hintedRole)}`);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  ensureSessionFromToken();

  if ("serviceWorker" in navigator) {
    try {
      navigator.serviceWorker.register("/service-worker.js").then((reg) => {
        try {
          reg.update();
        } catch {
          // ignore
        }
      });
    } catch {
      // ignore
    }
  }

  const loginForm = document.getElementById("loginForm");
  if (loginForm) loginForm.addEventListener("submit", handleLogin);

  const registerForm = document.getElementById("registerForm");
  if (registerForm) registerForm.addEventListener("submit", handleRegister);

  applyRoleHint();
  wireLogout();
});
