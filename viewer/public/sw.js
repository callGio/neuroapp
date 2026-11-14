/* Gyrafold service worker: offline support.
 *
 * BUMP VERSION on every deploy that changes any file in SHELL below (pages,
 * content JSON, atlas-manifest.json, icons, fonts, three.js). A new VERSION
 * makes browsers fetch a fresh copy of the shell and delete the old shell
 * caches. The 3D models live in MODELS_CACHE, which is NOT tied to VERSION,
 * so returning visitors never download the ~54 MB of models twice. Change
 * MODELS_CACHE only if the .glb files themselves change.
 *
 * Same-origin GET requests only. Nothing here talks to any other host.
 */
const VERSION = "2026-11-13.1";
const SHELL_CACHE = "gyrafold-shell-" + VERSION;
const RUNTIME_CACHE = "gyrafold-runtime-" + VERSION;
const MODELS_CACHE = "gyrafold-models-v1"; // also named in atlas-viewer.html
const NAV_TIMEOUT_MS = 3000;

const SHELL = [
  "./index.html",
  "./atlas-viewer.html",
  "./neuron.html",
  "./imaging.html",
  "./privacy.html",
  "./manifest.webmanifest",
  "./assets/favicon.svg",
  "./assets/brain-lateral.webp",
  "./assets/icons/icon-192.png",
  "./assets/icons/icon-512.png",
  "./assets/icons/maskable-192.png",
  "./assets/icons/maskable-512.png",
  "./assets/icons/apple-touch-icon-180.png",
  "./vendor/fonts/inter-var.woff2",
  "./vendor/fonts/space-grotesk-var.woff2",
  "./vendor/three/build/three.module.js",
  "./vendor/three/examples/jsm/loaders/GLTFLoader.js",
  "./vendor/three/examples/jsm/controls/OrbitControls.js",
  "./vendor/three/examples/jsm/utils/BufferGeometryUtils.js",
  "./content/learning.json",
  "./content/neuron.json",
  "./content/imaging.json",
  "./atlas-manifest.json"
];

// A redirected response cannot answer a navigation, so store a clean copy.
function clean(res) {
  if (!res.redirected) return Promise.resolve(res);
  return res.blob().then(body => new Response(body, {
    status: res.status, statusText: res.statusText, headers: res.headers
  }));
}

function cacheable(res) {
  return res && res.status === 200 && res.type === "basic";
}

function noSearch(url) {
  const u = new URL(url);
  u.search = "";
  u.hash = "";
  return u.href;
}

// Install: fetch the whole shell first, then store it. If any file fails, the
// install fails loudly and the previous worker (and its cache) stays in charge.
self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const fetched = await Promise.all(SHELL.map(async url => {
      const res = await fetch(new Request(url, { cache: "reload" }));
      if (!res.ok) throw new Error("Gyrafold precache failed: " + url + " (HTTP " + res.status + ")");
      return [url, await clean(res)];
    }));
    const cache = await caches.open(SHELL_CACHE);
    await Promise.all(fetched.map(([url, res]) => cache.put(url, res)));
    // The new shell is complete, so take over now: pages and their assets
    // then always come from the same version.
    await self.skipWaiting();
  })());
});

// Activate: drop caches from older versions, keep the models cache.
self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const keep = new Set([SHELL_CACHE, RUNTIME_CACHE, MODELS_CACHE]);
    const names = await caches.keys();
    await Promise.all(names
      .filter(n => n.startsWith("gyrafold-") && !keep.has(n))
      .map(n => caches.delete(n)));
    await self.clients.claim();
  })());
});

// A page may ask a waiting worker to take over now.
self.addEventListener("message", event => {
  if (event.data === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (req.headers.has("range")) return; // let the network handle partial requests

  if (req.mode === "navigate") {
    event.respondWith(networkFirst(event));
  } else if (url.pathname.endsWith(".glb")) {
    event.respondWith(cacheFirst(event, MODELS_CACHE));
  } else if (url.pathname.endsWith(".json") || url.pathname.endsWith(".webmanifest")) {
    event.respondWith(staleWhileRevalidate(event));
  } else {
    event.respondWith(cacheFirst(event, RUNTIME_CACHE));
  }
});

// Pages: try the network for up to NAV_TIMEOUT_MS so deploys show up at once;
// fall back to the cached page (query strings ignored), then to index.html.
async function networkFirst(event) {
  const req = event.request;
  // The fresh page is returned at once; saving a copy happens on the side and
  // can never fail the page load.
  const network = fetch(req).then(res => {
    if (cacheable(res)) {
      const copy = res.clone();
      event.waitUntil(clean(copy)
        .then(c => caches.open(SHELL_CACHE).then(cache => cache.put(noSearch(req.url), c)))
        .catch(() => {}));
    }
    return res;
  });
  event.waitUntil(network.catch(() => {}));

  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error("timeout")), NAV_TIMEOUT_MS);
  });
  try {
    return await Promise.race([network, timeout]);
  } catch (e) {
    const cached = await caches.match(req, { ignoreSearch: true });
    if (cached) return cached;
    try {
      return await network; // slow but alive: keep waiting
    } catch (e2) {
      const home = await caches.match("./index.html");
      if (home) return home;
      return new Response("Gyrafold is offline and this page is not saved yet.", {
        status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" }
      });
    }
  } finally {
    clearTimeout(timer);
  }
}

// Fonts, scripts, images, icons, models: cached copy first, else network
// (and keep a copy).
async function cacheFirst(event, cacheName) {
  const req = event.request;
  const cached = cacheName === MODELS_CACHE
    ? await (await caches.open(MODELS_CACHE)).match(req)
    : await caches.match(req);
  if (cached) return cached;
  const res = await fetch(req);
  if (cacheable(res)) {
    const copy = res.clone();
    event.waitUntil(caches.open(cacheName).then(c => c.put(req, copy)).catch(() => {}));
  }
  return res;
}

// Lesson JSON and the manifest: answer from cache at once, refresh in the
// background for next time.
async function staleWhileRevalidate(event) {
  const req = event.request;
  const key = noSearch(req.url);
  const cached = await caches.match(key);
  const network = fetch(req).then(res => {
    if (cacheable(res)) {
      const copy = res.clone();
      event.waitUntil(caches.open(SHELL_CACHE).then(cache => cache.put(key, copy)).catch(() => {}));
    }
    return res;
  });
  if (cached) {
    event.waitUntil(network.catch(() => {}));
    return cached;
  }
  return network;
}
