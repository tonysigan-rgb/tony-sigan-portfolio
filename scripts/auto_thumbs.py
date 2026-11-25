"""Episode thumbnails (runs in GitHub Actions with the auto-subtitles job).

For every ps-epNN.mp4 in the Cloudflare folder without assets/thumbs/ps-epNN.jpg, pick a striking frame
(sharp, well lit, colourful; from 10%-70% of the episode, skipping dark/blank frames) and save a
360x640 JPEG. Run with FORCE=1 to remake all of them.
"""
import io, os, re, sys, tempfile, urllib.request

import av
import numpy as np
from PIL import Image

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
    return sharp * (1 + colour / 60) * (0.6 + centre / 80)


def best_frame(path):
    with av.open(path) as box:
        st = box.streams.video[0]
        dur = float(box.duration / av.time_base) if box.duration else float(st.duration * st.time_base)
        best, best_s = None, -1
        t = dur * 0.10
        while t < dur * 0.70:
            box.seek(int(t / st.time_base), stream=st, any_frame=False, backward=True)
            for frame in box.decode(st):
                if frame.time is not None and frame.time >= t - 0.05:
                    img = frame.to_image()
                    s = score(img)
                    if s > best_s:
                        best, best_s = img, s
                    break
            t += 1.5
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
