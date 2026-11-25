/* ================================================================
   PLUFFY MINIS — EPISODE SCHEDULE (used by drama.html, pluffyminis.html, videos.html)

   Episodes play only from Cloudflare R2 (videoBase below). An episode is watchable once its file
   (ps-epNN.mp4) is in the Cloudflare folder; until then it shows as SOON. No YouTube links needed.
   release:  the Monday it unlocks on this website ("YYYY-MM-DD", unlocks 8:00 AM Malaysia time).
             Leave it out after the first dated episode and it is set automatically to the Monday
             one week after the previous episode (EP06 = 30 Nov 2026, EP07 = 7 Dec, ...).
             Before that date the episode shows as "WATCH EARLY": people who subscribe to the
             YouTube channel can watch it here straight away.
             Episodes before the first dated one (EP01–03) are free to watch here.
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
  // file is in the bucket; if it isn't there yet, the episode shows as SOON.
  videoBase: "https://pub-defd093bf93442e4b37f513a47e645b2.r2.dev/P.S.%20I%20Think%2C%20I%20Like%20You/",
  videoPattern: "ps-ep{nn}.mp4",
  // Subtitles live in subs/ (ps-epNN.en|ms|zh|ko.vtt). Change this after editing them so phones fetch the new copy.
  subsVersion: "202611250042",
  googleClientId: "537130988058-m8nk7l7ed010ioh3lbj83vr1vc40hti1.apps.googleusercontent.com",
  episodes: [
    { title: "Episode 1", plot: "" },
    { title: "Episode 2", plot: "" },
    { title: "Episode 3", plot: "" },
    { title: "Episode 4", plot: "", release: "2026-11-09" },
    { title: "Episode 5", plot: "", release: "2026-11-23" },
    { title: "Episode 6", plot: "" },
    { title: "Episode 7", plot: "" },
    { title: "Episode 8", plot: "" },
    { title: "Episode 9", plot: "" },
    { title: "Episode 10", plot: "" },
    { title: "Episode 11", plot: "" },
    { title: "Episode 12", plot: "" },
    { title: "Episode 13", plot: "" },
    { title: "Episode 14", plot: "" },
    { title: "Episode 15", plot: "" },
    { title: "Episode 16", plot: "" },
    { title: "Episode 17", plot: "" },
    { title: "Episode 18", plot: "" },
    { title: "Episode 19", plot: "" },
    { title: "Episode 20", plot: "" },
    { title: "Episode 21", plot: "" },
    { title: "Episode 22", plot: "" },
    { title: "Episode 23", plot: "" },
    { title: "Episode 24", plot: "" },
    { title: "Episode 25", plot: "" },
    { title: "Episode 26", plot: "" },
    { title: "Episode 27", plot: "" },
    { title: "Episode 28", plot: "" },
    { title: "Episode 29", plot: "" },
    { title: "Episode 30", plot: "" },
    { title: "Episode 31", plot: "" },
    { title: "Episode 32", plot: "" },
    { title: "Episode 33", plot: "" },
    { title: "Episode 34", plot: "" },
    { title: "Episode 35", plot: "" },
    { title: "Episode 36", plot: "" },
    { title: "Episode 37", plot: "" },
    { title: "Episode 38", plot: "" },
    { title: "Episode 39", plot: "" },
    { title: "Episode 40", plot: "" },
  ],
};

/* ================================================================
   SOUNDTRACK — songs per episode (all from Epidemic Sound), in the order you list them.
   Shown when viewers tap the music button above CC.  by / feat: [name, artist page]
   link: the song's own Epidemic Sound page (the title opens it). Without a link, the title opens
   Epidemic Sound's search for that song + artist.
   ================================================================ */
window.PLUFFY.soundtrack = {
  1: [
    { title: "Shut Your Mouth (and Kiss Me)", link: "https://www.epidemicsound.com/music/tracks/648d695c-02ac-4e99-b59b-52c7a2bc8efb/", by: [["Loving Caliber", "https://www.epidemicsound.com/artists/loving-caliber/"]] },
    { title: "Like It Like That", link: "https://www.epidemicsound.com/music/tracks/f942b50a-f928-46e7-afb3-78fe41186b85/", by: [["Mindme", "https://www.epidemicsound.com/artists/mindme/"]], feat: [["Le June", "https://www.epidemicsound.com/artists/le-june/"]] },
  ],
  2: [
    { title: "A Letter to Buddy", link: "https://www.epidemicsound.com/music/tracks/c00df26c-a8eb-437a-917f-a3a575d00a47/", by: [["Holy See", "https://www.epidemicsound.com/artists/holy-see/"]] },
    { title: "In Love", link: "https://www.epidemicsound.com/music/tracks/6fa0f12c-9285-3148-80c3-e3c629b16ac3/", by: [["Gamma Skies", "https://www.epidemicsound.com/artists/gamma-skies/"]] },
  ],
  3: [
    { title: "Why I Try", link: "https://www.epidemicsound.com/music/tracks/42c886c7-0545-3c98-9e83-9785dd6c8f15/", by: [["Loving Caliber", "https://www.epidemicsound.com/artists/loving-caliber/"]] },
    { title: "Skip the Small Talk", link: "https://www.epidemicsound.com/music/tracks/87fe8bef-def0-457b-9907-788016c7f86d/", by: [["Gamma Skies", "https://www.epidemicsound.com/artists/gamma-skies/"]] },
  ],
  4: [
    { title: "Fire", link: "https://www.epidemicsound.com/music/tracks/ca5077b3-661b-46ab-b0f2-bd7cb12a9b24/", by: [["Tilden Parc", "https://www.epidemicsound.com/artists/tilden-parc/"]] },
    { title: "Life of the Party", link: "https://www.epidemicsound.com/music/tracks/ad98eae7-2705-4190-bdff-b2fe50b455c8/", by: [["Maybe", "https://www.epidemicsound.com/artists/maybe-2/"]] },
    { title: "Number One", link: "https://www.epidemicsound.com/music/tracks/5b7d1e23-e612-37f5-92c4-bf8f923fbc14/", by: [["Romaro", "https://www.epidemicsound.com/artists/romaro/"]], feat: [["Elena Persson", "https://www.epidemicsound.com/artists/elena-persson/"]] },
  ],
  5: [
    { title: "I Do Believe", link: "https://www.epidemicsound.com/music/tracks/6e34314d-2bbf-3115-8d35-31f5ac1c6db6/", by: [["Craig Reever", "https://www.epidemicsound.com/artists/craig-reever/"]], feat: [["Mia Niles", "https://www.epidemicsound.com/artists/mia-niles/"]] },
    { title: "Stay with Me", link: "https://www.epidemicsound.com/music/tracks/34ed1964-6c8c-4bb6-9633-d405f2b55e09/", by: [["IFCHAN", "https://www.epidemicsound.com/artists/ifchan/"], ["SCENE", "https://www.epidemicsound.com/artists/scene/"]] },
  ],
  6: [
    { title: "Bad for You", link: "https://www.epidemicsound.com/music/tracks/73f51609-8331-4e98-a43f-e2ed49241b89/", by: [["Vicki Vox", "https://www.epidemicsound.com/artists/vicki-vox/"]] },
    { title: "Not Gonna Wake Up", link: "https://www.epidemicsound.com/music/tracks/1b4dcdcb-62e9-4d59-9103-f762b718fce6/", by: [["Mindme", "https://www.epidemicsound.com/artists/mindme/"]], feat: [["Mia Pfirrman", "https://www.epidemicsound.com/artists/mia-pfirrman/"]] },
    { title: "Safe and Sound", link: "https://www.epidemicsound.com/music/tracks/ec0a9f93-8587-3314-98fe-f9b9844f323d/", by: [["CLNGR", "https://www.epidemicsound.com/artists/clngr/"]] },
  ],
};

/* ================================================================
   MONDAY RELEASE SCHEDULE — every episode unlocks at 8:00 AM Malaysia time (UTC+8) on its Monday.
   Undated episodes after a dated one get the Monday one week later, so the weekly schedule keeps
   going on its own. Until then, YouTube subscribers can watch early.
   ================================================================ */
(function () {
  const P = window.PLUFFY;
  P.releaseHour = "08:00";
  let prev = null;
  P.episodes.forEach((e) => {
    if (e.release) { prev = e.release; e.releaseAuto = false; return; }
    if (!prev) return;
    const d = new Date(prev + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + 7);
    e.release = prev = d.toISOString().slice(0, 10); e.releaseAuto = true;
  });
  P.releaseAt = (e) => (e && e.release ? new Date(`${e.release}T${P.releaseHour}:00+08:00`).getTime() : 0);
})();

/* ================================================================
   UPLOADED-EPISODE CHECK
   An episode can only be watched once its video file (ps-epNN.mp4) is in the Cloudflare folder.
   Until then it shows as SOON on every page and in the apps.
   Pages call PLUFFY.whenReady(fn): it asks Cloudflare which files exist, sets
   episode.uploaded = true / false, then runs fn. If Cloudflare can't be reached right now, the
   last result this device saw is used, so the episode list doesn't go blank.
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
  const KEY = "pluffy-uploaded-v1", LAST = "pluffy-uploaded-last", MAX_AGE = 5 * 60 * 1000;
  const lastKnown = () => { try { const l = JSON.parse(localStorage.getItem(LAST) || "null"); return Array.isArray(l) ? l : null; } catch (_) { return null; } };
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
    try { sessionStorage.setItem(KEY, JSON.stringify({ t: Date.now(), n, list })); localStorage.setItem(LAST, JSON.stringify(list)); } catch (_) {}
    return list;
  }
  let done = null;
  P.whenReady = (fn) => {
    if (!done) {
      const timeout = new Promise((ok) => setTimeout(() => ok(null), 6000));
      done = Promise.race([check().catch(() => null), timeout]).then((fresh) => {
        P.checked = !!fresh;
        const list = fresh || lastKnown() || [];
        P.episodes.forEach((e, i) => { e.uploaded = !!list[i]; });
        return list;
      });
    }
    done.then(() => fn());
  };
})();
