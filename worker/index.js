export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const allowed = new Set([
      "/all.txt",
      "/top100.txt",
      "/fast.txt",
      "/vless.txt",
      "/vmess.txt",
      "/trojan.txt",
      "/ss.txt",
      "/configs.json",
      "/sources.json",
      "/subscription.b64",
    ]);

    if (!allowed.has(url.pathname)) {
      return new Response("Not found", { status: 404 });
    }

    if (!env.ORIGIN) {
      return new Response("ORIGIN is not configured", { status: 500 });
    }

    const target = new URL(url.pathname + url.search, env.ORIGIN);
    const cache = caches.default;
    const cacheKey = new Request(target.toString(), request);

    let response = await cache.match(cacheKey);
    if (response) {
      return response;
    }

    response = await fetch(target.toString(), {
      headers: {
        "User-Agent": "proxy-aggregator-worker/1.0",
      },
    });

    response = new Response(response.body, response);
    response.headers.set("Cache-Control", "public, max-age=300");

    ctx.waitUntil(cache.put(cacheKey, response.clone()));
    return response;
  },
};
