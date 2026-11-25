"""Episode thumbnails (runs in GitHub Actions with the auto-subtitles job).

For every ps-epNN.mp4 in the Cloudflare folder without assets/thumbs/ps-epNN.jpg, pick a striking frame
and save a 360x640 JPEG: from the middle of the episode (after the opening titles and name captions),
preferring frames with clear faces, then sharp, well lit and colourful. Run with FORCE=1 to remake all.
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
    total = len(re.findall(r'\{\s*title:\s*"Episode \d+"', js))
    return base, pattern, total


def exists(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=30).status == 200
    except Exception:
        return False


def caption_amount(a):
    """How much of the frame is gold/yellow name-caption text (thin bright strokes, not lamp glow)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r > 170) & (g > 120) & (b < 120) & (r - b > 80)
    if m.mean() < 0.0008:
        return 0.0
    inner = m[1:-1, 1:-1] & m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]
    edge_ratio = 1 - inner.sum() / max(1, m[1:-1, 1:-1].sum())      # text = mostly edges; glow = solid blobs
    return float(m.mean()) if edge_ratio > 0.55 else 0.0


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
    big = np.asarray(img.convert("RGB").resize((360, 640)), dtype=np.int16)
    if caption_amount(big) > 0.0015:
        base *= 0.15                                # on-screen name captions / titles: avoid
    if FACES is not None:
        g = cv2.cvtColor(np.asarray(img.convert("RGB").resize((360, 640))), cv2.COLOR_RGB2GRAY)
        faces = FACES.detectMultiScale(g, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
        if len(faces):
            big = max(w * h for (x, y, w, h) in faces) / (360 * 640)
            base *= 2.5 + min(big, 0.12) * 25 + 0.4 * min(len(faces), 3)   # clear faces win, two-shots a bit more
    return base


def best_frame(path):
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
                    if s > best_s:
                        best, best_s = img, s
                    break
            t += 1.0
    return best


def main():
    base, pattern, total = config()
    os.makedirs(OUT, exist_ok=True)
    force = os.environ.get("FORCE") == "1"
    made = 0
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
            img = best_frame(mp4)
        if img is None:
            print(f"EP{n:02d}: no usable frame")
            continue
        w, h = img.size
        tw = min(w, int(h * 9 / 16))                # crop to 9:16 if needed
        img = img.crop(((w - tw) // 2, 0, (w - tw) // 2 + tw, h)).resize((360, 640), Image.LANCZOS)
        img.save(dst, "JPEG", quality=82, optimize=True, progressive=True)
        print(f"EP{n:02d}: thumbnail saved ({os.path.getsize(dst) // 1024} KB)")
        made += 1
    print(f"{made} thumbnail(s) made")
    return 0


if __name__ == "__main__":
    sys.exit(main())
