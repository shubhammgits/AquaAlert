import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function AuthPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isSignUp, setIsSignUp] = useState(true); 
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "user",
    phone: "",
    city: "",
    district: "",
    state: ""
  });

  const apiBaseUrl =
    import.meta.env.VITE_API_BASE_URL || (window.location.port === "5173" ? "http://127.0.0.1:8000" : "");

  useEffect(() => {
    const roleFromState = location.state?.role;
    if (roleFromState) {
      const normalizedRole =
        roleFromState === "User" ? "user" :
        roleFromState === "Public Source" ? "user" :
        roleFromState === "Field Worker" ? "worker" :
        roleFromState === "Supervisor" ? "supervisor" :
        roleFromState;

      setFormData((current) => ({ ...current, role: normalizedRole }));
      setIsSignUp(true);
    }
  }, [location.state]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const normalized = {
      ...formData,
      name: (formData.name || "").trim(),
      email: (formData.email || "").trim().toLowerCase(),
      password: (formData.password || "").trim(),
      phone: (formData.phone || "").trim(),
      district: (formData.district || "").trim(),
      state: (formData.state || "").trim(),
      city: (formData.city || "").trim(),
    };

    try {
      if (isSignUp) {
        const response = await fetch(`${apiBaseUrl}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(normalized),
        });

        const data = await response.json();
        if (!response.ok) {
          const detail = Array.isArray(data?.detail)
            ? `${(data.detail[0]?.loc || []).join(".")}: ${data.detail[0]?.msg || "Invalid value"}`
            : data?.detail;
          throw new Error(detail || "Registration failed");
        }

        const loginResponse = await fetch(`${apiBaseUrl}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: normalized.email, password: normalized.password }),
        });

        const loginData = await loginResponse.json();
        if (!loginResponse.ok) {
          const detail = Array.isArray(loginData?.detail)
            ? `${(loginData.detail[0]?.loc || []).join(".")}: ${loginData.detail[0]?.msg || "Invalid value"}`
            : loginData?.detail;
          throw new Error(detail || "Login failed after registration");
        }

        localStorage.setItem("aquaalert_token", loginData.access_token);
        localStorage.setItem("aquaalert_role", loginData.role);
        localStorage.setItem("aquaalert_name", loginData.name);
        navigate("/");
        return;
      }

      const response = await fetch(`${apiBaseUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: normalized.email, password: normalized.password }),
      });

      const data = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(data?.detail)
          ? `${(data.detail[0]?.loc || []).join(".")}: ${data.detail[0]?.msg || "Invalid value"}`
          : data?.detail;
        throw new Error(detail || "Login failed");
      }

      localStorage.setItem("aquaalert_token", data.access_token);
      localStorage.setItem("aquaalert_role", data.role);
      localStorage.setItem("aquaalert_name", data.name);
      navigate("/");
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 bg-white dark:bg-slate-950 transition-colors duration-300">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-8 md:p-10 transition-all">
        
        {/* Header Section */}
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            {isSignUp ? "Create Account" : "Aqua Alert"}
          </h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            {isSignUp 
              ? "Provide your details and location to join the network." 
              : "Sign in to access your monitoring dashboard."}
          </p>
        </div>

          {error && (
            <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </div>
          )}

        <form onSubmit={handleAuth} className="grid grid-cols-1 md:grid-cols-6 gap-5">
          
          {/* USER NAME */}
          {isSignUp && (
            <div className="md:col-span-6">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1">User Name</label>
              <input
                type="text" name="name" required
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                placeholder="Full Name" onChange={handleChange}
              />
            </div>
          )}

          {/* EMAIL */}
          <div className={isSignUp ? "md:col-span-3" : "md:col-span-6"}>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1">Email</label>
            <input
              type="email" name="email" required
              className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              placeholder="name@aqua.com" onChange={handleChange}
            />
          </div>

          {/* PHONE NO */}
          {isSignUp && (
            <div className="md:col-span-3">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1">Phone No.</label>
              <input
                type="tel" name="phone" required
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                placeholder="+91..." onChange={handleChange}
              />
            </div>
          )}

          {/* LOCATION SECTION - Only for Register */}
          {isSignUp && (
            <>
              <div className="md:col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1">City</label>
                <input
                  type="text" name="city" required
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  placeholder="e.g. Delhi" onChange={handleChange}
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1">District</label>
                <input
                  type="text" name="district" required
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  placeholder="e.g. Central" onChange={handleChange}
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1">State</label>
                <input
                  type="text" name="state" required
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  placeholder="e.g. Delhi" onChange={handleChange}
                />
              </div>
            </>
          )}

          {/* ROLE & PASSWORD */}
          <div className={isSignUp ? "md:col-span-3" : "md:col-span-6"}>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1">
                {isSignUp ? "Designated Role" : "Password"}
            </label>
            {isSignUp ? (
              <select
                name="role"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all cursor-pointer"
                onChange={handleChange}
                value={formData.role}
              >
                <option value="user">Citizen / User</option>
                <option value="supervisor">Supervisor</option>
                <option value="worker">Field Worker</option>
              </select>
            ) : (
              <input
                type="password" name="password" required minLength={6}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                placeholder="•••••••• (min 6)" onChange={handleChange}
              />
            )}
          </div>

          {isSignUp && (
            <div className="md:col-span-3">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1">Set Password</label>
              <input
                type="password" name="password" required minLength={6}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                placeholder="•••••••• (min 6)" onChange={handleChange}
              />
            </div>
          )}

          {/* SUBMIT BUTTON */}
          <div className="md:col-span-6 mt-4">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl shadow-lg transition-all active:scale-[0.98]"
            >
              {loading ? "Please wait..." : isSignUp ? "Register Account" : "Log In"}
            </button>
          </div>
        </form>

        {/* TOGGLE FOOTER */}
        <div className="mt-8 text-center text-sm">
          <p className="text-slate-500 dark:text-slate-400">
            {isSignUp ? "Already a verified user?" : "New to the system?"}
            <button
              onClick={() => setIsSignUp(!isSignUp)}
              className="ml-2 font-bold text-blue-600 hover:underline transition-colors"
            >
              {isSignUp ? "Log In" : "Register Profile"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}