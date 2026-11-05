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
  googleClientId: "537130988058-m8nk7l7ed010ioh3lbj83vr1vc40hti1.apps.googleusercontent.com",
  episodes: [
    { title: "Episode 1", url: "https://youtube.com/shorts/nPlVttY9neU", plot: "" },
    { title: "Episode 2", url: "https://youtube.com/shorts/exbzsaH_mzE", plot: "" },
    { title: "Episode 3", url: "https://youtube.com/shorts/K53sfH6Mbok", plot: "" },
    { title: "Episode 4", url: "https://youtube.com/shorts/VnYPPxy1yxw", plot: "", release: "2026-11-09" },
    { title: "Episode 5", url: "", plot: "" },
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
