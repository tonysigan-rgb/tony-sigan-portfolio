"""Episode thumbnails (runs in GitHub Actions with the auto-subtitles job).

For every ps-epNN.mp4 in the Cloudflare folder without assets/thumbs/ps-epNN.jpg, pick a striking frame
and save a 360x640 JPEG: from the middle of the episode (after the opening titles and name captions),
preferring frames with clear faces, then sharp, well lit and colourful, and never the same shot as another
episode's thumbnail (scenes replayed in later episodes). An episode can name its exact frame with
thumbAt: seconds in pluffy-data.js. Run with FORCE=1 to remake all.
"""
import io, os, re, sys, tempfile, urllib.request

import av
import numpy as np
from PIL import Image
try:
    import cv2
    FACES = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
except Exception:          # face detection is a bonus; without OpenCV the picker still works
    cv2 = FACES = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "thumbs")
UA = {"User-Agent": "Mozilla/5.0 (pluffy-auto-thumbs)"}


def config():
    js = open(os.path.join(ROOT, "pluffy-data.js"), encoding="utf-8").read()
    base = re.search(r'videoBase:\s*"([^"]+)"', js).group(1).rstrip("/") + "/"
    pattern = re.search(r'videoPattern:\s*"([^"]+)"', js).group(1)
    eps = re.findall(r'\{\s*title:\s*"Episode (\d+)"[^}]*\}', js)
    total = len(eps)
    at = {}
    for m in re.finditer(r'\{\s*title:\s*"Episode (\d+)"[^}]*?thumbAt:\s*([\d.]+)', js):
        at[int(m.group(1))] = float(m.group(2))
    return base, pattern, total, at


def exists(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=30).status == 200
    except Exception:
        return False


def fingerprint(img):
    g = np.asarray(img.convert("L").resize((9, 16)), dtype=np.int16)
    return (g[:, 1:] > g[:, :-1]).flatten()             # 128-bit difference hash


def similar(fp, others):
    return any((fp != o).sum() < 22 for o in others)


def score(img):
    a = np.asarray(img.convert("RGB").resize((180, 320)), dtype=np.float32)
    gray = a.mean(axis=2)
    bright = gray.mean()
    if bright < 40 or bright > 215 or gray.std() < 25:
        return -1                                   # too dark, too bright or flat (fades, title cards)
    sharp = (np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean())
    rg, yb = a[..., 0] - a[..., 1], 0.5 * (a[..., 0] + a[..., 1]) - a[..., 2]
    colour = np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    centre = gray[60:220, 30:150].std()             # something happening in the middle (faces, action)
    base = sharp * (1 + colour / 60) * (0.6 + centre / 80)
    if FACES is not None:
        g = cv2.cvtColor(np.asarray(img.convert("RGB").resize((360, 640))), cv2.COLOR_RGB2GRAY)
        faces = FACES.detectMultiScale(g, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
        if len(faces):
            big = max(w * h for (x, y, w, h) in faces) / (360 * 640)
            base *= 2.5 + min(big, 0.12) * 25 + 0.4 * min(len(faces), 3)   # clear faces win, two-shots a bit more
    return base


def frame_at(path, sec):
    with av.open(path) as box:
        st = box.streams.video[0]
        box.seek(int(sec / st.time_base), stream=st, any_frame=False, backward=True)
        for frame in box.decode(st):
            if frame.time is not None and frame.time >= sec - 0.05:
                return frame.to_image()
    return None


def best_frame(path, avoid=()):
    with av.open(path) as box:
        st = box.streams.video[0]
        dur = float(box.duration / av.time_base) if box.duration else float(st.duration * st.time_base)
        best, best_s = None, -1
        t = dur * 0.15
        while t < dur * 0.80:
            box.seek(int(t / st.time_base), stream=st, any_frame=False, backward=True)
            for frame in box.decode(st):
                if frame.time is not None and frame.time >= t - 0.05:
                    img = frame.to_image()
                    s = score(img)
                    if s > 0 and similar(fingerprint(img), avoid):
                        s *= 0.05                       # same shot as another episode's thumbnail
                    if s > best_s:
                        best, best_s = img, s
                    break
            t += 1.0
    return best


def main():
    base, pattern, total, thumb_at = config()
    os.makedirs(OUT, exist_ok=True)
    force = os.environ.get("FORCE") == "1"
    made = 0
    # fingerprints of the thumbnails we keep, so a new one never repeats another episode's shot
    kept = {}
    for n in range(1, total + 1):
        f = os.path.join(OUT, f"ps-ep{n:02d}.jpg")
        if os.path.exists(f) and not force:
            kept[n] = fingerprint(Image.open(f))
    for n in range(1, total + 1):
        dst = os.path.join(OUT, f"ps-ep{n:02d}.jpg")
        if os.path.exists(dst) and not force:
            continue
        url = base + pattern.replace("{nn}", f"{n:02d}")
        if not exists(url):
            continue
        with tempfile.TemporaryDirectory() as tmp:
            mp4 = os.path.join(tmp, "ep.mp4")
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(mp4, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            img = frame_at(mp4, thumb_at[n]) if n in thumb_at else best_frame(mp4, [v for k, v in kept.items() if k != n])
        if img is None:
            print(f"EP{n:02d}: no usable frame")
            continue
        w, h = img.size
        tw = min(w, int(h * 9 / 16))                # crop to 9:16 if needed
        img = img.crop(((w - tw) // 2, 0, (w - tw) // 2 + tw, h)).resize((360, 640), Image.LANCZOS)
        img.save(dst, "JPEG", quality=82, optimize=True, progressive=True)
        kept[n] = fingerprint(img)
        print(f"EP{n:02d}: thumbnail saved ({os.path.getsize(dst) // 1024} KB)")
        made += 1
    print(f"{made} thumbnail(s) made")
    return 0


if __name__ == "__main__":
    sys.exit(main())
