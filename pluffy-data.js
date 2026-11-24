/* ================================================================
   PLUFFY MINIS — EPISODE SCHEDULE (used by drama.html, pluffyminis.html, videos.html)

   url:      the episode's YouTube link. Empty "" = shows as SOON.
   release:  the Monday it unlocks on this website ("YYYY-MM-DD", unlocks 12:00 AM Malaysia time).
             Before that date the episode shows as "WATCH EARLY" and sends people to
             subscribe on YouTube, where it is already up.
             Leave release out (or in the past) = free to watch here.
   plot:     optional one- or two-line summary.
   ================================================================ */
window.PLUFFY = {
  channel: "https://www.youtube.com/@itsmetslFilms",
  subscribe: "https://www.youtube.com/@itsmetslFilms?sub_confirmation=1",
  handle: "@itsmetslFilms",
  // Google sign-in for "subscribers watch early". Paste your OAuth Client ID here to switch it on
  // (looks like 1234567890-abc123.apps.googleusercontent.com). Empty = only the Subscribe button shows.
  // Google sign-in: checks the viewer's subscription, subscribes them if needed, then plays.
  // Cloudflare R2 video storage (bucket "pluffy-minis", folder "P.S. I Think, I Like You"). Episode N plays /ps-epNN.mp4 from here when that
  // file is in the bucket; if it isn't there yet, the YouTube link plays instead.
  videoBase: "https://pub-defd093bf93442e4b37f513a47e645b2.r2.dev/P.S.%20I%20Think%2C%20I%20Like%20You/",
  videoPattern: "ps-ep{nn}.mp4",
  // Subtitles live in subs/ (ps-epNN.en|ms|zh|ko.vtt). Change this after editing them so phones fetch the new copy.
  subsVersion: "20261124a",
  googleClientId: "537130988058-m8nk7l7ed010ioh3lbj83vr1vc40hti1.apps.googleusercontent.com",
  episodes: [
    { title: "Episode 1", url: "https://youtube.com/shorts/nPlVttY9neU", plot: "" },
    { title: "Episode 2", url: "https://youtube.com/shorts/exbzsaH_mzE", plot: "" },
    { title: "Episode 3", url: "https://youtube.com/shorts/K53sfH6Mbok", plot: "" },
    { title: "Episode 4", url: "https://youtube.com/shorts/VnYPPxy1yxw", plot: "", release: "2026-11-09" },
    { title: "Episode 5", url: "https://youtube.com/shorts/GfihY1PbGyM", plot: "", release: "2026-11-23" },
    { title: "Episode 6", url: "", plot: "" },
    { title: "Episode 7", url: "", plot: "" },
    { title: "Episode 8", url: "", plot: "" },
    { title: "Episode 9", url: "", plot: "" },
    { title: "Episode 10", url: "", plot: "" },
    { title: "Episode 11", url: "", plot: "" },
    { title: "Episode 12", url: "", plot: "" },
    { title: "Episode 13", url: "", plot: "" },
    { title: "Episode 14", url: "", plot: "" },
    { title: "Episode 15", url: "", plot: "" },
    { title: "Episode 16", url: "", plot: "" },
    { title: "Episode 17", url: "", plot: "" },
    { title: "Episode 18", url: "", plot: "" },
    { title: "Episode 19", url: "", plot: "" },
    { title: "Episode 20", url: "", plot: "" },
    { title: "Episode 21", url: "", plot: "" },
    { title: "Episode 22", url: "", plot: "" },
    { title: "Episode 23", url: "", plot: "" },
    { title: "Episode 24", url: "", plot: "" },
    { title: "Episode 25", url: "", plot: "" },
    { title: "Episode 26", url: "", plot: "" },
    { title: "Episode 27", url: "", plot: "" },
    { title: "Episode 28", url: "", plot: "" },
    { title: "Episode 29", url: "", plot: "" },
    { title: "Episode 30", url: "", plot: "" },
    { title: "Episode 31", url: "", plot: "" },
    { title: "Episode 32", url: "", plot: "" },
    { title: "Episode 33", url: "", plot: "" },
    { title: "Episode 34", url: "", plot: "" },
    { title: "Episode 35", url: "", plot: "" },
    { title: "Episode 36", url: "", plot: "" },
    { title: "Episode 37", url: "", plot: "" },
    { title: "Episode 38", url: "", plot: "" },
    { title: "Episode 39", url: "", plot: "" },
    { title: "Episode 40", url: "", plot: "" },
  ],
};

/* ================================================================
   UPLOADED-EPISODE CHECK
   An episode can only be watched once its video file (ps-epNN.mp4) is in the Cloudflare folder.
   Until then it shows as SOON on every page and in the apps, even if it has a YouTube link.
   Pages call PLUFFY.whenReady(fn): it asks Cloudflare which files exist, sets
   episode.uploaded = true / false, then runs fn. If Cloudflare can't be reached, the
   episodes keep their YouTube-link behaviour so the site never goes blank.
   ================================================================ */
(function () {
  const P = window.PLUFFY;
  const base = (P.videoBase || "").replace(/\/?$/, "/");
  P.fileUrl = (i) => {
    const e = P.episodes[i] || {};
    if (e.video === false || !P.videoBase) return "";
    const name = e.video || (P.videoPattern || "").replace("{nn}", String(i + 1).padStart(2, "0"));
    return !name ? "" : /^https?:/.test(name) ? name : base + name;
  };
  // true / false per episode, or null if the check couldn't run
  const KEY = "pluffy-uploaded-v1", MAX_AGE = 5 * 60 * 1000;
  const head = (u) => fetch(u, { method: "HEAD", cache: "no-store", mode: "cors" }).then((r) => r.ok, () => null);
  async function check() {
    try { const c = JSON.parse(sessionStorage.getItem(KEY) || "null"); if (c && Date.now() - c.t < MAX_AGE && c.n === P.episodes.length) return c.list; } catch (_) {}
    const n = P.episodes.length, list = new Array(n).fill(false);
    let misses = 0;
    // check in small groups; stop after 3 missing in a row past the last uploaded file
    for (let i = 0; i < n && misses < 3; i += 3) {
      const idx = [i, i + 1, i + 2].filter((k) => k < n);
      const res = await Promise.all(idx.map((k) => (P.fileUrl(k) ? head(P.fileUrl(k)) : false)));
      if (res.some((r) => r === null)) return null;   // Cloudflare unreachable / blocked
      res.forEach((ok, j) => { list[idx[j]] = ok; misses = ok ? 0 : misses + 1; });
    }
    try { sessionStorage.setItem(KEY, JSON.stringify({ t: Date.now(), n, list })); } catch (_) {}
    return list;
  }
  let done = null;
  P.whenReady = (fn) => {
    if (!done) {
      const timeout = new Promise((ok) => setTimeout(() => ok(null), 6000));
      done = Promise.race([check().catch(() => null), timeout]).then((list) => {
        P.checked = !!list;
        P.episodes.forEach((e, i) => {
          e.uploaded = list ? !!list[i] : null;
          if (list && !list[i]) e.url = "";   // not uploaded -> SOON everywhere
        });
        return list;
      });
    }
    done.then(() => fn());
  };
})();
