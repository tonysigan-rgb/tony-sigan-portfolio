"""Builds subs/ps-epNN.<lang>.vtt from source.py.  Usage: python3 subs/build.py"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from source import EP
LANGS = ["en", "ms", "zh", "ko"]
LIMIT = {"en": 44, "ms": 46, "zh": 18, "ko": 22}

def wrap(t, lang):
    if "\n" in t or len(t) <= LIMIT[lang]:
        return t
    mid = len(t) // 2
    if lang == "zh":
        cands = [m.end() for m in re.finditer(r"[，。！？、：；…]", t[:-1])] or [mid]
    else:
        cands = [m.start() for m in re.finditer(r" ", t)]
    if not cands:
        return t
    cut = min(cands, key=lambda i: abs(i - mid))
    return (t[:cut].rstrip() + "\n" + t[cut:].lstrip()).strip()

def ts(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"

here = os.path.dirname(os.path.abspath(__file__))
for n, cues in EP.items():
    prev = 0
    for c in cues:
        assert c[0] < c[1] and c[0] >= prev - 0.001, (n, c)
        prev = c[1]
    for li, lang in enumerate(LANGS):
        out = ["WEBVTT", ""]
        for i, c in enumerate(cues, 1):
            out += [str(i), f"{ts(c[0])} --> {ts(c[1])}", wrap(c[2 + li], lang), ""]
        open(os.path.join(here, f"ps-ep{n:02d}.{lang}.vtt"), "w", encoding="utf-8").write("\n".join(out))
print("built", len(EP), "episodes x", len(LANGS), "languages")
