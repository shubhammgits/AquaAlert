const CACHE_NAME = "aquaalert-v1";
const ASSETS = [
  "/",
  "/index.html",
  "/login.html",
  "/register.html",
  "/user_dashboard.html",
  "/supervisor_dashboard.html",
  "/css/styles.css",
  "/js/api.js",
  "/js/auth.js",
  "/js/camera.js",
  "/js/map.js",
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

  // Never cache API calls (auth/reports/clusters). Always hit network.
  if (
    url.pathname.startsWith("/auth") ||
    url.pathname.startsWith("/reports") ||
    url.pathname.startsWith("/clusters")
  ) {
    event.respondWith(fetch(event.request));
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
