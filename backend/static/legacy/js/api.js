const API = {
  async request(path, { method = "GET", body = null, auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
      const token = localStorage.getItem("aa_token");
      if (token) headers.Authorization = `Bearer ${token}`;
    }

    const res = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    });

    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }
    if (!res.ok) {
      let msg = `Request failed (${res.status})`;
      if (data && data.detail) {
        if (Array.isArray(data.detail)) {
          const first = data.detail[0] || {};
          const fieldPath = Array.isArray(first.loc) ? first.loc.join(".") : "field";
          msg = `${fieldPath}: ${first.msg || "Invalid value"}`;
        } else if (typeof data.detail === "string") {
          msg = data.detail;
        }
      }
      throw new Error(msg);
    }
    return data;
  },
};
