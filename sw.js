/* Service worker — Mi Try-Out CVVB 2026-27.
   Sube CACHE a v2, v3... cada vez que cambies index.html,
   asi los telefonos que ya lo instalaron reciben la version nueva. */
var CACHE = "mi-tryout-cvvb-v1";
var ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./logo.png",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png"
];

self.addEventListener("install", function (e) {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return Promise.all(ASSETS.map(function (u) {
        return c.add(u).catch(function () { return null; });
      }));
    })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        return k === CACHE ? null : caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

/* Red primero para el HTML (para que siempre veas horarios frescos),
   cache primero para todo lo demas. */
self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var esHTML = req.mode === "navigate" ||
               (req.headers.get("accept") || "").indexOf("text/html") >= 0;
  if (esHTML) {
    e.respondWith(
      fetch(req).then(function (r) {
        var copia = r.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copia); });
        return r;
      }).catch(function () {
        return caches.match(req).then(function (r) {
          return r || caches.match("./index.html");
        });
      })
    );
    return;
  }
  e.respondWith(
    caches.match(req).then(function (r) {
      return r || fetch(req).then(function (res) {
        var copia = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copia); });
        return res;
      }).catch(function () { return r; });
    })
  );
});
