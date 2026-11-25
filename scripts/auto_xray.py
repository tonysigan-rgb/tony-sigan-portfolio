"""Actor X-Ray (runs in GitHub Actions with the auto-subtitles job).

For every uploaded ps-epNN.mp4 on Cloudflare:
  1. find every face once a second (OpenCV YuNet) and remember its face-print (SFace), cached in
     subs/xray/faces-epNN.json so a video is only downloaded once;
  2. learn each character from the seed frames in subs/cast.json, then grow those references with
     faces it is very sure about (self-training);
  3. name the faces in every episode -- only when the match is clear (similarity >= 0.60 and well
     ahead of the next-best character), otherwise leave it unnamed -- and write
     subs/xray/ps-epNN.json: {"on": {key: [[start, end], ...]}, "cast": [keys by screen time]};
  4. cut a 320x320 portrait for each character from its portrait frame into assets/cast/<key>.jpg.

Everything is redone from the cache when cast.json changes (new seed, new character), so fixing a
wrong name is: add a seed frame for the right character in cast.json and push.
Local test: VIDEO_DIR=/path/with/ep01.mp4... python scripts/auto_xray.py
"""
import base64, hashlib, json, os, re, sys, tempfile, urllib.request

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XR = os.path.join(ROOT, "subs", "xray")
CAST_DIR = os.path.join(ROOT, "assets", "cast")
CAST_FILE = os.path.join(ROOT, "subs", "cast.json")
UA = {"User-Agent": "Mozilla/5.0 (pluffy-auto-xray)"}
MODELS = os.path.expanduser(os.environ.get("XRAY_MODELS", "~/.cache/pluffy-xray"))
ZOO = "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/"
DET = ("face_detection_yunet/face_detection_yunet_2023mar.onnx")
REC = ("face_recognition_sface/face_recognition_sface_2021dec.onnx")
ACCEPT, MARGIN = 0.60, 0.15          # naming a face on screen
GROW, GROW_MARGIN = 0.62, 0.12       # adding a face to the references (big, sharp faces only)
GAP = 3.0                            # join appearances less than 3 s apart into one stretch


def config():
    js = open(os.path.join(ROOT, "pluffy-data.js"), encoding="utf-8").read()
    base = re.search(r'videoBase:\s*"([^"]+)"', js).group(1).rstrip("/") + "/"
    pattern = re.search(r'videoPattern:\s*"([^"]+)"', js).group(1)
    total = len(re.findall(r'\{\s*title:\s*"Episode \d+"', js))
    return base, pattern, total


def model(rel):
    os.makedirs(MODELS, exist_ok=True)
    p = os.path.join(MODELS, os.path.basename(rel))
    if not os.path.exists(p) or os.path.getsize(p) < 100000:
        urllib.request.urlretrieve(ZOO + rel, p)
    return p


def exists(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=30).status == 200
    except Exception:
        return False


def fetch(url, dest):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(dest, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)


def pack(e):
    return base64.b64encode(np.clip(np.round(e * 400), -127, 127).astype(np.int8).tobytes()).decode()


def unpack(s):
    e = np.frombuffer(base64.b64decode(s), dtype=np.int8).astype(np.float32)
    return e / (np.linalg.norm(e) or 1)


class Faces:
    def __init__(self):
        self.det = cv2.FaceDetectorYN.create(model(DET), "", (320, 320), 0.85, 0.3, 5000)
        self.rec = cv2.FaceRecognizerSF.create(model(REC), "")

    def detect(self, frame):
        """faces in a frame: list of (cx, cy, h, score, embedding, box) with cx/cy/h as 0-1 of the frame"""
        h, w = frame.shape[:2]
        sc = 640 / max(h, w)
        small = cv2.resize(frame, (int(w * sc), int(h * sc)))
        self.det.setInputSize((small.shape[1], small.shape[0]))
        _, found = self.det.detect(small)
        out = []
        for f in (found if found is not None else []):
            x, y, fw, fh = f[:4]
            if fh < 28:
                continue
            e = self.rec.feature(self.rec.alignCrop(small, f)).flatten()
            e = e / (np.linalg.norm(e) or 1)
            out.append(((x + fw / 2) / small.shape[1], (y + fh / 2) / small.shape[0], fh / small.shape[0],
                        float(f[-1]), e, (x / sc, y / sc, fw / sc, fh / sc)))
        return out


def scan(path, faces):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    rows, t = [], 0.0
    while t < dur:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok:
            break
        for cx, cy, h, s, e, _ in faces.detect(fr):
            rows.append([round(t, 1), round(float(cx), 3), round(float(cy), 3), round(float(h), 3), round(float(s), 3), pack(e)])
        t += 1.0
    cap.release()
    return {"v": 1, "dur": round(dur, 2), "faces": rows}


def frame_at(path, t):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, fr = cap.read()
    cap.release()
    return fr if ok else None


def portrait(path, spec, faces, dest):
    _, t, cx, cy = spec
    fr = frame_at(path, t)
    if fr is None:
        return False
    found = faces.detect(fr)
    H, W = fr.shape[:2]
    if found:
        f = min(found, key=lambda f: (f[0] - cx) ** 2 + (f[1] - cy) ** 2)
        x, y, fw, fh = f[5]
        mx, my, s = x + fw / 2, y + fh / 2, max(fw, fh) * 2.0
    else:
        mx, my, s = cx * W, cy * H, min(W, H) * 0.45
    s = min(s, W, H)
    x0 = int(min(max(0, mx - s / 2), W - s))
    y0 = int(min(max(0, my - s * 0.45), H - s))
    crop = cv2.resize(fr[y0:y0 + int(s), x0:x0 + int(s)], (320, 320), interpolation=cv2.INTER_AREA)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    cv2.imwrite(dest, crop, [cv2.IMWRITE_JPEG_QUALITY, 86])
    return True


def main():
    base, pattern, total = config()
    cast = json.load(open(CAST_FILE, encoding="utf-8"))["cast"]
    keys = [c["key"] for c in cast]
    os.makedirs(XR, exist_ok=True)
    state_p = os.path.join(XR, "state.json")
    state = json.load(open(state_p)) if os.path.exists(state_p) else {}
    cast_hash = hashlib.sha1(open(CAST_FILE, "rb").read()).hexdigest()[:12]
    local = os.environ.get("VIDEO_DIR")
    faces = None
    cache = {}
    with tempfile.TemporaryDirectory() as tmp:
        def video(n):
            if local:
                p = os.path.join(local, f"ep{n:02d}.mp4")
                return p if os.path.exists(p) else None
            p = os.path.join(tmp, f"ep{n:02d}.mp4")
            if not os.path.exists(p):
                url = base + pattern.replace("{nn}", f"{n:02d}")
                if not exists(url):
                    return None
                print("downloading", n, flush=True)
                fetch(url, p)
            return p

        # 1. face cache for every uploaded episode
        new, misses = [], 0
        for n in range(1, total + 1):
            fp = os.path.join(XR, f"faces-ep{n:02d}.json")
            if os.path.exists(fp):
                cache[n] = json.load(open(fp)); misses = 0
                continue
            url = base + pattern.replace("{nn}", f"{n:02d}")
            if not local and not exists(url):
                misses += 1
                if misses >= 3:      # episodes go up in order; stop after three missing in a row
                    break
                continue
            misses = 0
            p = video(n)
            if not p:
                continue
            faces = faces or Faces()
            print("scanning faces in episode", n, flush=True)
            cache[n] = scan(p, faces)
            json.dump(cache[n], open(fp, "w"), separators=(",", ":"))
            new.append(n)
        if not cache:
            print("no episodes yet"); return
        if not new and state.get("cast") == cast_hash and all(os.path.exists(os.path.join(CAST_DIR, k + ".jpg")) for k in keys):
            print("X-Ray up to date"); return

        # 2. references from the seed frames, then self-training
        F = []   # (ep, t, cx, cy, h, score, emb)
        for n, d in cache.items():
            for t, cx, cy, h, s, e in d["faces"]:
                F.append((n, t, cx, cy, h, s, unpack(e)))
        E = np.stack([f[6] for f in F]) if F else np.zeros((0, 128))
        refs = {k: [] for k in keys}
        for c in cast:
            for ep, t, cx, cy in c.get("seeds", []) + [c["portrait"]]:
                cand = [i for i, f in enumerate(F) if f[0] == ep and abs(f[1] - t) < 0.6]
                if not cand:
                    continue
                i = min(cand, key=lambda i: (F[i][2] - cx) ** 2 + (F[i][3] - cy) ** 2)
                if (F[i][2] - cx) ** 2 + (F[i][3] - cy) ** 2 < 0.15 ** 2 and i not in refs[c["key"]]:
                    refs[c["key"]].append(i)
        print("seed faces found:", {k: len(v) for k, v in refs.items()})

        def classify(rows):
            best = np.full((len(rows), len(keys)), -1.0)
            for j, k in enumerate(keys):
                if refs[k]:
                    sims = E[rows] @ E[refs[k]].T
                    top = np.sort(sims, axis=1)[:, ::-1][:, :3]
                    best[:, j] = top.mean(axis=1)
            order = np.argsort(-best, axis=1)
            s1 = best[np.arange(len(rows)), order[:, 0]]
            s2 = best[np.arange(len(rows)), order[:, 1]] if len(keys) > 1 else np.zeros(len(rows))
            return order[:, 0], s1, s1 - s2

        allrows = np.arange(len(F))
        used = {i for v in refs.values() for i in v}
        for rnd in range(3):
            pool = np.array([i for i in allrows if i not in used and F[i][5] >= 0.9 and F[i][4] >= 0.075], dtype=int)
            if not len(pool):
                break
            who, s, m = classify(pool)
            ok = (s > GROW) & (m > GROW_MARGIN)
            for i, j in zip(pool[ok], who[ok]):
                refs[keys[j]].append(int(i)); used.add(int(i))
            print("self-training round", rnd, "added", int(ok.sum()), flush=True)

        # 3. who is on screen, per episode
        who, s, m = classify(allrows) if len(F) else ([], [], [])
        for n, d in cache.items():
            times = {k: [] for k in keys}
            for i, f in enumerate(F):
                if f[0] == n and s[i] >= ACCEPT and m[i] >= MARGIN:
                    times[keys[who[i]]].append(f[1])
            on, screen = {}, {}
            for k, ts in times.items():
                ts = sorted(set(ts))
                if len(ts) < 2:          # a single one-second glimpse is too unreliable to show
                    continue
                spans = []
                for t in ts:
                    if spans and t - spans[-1][1] <= GAP:
                        spans[-1][1] = t
                    else:
                        spans.append([t, t])
                spans = [[max(0, round(a - 0.5, 1)), round(min(d["dur"], b + 1.0), 1)] for a, b in spans]
                on[k] = spans
                screen[k] = sum(b - a for a, b in spans)
            order = sorted(screen, key=lambda k: -screen[k])
            json.dump({"v": 1, "on": on, "cast": order}, open(os.path.join(XR, f"ps-ep{n:02d}.json"), "w"), separators=(",", ":"))
            print(f"EP{n:02d}:", {k: round(screen[k]) for k in order})

        # 4. portraits
        faces = faces or Faces()
        for c in cast:
            dest = os.path.join(CAST_DIR, c["key"] + ".jpg")
            sig = json.dumps(c["portrait"])
            if os.path.exists(dest) and state.get("portraits", {}).get(c["key"]) == sig:
                continue
            p = video(int(c["portrait"][0]))
            if p and portrait(p, c["portrait"], faces, dest):
                state.setdefault("portraits", {})[c["key"]] = sig
                print("portrait", c["key"])
        state["cast"] = cast_hash
        json.dump(state, open(state_p, "w"), indent=1)


if __name__ == "__main__":
    main()
