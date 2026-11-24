"""Builds subs/ps-epNN.<lang>.vtt from subs/data/ps-epNN.json.   Usage: python3 subs/build.py

Each data file: {"episode": N, "status": "needs-translation" | "translated",
                 "cues": [{"s": start_sec, "e": end_sec, "en": "...", "ms": "...", "zh": "...", "ko": "...",
                           "check": "optional note: hard to hear"}]}
A language is only written when every cue has it.
"""
import glob, json, os, re

LANGS = ["en", "ms", "zh", "ko"]
LIMIT = {"en": 44, "ms": 46, "zh": 18, "ko": 22}
HERE = os.path.dirname(os.path.abspath(__file__))

def wrap(t, lang):
    if "\n" in t or len(t) <= LIMIT[lang]:
        return t
    mid = len(t) // 2
    cands = ([m.end() for m in re.finditer(r"[，。！？、：；…]", t[:-1])] or [mid]) if lang == "zh" else [m.start() for m in re.finditer(r" ", t)]
    if not cands:
        return t
    cut = min(cands, key=lambda i: abs(i - mid))
    return (t[:cut].rstrip() + "\n" + t[cut:].lstrip()).strip()

def ts(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"

def build(path):
    d = json.load(open(path, encoding="utf-8"))
    n, cues = d["episode"], d["cues"]
    prev = 0
    for c in cues:
        assert c["s"] < c["e"] and c["s"] >= prev - 0.001, (n, c)
        prev = c["e"]
    written = []
    for lang in LANGS:
        if not cues or not all((c.get(lang) or "").strip() for c in cues):
            continue
        out = ["WEBVTT", ""]
        for i, c in enumerate(cues, 1):
            out += [str(i), f"{ts(c['s'])} --> {ts(c['e'])}", wrap(c[lang].strip(), lang), ""]
        open(os.path.join(HERE, f"ps-ep{n:02d}.{lang}.vtt"), "w", encoding="utf-8").write("\n".join(out))
        written.append(lang)
    return n, written

if __name__ == "__main__":
    for p in sorted(glob.glob(os.path.join(HERE, "data", "ps-ep*.json"))):
        n, langs = build(p)
        print(f"EP{n:02d}: {', '.join(langs) or 'nothing yet'}")
