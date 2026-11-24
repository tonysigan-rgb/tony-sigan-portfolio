"""Auto-subtitles, step 1 (runs hourly in GitHub Actions).

Looks in the Cloudflare R2 folder for ps-epNN.mp4 files that have no subs/data/ps-epNN.json yet,
transcribes their English dialogue with Whisper (word timings), and writes:
  subs/data/ps-epNN.json   status "needs-translation", English only
  subs/ps-epNN.en.vtt      (via subs/build.py)
A scheduled Claude task then adds the Malay/Indonesian, Mandarin and Korean lines.
"""
import json, os, re, subprocess, sys, tempfile, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "subs", "data")
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "3"))
NAMES = "Theo, Raymond, Owen, Lizzie."
PROMPT = NAMES + " A slow-burn college romance: letters to crushes, the academic rival, the track and field king."
# Phrases Whisper sometimes invents over music or silence
JUNK = re.compile(r"^(thanks for watching|thank you for watching|please subscribe|subscribe|like and subscribe|bye\.?)[.!]*$", re.I)


def config():
    js = open(os.path.join(ROOT, "pluffy-data.js"), encoding="utf-8").read()
    base = re.search(r'videoBase:\s*"([^"]+)"', js).group(1)
    pattern = re.search(r'videoPattern:\s*"([^"]+)"', js).group(1)
    total = len(re.findall(r'\{\s*title:\s*"Episode \d+"', js))
    return base.rstrip("/") + "/", pattern, total


def exists(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (pluffy-auto-subs)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def load_audio(path):
    """MP4 -> 16 kHz mono float32 samples for Whisper (uses PyAV, which faster-whisper installs)."""
    import av, numpy as np
    out = []
    with av.open(path) as box:
        res = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)
        for frame in box.decode(audio=0):
            for f in res.resample(frame) or []:
                out.append(f.to_ndarray().reshape(-1))
        for f in res.resample(None) or []:
            out.append(f.to_ndarray().reshape(-1))
    return (np.concatenate(out).astype(np.float32) / 32768.0) if out else np.zeros(0, np.float32)


def cues_from(segments):
    """Turn Whisper segments into readable subtitle cues (sentences, <= ~2 short lines, timed to the words)."""
    words = []
    for s in segments:
        if JUNK.match(s.text.strip()):
            continue
        for w in s.words or []:
            words.append([w.start, min(w.end, w.start + 1.0), w.word, w.probability])
    cues, cur = [], []

    def flush():
        if not cur:
            return
        text = "".join(w[2] for w in cur).strip()
        low = [w[2].strip() for w in cur if w[3] < 0.6]
        # a first word stranded far before the rest (Whisper timing slip): start at the second word
        start = cur[0][0]
        if len(cur) > 1 and cur[1][0] - cur[0][1] > 2.0:
            start = cur[1][0] - 0.3
        c = {"s": round(start, 2), "e": round(cur[-1][1] + 0.25, 2), "en": text}
        if low:
            c["check"] = "unclear word(s): " + ", ".join(low)
        cues.append(c)
        cur.clear()

    for w in words:
        if cur:
            gap = w[0] - cur[-1][1]
            text = "".join(x[2] for x in cur).strip()
            sentence_end = re.search(r"[.?!…]$", text)
            pause_ok = re.search(r"[,;:]$", text)
            if len(text) + len(w[2]) > 84 and not sentence_end:
                # too long for two lines: break after the last comma if there is one
                cut = max((i for i, x in enumerate(cur[:-1]) if re.search(r"[,;:]$", x[2].strip())), default=None)
                if cut is not None:
                    rest = cur[cut + 1:]; del cur[cut + 1:]; flush(); cur.extend(rest)
                    text = "".join(x[2] for x in cur).strip()
            tiny = sentence_end and len(text) <= 5 and gap < 0.4   # "Ah!", "Oh." stay with the next line
            if (sentence_end and not tiny) or len(text) + len(w[2]) > 84 or gap > 2.5 or (gap > 0.8 and pause_ok):
                # a lone word cut off from the rest of its sentence by a long gap joins the next cue
                if len(cur) == 1 and not sentence_end and not pause_ok and gap > 2.0:
                    cur.append(w)
                    continue
                flush()
        cur.append(w)
    flush()
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["s"] if i + 1 < len(cues) else c["e"] + 5
        c["e"] = round(min(max(c["e"], c["s"] + 1.0), nxt - 0.04), 2)
    return cues


def main():
    base, pattern, total = config()
    test = os.environ.get("TEST_EPISODE")   # test run: transcribe this episode, print it, change nothing
    todo = []
    for n in ([int(test)] if test else range(1, total + 1)):
        if not test and os.path.exists(os.path.join(DATA, f"ps-ep{n:02d}.json")):
            continue
        url = base + pattern.replace("{nn}", f"{n:02d}")
        if exists(url):
            todo.append((n, url))
        if len(todo) >= MAX_PER_RUN:
            break
    if not todo:
        print("No new episodes without subtitles.")
        return 0
    from faster_whisper import WhisperModel
    model = WhisperModel(os.environ.get("WHISPER_MODEL", "large-v3"), device="cpu", compute_type="int8")
    os.makedirs(DATA, exist_ok=True)
    for n, url in todo:
        print(f"EP{n:02d}: downloading {url}", flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            mp4 = os.path.join(tmp, "ep.mp4")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pluffy-auto-subs)"})
            with urllib.request.urlopen(req, timeout=300) as r, open(mp4, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            audio = load_audio(mp4)
            segs, info = model.transcribe(audio, beam_size=5, vad_filter=True, vad_parameters={"min_silence_duration_ms": 400},
                                          word_timestamps=True, condition_on_previous_text=False, initial_prompt=PROMPT)
            segs = list(segs)
        cues = cues_from(segs)
        if test:
            print(f"TEST EP{n:02d} ({info.language}):")
            for c in cues:
                print(f"  {c['s']:7.2f} {c['e']:7.2f}  {c['en']}" + (f"   [{c['check']}]" if "check" in c else ""))
            continue
        out = {"episode": n, "status": "needs-translation", "language": info.language,
               "source": "whisper " + os.environ.get("WHISPER_MODEL", "large-v3") + " (automatic)", "cues": cues}
        json.dump(out, open(os.path.join(DATA, f"ps-ep{n:02d}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"EP{n:02d}: {len(cues)} lines, language {info.language}", flush=True)
    if not test:
        subprocess.run([sys.executable, os.path.join(ROOT, "subs", "build.py")], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
