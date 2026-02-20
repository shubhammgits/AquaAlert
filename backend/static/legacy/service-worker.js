const CACHE_NAME = "aquaalert-v2";
const ASSETS = [
  "/",
  "/index.html",
  "/login.html",
  "/register.html",
  "/user_dashboard.html",
  "/supervisor_dashboard.html",
  "/worker_dashboard.html",
  "/css/styles.css",
  "/js/api.js",
  "/js/auth.js",
  "/js/camera.js",
  "/js/map.js",
  "/js/validation.js",
  "/js/supervisor.js",
  "/js/worker.js",
  "/manifest.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== location.origin) return;

  // For app shell + static assets, prefer network to pick up updates quickly.
  const isHtml =
    event.request.mode === "navigate" || url.pathname === "/" || url.pathname.endsWith(".html") || url.pathname === "/index.html";
  const isStaticAsset = url.pathname.startsWith("/js/") || url.pathname.startsWith("/css/") || url.pathname === "/manifest.json";

  // Never cache API calls (auth/reports/clusters). Always hit network.
  if (url.pathname.startsWith("/auth") || url.pathname.startsWith("/reports") || url.pathname.startsWith("/clusters")) {
    event.respondWith(fetch(event.request));
    return;
  }

  if (isHtml || isStaticAsset) {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return res;
        })
        .catch(() => caches.match(event.request).then((cached) => cached || caches.match("/")))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((res) => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return res;
        })
        .catch(() => caches.match("/"));
    })
  );
});
