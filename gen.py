#!/usr/bin/env python3
"""Generador de vídeos verticales ÉLVARA (1080x1920, 30 fps).

Uso:
  python3 gen.py --concept regalo --seed 20261106 --date 2026-11-06 --out out/2026-11-06.mp4
  python3 gen.py --concept regalo --seed 20261106 --date 2026-11-06 --preview out/prev.jpg
  python3 gen.py --list            (muestra conceptos disponibles hoy)
"""
import argparse, datetime as dt, json, os, random, subprocess, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(ROOT, "assets", *p)
CAT = json.load(open(os.path.join(ROOT, "catalog.json"), encoding="utf-8"))
W, H, FPS = 1080, 1920, 30
BOLD, LIGHT = A("fonts", "Poppins-Bold.ttf"), A("fonts", "Poppins-Light.ttf")
PALETTES = {"oro": (214, 182, 120), "oro_rosa": (222, 170, 150), "champan": (232, 210, 160)}
DARK = (140, 104, 52)
BEIGE = np.array([214, 224, 238], np.float32)

def ease(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3

def rmask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    return np.array(m, np.float32)[..., None] / 255.0

def shadow(x0, y0, w, h):
    s = Image.new("L", (W, H), 0)
    ImageDraw.Draw(s).rounded_rectangle([x0, y0 + 20, x0 + w, y0 + 20 + h], 36, fill=200)
    return np.array(s.filter(ImageFilter.GaussianBlur(30)), np.float32)[..., None] / 255.0

def text_block(text, font, fill, tracking=0, shadow_px=0):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = text.split("\n"); lh = font.size * 1.2
    im = Image.new("RGBA", (W, int(lh * len(lines)) + 30), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for n, ln in enumerate(lines):
        w_ = d.textlength(ln, font=font) + tracking * len(ln); x = (W - w_) / 2; y = n * lh
        for ch in (ln if tracking else [ln]):
            dr.text((x, y), ch, font=font, fill=fill)
            if tracking: x += dr.textlength(ch, font=font) + tracking
    if shadow_px:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(shadow_px))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * 0.7)))
        im = Image.alpha_composite(sh, im)
    return np.array(im, np.float32) / 255.0

def blur_bg(img, k=0.33):
    s = cv2.GaussianBlur(cv2.resize(img, (54, 96), interpolation=cv2.INTER_AREA), (0, 0), 3)
    return cv2.resize(s, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) * k

class Video:
    def __init__(self, concept, seed, date):
        self.rng = random.Random(seed); self.date = date
        xmas_end = dt.date.fromisoformat(CAT["christmas_until"])
        self.xmas = date <= xmas_end
        self.dias = (xmas_end - date).days
        self.gold = PALETTES[self.rng.choice(list(PALETTES))]
        self.snow_on = self.xmas
        self.cb = (1000, 720, 560); self.pb = (1000, 1100, 420)
        self.cmask = rmask(1000, 720, 36); self.csh = shadow(40, 560, 1000, 720)
        self.pmask = rmask(1000, 1100, 36); self.psh = shadow(40, 420, 1000, 1100)
        spec = CAT["concepts"][concept]["scenes"]
        self.scenes = []; used = set()
        for i, (kind, cat, ks, ts, ss) in enumerate(spec):
            opts = [c for c in CAT["categories"][cat] if c not in used] or CAT["categories"][cat]
            src = self.rng.choice(opts); used.add(src)
            k = self.rng.choice(ks); t = self.rng.choice(ts).replace("{dias}", str(self.dias)); s = self.rng.choice(ss)
            dur = 2.4 if i == 0 else (2.3 if kind == "full" else self.rng.choice([1.6, 1.8, 2.0, 2.2]))
            if kind == "box" and cat in ("red", "amber", "blue", "purple") and concept in ("colores", "pregunta"):
                dur = 1.7
            self.scenes.append(dict(kind=kind, src=src, k=k, t=t, s=s, dur=dur))
        self.scenes.append(dict(kind="outro", dur=3.0))
        self.xf = self.rng.choice([0.22, 0.28, 0.35])
        self._load()
        self.starts = []; acc = 0.0
        for s in self.scenes: self.starts.append(acc); acc += s["dur"] - self.xf
        self.total = acc + self.xf
        self._particles()

    # ---------- assets
    def _clip(self, name):
        cap = cv2.VideoCapture(A("clips", name + ".mp4")); fr = []
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(f)
        if self.rng.random() < 0.3 and len(fr) > 40:  # a veces cámara lenta suave
            fr = [fr[i // 2] for i in range(len(fr) * 2)]
        return fr

    def _blocks(self, k, t, s, top, bottom, on_photo=False):
        b = []; sp = 10 if on_photo else 0
        tf = ImageFont.truetype(BOLD, 84 if ("\n" not in t and len(t) < 20) else 76)
        tb = text_block(t, tf, (255, 255, 255, 255), shadow_px=sp) if t else None
        th = tb.shape[0] if tb is not None else 0
        ty = top - 60 - th
        if k: b.append((text_block(k, ImageFont.truetype(BOLD, 34), self.gold + (255,), 8, sp), ty - 60))
        if tb is not None: b.append((tb, ty))
        if s: b.append((text_block(s, ImageFont.truetype(LIGHT, 44), (240, 240, 240, 255), shadow_px=sp), bottom + 60))
        return b, ty + th + 6

    def _load(self):
        logo = cv2.resize(cv2.imread(A("logo.jpg")), (1080, 720), interpolation=cv2.INTER_AREA).astype(np.float32)
        fy, fx = np.mgrid[0:720, 0:1080].astype(np.float32)
        self.logo = logo
        self.feather = np.clip(np.minimum.reduce([fx / 120, (1079 - fx) / 120, fy / 120, (719 - fy) / 120]), 0, 1)
        grad = np.linspace(1.03, 0.94, H, dtype=np.float32)[:, None, None]
        self.beige = np.ones((H, W, 3), np.float32) * BEIGE * grad
        for s in self.scenes:
            if s["kind"] == "box":
                s["frames"] = self._clip(s["src"]); s["blocks"], s["ly"] = self._blocks(s["k"], s["t"], s["s"], 560, 1280)
            elif s["kind"] == "photo":
                im = cv2.imread(A("photos", s["src"] + ".jpg")); h, w = im.shape[:2]
                sc = max(1000 / w, 1100 / h) * 1.06
                s["img"] = cv2.resize(im, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_AREA)
                s["bg"] = blur_bg(s["img"]); s["blocks"], s["ly"] = self._blocks(s["k"], s["t"], s["s"], 420, 1520)
            elif s["kind"] == "full":
                im = cv2.imread(A("photos", s["src"] + ".jpg")); h, w = im.shape[:2]
                sc = max(W / w, H / h) * 1.12
                s["img"] = cv2.resize(im, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_AREA)
                s["blocks"], s["ly"] = self._blocks(s["k"], s["t"], s["s"], 470, 1500, on_photo=True)
                s["dir"] = self.rng.choice([-1, 1])
            else:
                s["blocks"] = [(text_block(f"Máscara LED · {CAT['price']}", ImageFont.truetype(BOLD, 70), (70, 52, 32, 255)), 1420),
                               (text_block(f"Envío gratis · {CAT['web']}", ImageFont.truetype(LIGHT, 42), DARK + (255,)), 1525)]
                s["ly"] = 1395
        g = np.linspace(0, 1, H, dtype=np.float32)
        self.vignette = (0.55 * np.clip(1 - g / 0.35, 0, 1) ** 1.5 + 0.6 * np.clip((g - 0.7) / 0.3, 0, 1) ** 1.5)[:, None, None]

    def _particles(self):
        r = np.random.default_rng(self.rng.randint(0, 10**6)); n = 70
        self.px, self.py0 = r.uniform(0, W, n), r.uniform(0, H, n)
        self.ps, self.pr = r.uniform(70, 160, n), r.uniform(2.5, 7, n)
        self.psw, self.pg = r.uniform(0, 6.28, n), r.random(n) < 0.55
        self.sprites = {}

    def _sprite(self, rad):
        k = round(rad * 2) / 2
        if k not in self.sprites:
            s = int(k * 6) | 1; c = s // 2; yy, xx = np.mgrid[0:s, 0:s]
            self.sprites[k] = np.clip(1 - np.sqrt((yy - c) ** 2 + (xx - c) ** 2) / (k * 2.6), 0, 1) ** 1.6
        return self.sprites[k]

    def _snow(self, f, t, strength):
        gold = np.array(self.gold[::-1], np.float32)
        for i in range(len(self.px)):
            y = (self.py0[i] + self.ps[i] * t) % (H + 40) - 20; x = self.px[i] + 18 * np.sin(self.psw[i] + t * 1.3)
            sp = self._sprite(self.pr[i]); s = sp.shape[0]; x0, y0 = int(x - s / 2), int(y - s / 2)
            if x0 < 0 or y0 < 0 or x0 + s > W or y0 + s > H: continue
            col = gold if self.pg[i] else np.array([255, 255, 255], np.float32)
            a = sp[..., None] * 0.75 * strength; reg = f[y0:y0 + s, x0:x0 + s]
            f[y0:y0 + s, x0:x0 + s] = reg * (1 - a) + col * a

    # ---------- render
    def _text(self, f, blocks, t, ly):
        lw = int(160 * ease((t - 0.25) / 0.4))
        if lw > 2 and blocks: f[ly:ly + 3, W // 2 - lw // 2:W // 2 + lw // 2] = np.array(self.gold[::-1], np.float32)
        for n, (arr, y) in enumerate(blocks):
            a = ease((t - 0.05 - n * 0.1) / 0.4)
            if a <= 0: continue
            yy = int(y + (1 - a) * 26); h_ = min(arr.shape[0], H - yy)
            f[yy:yy + h_] = f[yy:yy + h_] * (1 - arr[:h_, :, 3:4] * a) + arr[:h_, :, 2::-1] * 255.0 * arr[:h_, :, 3:4] * a

    def _logo(self, t, dur, ly):
        z = 1.0 + 0.04 * t / dur
        lg = cv2.resize(self.logo, None, fx=z, fy=z, interpolation=cv2.INTER_LINEAR)
        fe = cv2.resize(self.feather, (lg.shape[1], lg.shape[0]))[..., None]
        y0 = max(0, int(ly - lg.shape[0] / 2)); x0 = int((W - lg.shape[1]) / 2); cx = max(0, -x0)
        lg, fe, x0 = lg[:, cx:cx + W], fe[:, cx:cx + W], max(0, x0)
        f = self.beige.copy(); reg = f[y0:y0 + lg.shape[0], x0:x0 + lg.shape[1]]
        f[y0:y0 + lg.shape[0], x0:x0 + lg.shape[1]] = reg * (1 - fe) + lg * fe
        return f

    def render(self, s, t):
        k, dur = s["kind"], s["dur"]
        if k == "outro":
            f = self._logo(t, dur, 860); self._text(f, s["blocks"], t, s["ly"]); return f
        if k == "box":
            fr = s["frames"]; im = fr[min(int(t * FPS), len(fr) - 1)]
            M = cv2.getRotationMatrix2D((500, 360), 0, 1.0 + 0.05 * t / dur)
            im = cv2.warpAffine(im, M, (1000, 720), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            f = blur_bg(im) * (1 - self.csh * 0.85); reg = f[560:1280, 40:1040]
            f[560:1280, 40:1040] = reg * (1 - self.cmask) + im.astype(np.float32) * self.cmask
        elif k == "photo":
            im = s["img"]; ih, iw = im.shape[:2]; z = 1.0 + 0.05 * t / dur
            ww, wh = 1000 * 1.06 / z, 1100 * 1.06 / z; cx, cy = iw / 2, min(max(ih * 0.5, wh / 2), ih - wh / 2)
            M = np.float32([[1000 / ww, 0, -(cx - ww / 2) * 1000 / ww], [0, 1100 / wh, -(cy - wh / 2) * 1100 / wh]])
            crop = cv2.warpAffine(im, M, (1000, 1100), flags=cv2.INTER_LINEAR)
            f = s["bg"] * (1 - self.psh * 0.85); reg = f[420:1520, 40:1040]
            f[420:1520, 40:1040] = reg * (1 - self.pmask) + crop.astype(np.float32) * self.pmask
        else:  # full-bleed foto con Ken Burns y degradados
            im = s["img"]; ih, iw = im.shape[:2]; p = t / dur
            z = 1.0 + 0.07 * p; ww, wh = W * 1.12 / z, H * 1.12 / z
            cx = iw / 2 + s["dir"] * (iw - ww) * 0.35 * (p - 0.5); cy = ih * 0.52
            cx = min(max(cx, ww / 2), iw - ww / 2); cy = min(max(cy, wh / 2), ih - wh / 2)
            M = np.float32([[W / ww, 0, -(cx - ww / 2) * W / ww], [0, H / wh, -(cy - wh / 2) * H / wh]])
            f = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32) * (1 - self.vignette)
        self._text(f, s["blocks"], t, s["ly"]); return f

    def frame(self, t):
        out = None; ow = 0.0
        for i, s in enumerate(self.scenes):
            lt = t - self.starts[i]
            if 0 <= lt < s["dur"]:
                f = self.render(s, lt); w = 1.0 if s["kind"] == "outro" else 0.0
                if out is None: out, ow = f, w
                else:
                    a = lt / self.xf; a = a * a * (3 - 2 * a); out = out * (1 - a) + f * a; ow = ow * (1 - a) + w * a
        if self.snow_on: self._snow(out, t, 1.0 - 0.5 * ow)
        g = min(1.0, (self.total - t) / 0.4)
        return np.clip(out * max(g, 0), 0, 255).astype(np.uint8)

def available(date):
    xmas = date <= dt.date.fromisoformat(CAT["christmas_until"])
    return [c for c, v in CAT["concepts"].items() if xmas or not v.get("christmas_only")]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--concept"); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--out"); ap.add_argument("--preview"); ap.add_argument("--list", action="store_true")
    a = ap.parse_args(); d = dt.date.fromisoformat(a.date)
    if a.list: print("\n".join(available(d))); sys.exit()
    v = Video(a.concept, a.seed, d)
    print(json.dumps({"concept": a.concept, "seconds": round(v.total, 2),
                      "scenes": [{k: s.get(k) for k in ("kind", "src", "k", "t", "s")} for s in v.scenes]}, ensure_ascii=False))
    if a.preview:
        ts = [v.starts[i] + v.scenes[i]["dur"] * 0.6 for i in range(len(v.scenes))]
        cv2.imwrite(a.preview, np.hstack([cv2.resize(v.frame(t), (270, 480)) for t in ts]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    if a.out:
        tmp = a.out + ".tmp.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                              "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
        for n in range(int(v.total * FPS)): p.stdin.write(v.frame(n / FPS).tobytes())
        p.stdin.close(); p.wait()
        if p.returncode == 0: os.replace(tmp, a.out); print("OK", a.out)
        else: sys.exit("ffmpeg falló")
