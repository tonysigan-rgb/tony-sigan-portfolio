/*
 * pluffy minis — episode comments (Cloudflare Worker + D1 database bound as DB)
 *
 * Anyone can comment, guests included. Comments show instantly, with these guards:
 *  - 1–300 characters, name up to 24 (default "Guest"); links and a list of bad words are refused
 *  - one comment per 30 seconds per device, at most 8 a minute per network (IP stored only as a salted hash)
 *  - viewers can report; a comment reported by 3 different viewers is hidden automatically
 *  - a viewer can delete their own comment (device key kept in their browser)
 *  - the owner can delete any comment: set a secret named ADMIN_KEY on this Worker, then send it
 *    in the X-Admin-Key header (the player's admin mode does this; see drama.html ?admin=1)
 *
 * Routes:  GET  /comments?ep=5          list (newest first)
 *          POST /comments               {ep, name, text, me}
 *          POST /comments/:id/like      {me}   (toggle)
 *          POST /comments/:id/report    {me}
 *          POST /comments/:id/delete    {me}   own comment, or X-Admin-Key for any
 */
const ORIGINS = ["https://tonysigan-rgb.github.io", "http://127.0.0.1:8767", "http://localhost:8767"];
const MAX_TEXT = 300, MAX_NAME = 24, WAIT = 30, HIDE_AT = 3;
const BAD = [
  "fuck", "fck", "fuk", "shit", "bitch", "cunt", "dick", "pussy", "asshole", "bastard", "slut", "whore", "nigger", "nigga",
  "faggot", "fag", "retard", "porn", "xxx", "sex video", "onlyfans",
  "babi", "bodoh", "sial", "pukimak", "puki", "kimak", "lancau", "pantat", "sundal", "jalang", "anjing", "bangsat", "kontol", "memek", "ngentot", "goblok",
  "操你", "傻逼", "妈的", "씨발", "병신", "개새끼",
];
const LINK = /(https?:\/\/|www\.|\b[a-z0-9-]+\.(com|net|org|io|me|ly|gg|xyz|link|site|co|my|id|tk|ru|cn)\b|t\.me\/|wa\.me\/|bit\.ly)/i;

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, ep INTEGER NOT NULL, name TEXT NOT NULL, text TEXT NOT NULL,
     ts INTEGER NOT NULL, owner TEXT NOT NULL, iph TEXT NOT NULL, likes INTEGER NOT NULL DEFAULT 0, reports INTEGER NOT NULL DEFAULT 0,
     hidden INTEGER NOT NULL DEFAULT 0)`,
  `CREATE INDEX IF NOT EXISTS comments_ep ON comments (ep, hidden, ts)`,
  `CREATE TABLE IF NOT EXISTS votes (me TEXT NOT NULL, id INTEGER NOT NULL, kind TEXT NOT NULL, PRIMARY KEY (me, id, kind))`,
];
let ready = null;
const setup = (db) => (ready ||= db.batch(SCHEMA.map((s) => db.prepare(s))).catch((e) => { ready = null; throw e; }));

async function sha(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("").slice(0, 32);
}
const clean = (s, max) => String(s || "").replace(/[\u0000-\u0008\u000b-\u001f\u007f​-‏‪-‮]/g, "").replace(/\n{3,}/g, "\n\n").trim().slice(0, max);
const squash = (s) => s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[@4]/g, "a").replace(/[3]/g, "e").replace(/[1!|]/g, "i").replace(/[0]/g, "o").replace(/[$5]/g, "s").replace(/[^a-z\u0080-￿ ]/g, "");
const rude = (s) => { const t = squash(s), w = ` ${t} `; return BAD.some((b) => (/^[a-z ]+$/.test(b) ? w.includes(` ${b} `) || (b.length >= 5 && t.replace(/ /g, "").includes(b.replace(/ /g, ""))) : t.includes(b))); };

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const cors = {
      "Access-Control-Allow-Origin": ORIGINS.includes(origin) ? origin : ORIGINS[0],
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-Admin-Key",
      "Access-Control-Max-Age": "86400",
      "Vary": "Origin",
    };
    const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" } });
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (!env.DB) return json({ error: "Database not connected (add a D1 binding named DB)." }, 500);
    await setup(env.DB);
    const url = new URL(req.url);
    const parts = url.pathname.replace(/\/+$/, "").split("/").filter(Boolean);   // ["comments", id?, action?]
    if (parts[0] !== "comments") return json({ ok: true, service: "pluffy comments" });
    const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};
    const me = clean(body.me, 64);
    const meH = me.length >= 16 ? await sha("me:" + me) : "";
    const admin = !!env.ADMIN_KEY && req.headers.get("X-Admin-Key") === env.ADMIN_KEY;

    if (req.method === "GET" && parts.length === 1) {
      const ep = parseInt(url.searchParams.get("ep"), 10);
      if (!(ep > 0 && ep < 1000)) return json({ error: "ep?" }, 400);
      const mine = url.searchParams.get("me") || "";
      const mineH = mine.length >= 16 ? await sha("me:" + mine) : "";
      const { results } = await env.DB.prepare(
        `SELECT c.id, c.name, c.text, c.ts, c.likes, c.owner = ?2 AS mine,
                EXISTS(SELECT 1 FROM votes v WHERE v.id = c.id AND v.me = ?2 AND v.kind = 'like') AS liked
         FROM comments c WHERE c.ep = ?1 AND c.hidden = 0 ORDER BY c.ts DESC LIMIT 300`).bind(ep, mineH || "-").all();
      const total = await env.DB.prepare(`SELECT COUNT(*) AS n FROM comments WHERE ep = ? AND hidden = 0`).bind(ep).first("n");
      return json({ ep, total, comments: results.map((r) => ({ ...r, mine: !!r.mine, liked: !!r.liked })) });
    }

    if (req.method === "POST" && parts.length === 1) {
      const ep = parseInt(body.ep, 10);
      const text = clean(body.text, MAX_TEXT + 1);
      const name = clean(body.name, MAX_NAME).replace(/\s+/g, " ") || "Guest";
      if (!(ep > 0 && ep < 1000)) return json({ error: "Which episode?" }, 400);
      if (!meH) return json({ error: "Please reload the page and try again." }, 400);
      if (!text) return json({ error: "Write something first." }, 400);
      if (text.length > MAX_TEXT) return json({ error: `Keep it under ${MAX_TEXT} characters.` }, 400);
      if (LINK.test(text) || LINK.test(name)) return json({ error: "Links aren't allowed in comments." }, 400);
      if (rude(text) || rude(name)) return json({ error: "Please keep it friendly — that wording isn't allowed." }, 400);
      const ip = req.headers.get("CF-Connecting-IP") || "0";
      const iph = await sha("ip:" + ip + ":" + (env.SALT || "pluffy"));
      const now = Math.floor(Date.now() / 1000);
      const last = await env.DB.prepare(`SELECT MAX(ts) AS t FROM comments WHERE owner = ? AND ts > ?`).bind(meH, now - WAIT).first("t");
      if (last) return json({ error: `Slow down a little — you can comment again in ${WAIT - (now - last)}s.` }, 429);
      // people on the same Wi-Fi or mobile network share an IP, so the IP limit is looser: 8 a minute
      const burst = await env.DB.prepare(`SELECT COUNT(*) AS n FROM comments WHERE iph = ? AND ts > ?`).bind(iph, now - 60).first("n");
      if (burst >= 8) return json({ error: "Lots of comments from your network right now — try again in a minute." }, 429);
      const dup = await env.DB.prepare(`SELECT 1 FROM comments WHERE owner = ? AND text = ? AND ts > ?`).bind(meH, text, now - 3600).first();
      if (dup) return json({ error: "You already posted that." }, 409);
      const r = await env.DB.prepare(`INSERT INTO comments (ep, name, text, ts, owner, iph) VALUES (?, ?, ?, ?, ?, ?) RETURNING id`).bind(ep, name, text, now, meH, iph).first();
      return json({ ok: true, comment: { id: r.id, name, text, ts: now, likes: 0, mine: true, liked: false } }, 201);
    }

    const id = parseInt(parts[1], 10), action = parts[2];
    if (req.method === "POST" && id > 0 && action) {
      const c = await env.DB.prepare(`SELECT id, owner, likes, reports FROM comments WHERE id = ?`).bind(id).first();
      if (!c) return json({ error: "That comment is gone." }, 404);
      if (action === "delete") {
        if (!admin && (!meH || meH !== c.owner)) return json({ error: "You can only delete your own comments." }, 403);
        await env.DB.batch([env.DB.prepare(`DELETE FROM comments WHERE id = ?`).bind(id), env.DB.prepare(`DELETE FROM votes WHERE id = ?`).bind(id)]);
        return json({ ok: true });
      }
      if (!meH) return json({ error: "Please reload the page and try again." }, 400);
      if (action === "like") {
        const had = await env.DB.prepare(`SELECT 1 FROM votes WHERE me = ? AND id = ? AND kind = 'like'`).bind(meH, id).first();
        await env.DB.batch(had
          ? [env.DB.prepare(`DELETE FROM votes WHERE me = ? AND id = ? AND kind = 'like'`).bind(meH, id), env.DB.prepare(`UPDATE comments SET likes = MAX(0, likes - 1) WHERE id = ?`).bind(id)]
          : [env.DB.prepare(`INSERT INTO votes (me, id, kind) VALUES (?, ?, 'like')`).bind(meH, id), env.DB.prepare(`UPDATE comments SET likes = likes + 1 WHERE id = ?`).bind(id)]);
        return json({ ok: true, liked: !had, likes: Math.max(0, c.likes + (had ? -1 : 1)) });
      }
      if (action === "report") {
        if (meH === c.owner) return json({ ok: true });
        const had = await env.DB.prepare(`SELECT 1 FROM votes WHERE me = ? AND id = ? AND kind = 'report'`).bind(meH, id).first();
        if (!had) await env.DB.batch([
          env.DB.prepare(`INSERT INTO votes (me, id, kind) VALUES (?, ?, 'report')`).bind(meH, id),
          env.DB.prepare(`UPDATE comments SET reports = reports + 1, hidden = CASE WHEN reports + 1 >= ? THEN 1 ELSE hidden END WHERE id = ?`).bind(HIDE_AT, id),
        ]);
        return json({ ok: true });
      }
    }
    return json({ error: "Not found" }, 404);
  },
};
