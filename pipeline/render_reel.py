# Render genérico de un Reel "El Chico y El Robot" a partir de un guion JSON.
# Estilo: fondo negro/dorado, subtítulos pequeños palabra a palabra con palabra clave en caja,
# tarjetas de datos animadas, voces Kokoro, música trap suave y efectos.
# Uso: python3 pipeline/render_reel.py guion.json salida.mp4
#
# v2 (2026-11-07, "más entretenidos"): gancho visible en el fotograma 0 (tarjeta del gancho grande desde t=0),
# voz desde 0,05 s, pausas más cortas, voces algo más rápidas, cámara con cortes (primer plano del que
# habla / plano general), zoom de golpe en palabras clave, subtítulos grandes por bloques de 1-3 palabras
# tipo Hormozi, destello + temblor en el sello, interrupciones del robot ("interrumpe": true) y barra de progreso.
# Ver pipeline/GANCHOS.md para cómo escribir guiones que enganchen.
#
# Formato del guion (ver pipeline/guion_ejemplo.json):
# {
#   "id": "dia19_natty",
#   "lineas": [
#     {"quien": "chico"|"robot", "texto": "subtítulo", "voz": "texto para TTS (opcional)",
#      "clave": ["palabra"], "animo": "normal|orgullo|susto|sufre (chico)",
#      "pantalla": "ojos|rayas|404 (robot)", "sello": "MITO (opcional)",
#      "interrumpe": true (opcional: esta línea corta a la anterior, empieza 0,3 s antes),
#      "tarjeta": {"tipo": "dato", "etiqueta": "...", "valor": 70, "unidad": "kg", "nota": "..."}
#               | {"tipo": "lista", "titulo": "...", "items": [["nombre", "valor"], ...]}
#               | {"tipo": "titulo", "texto": "TEXTO GRANDE", "sub": "..."}
#               | {"tipo": "cta", "arriba": "COMENTA", "grande": "...", "abajo": "..."} }
#   ]
# }
import json, math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 44100
G = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
WORK = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_work_" + G.get("id", "reel"))
os.makedirs(WORK, exist_ok=True)
KOKORO_DIR = os.environ.get("KOKORO_DIR", "/mnt/project-files/pipeline-cache/kokoro")
FD = "/usr/share/fonts/opentype/inter/"
random.seed(7); np.random.seed(7)
LINES = G["lineas"]
assert 4 <= len(LINES) <= 16, "el guion debe tener entre 4 y 16 líneas"
# Inter no tiene emojis ni símbolos raros: se sustituyen para que no salgan cuadrados
import re
_REP = {"✔": "SÍ", "✓": "SÍ", "✅": "SÍ", "❌": "NO", "✖": "NO", "→": "-", "👇": "", "🔥": "", "💪": ""}
def clean(x):
    if isinstance(x, str):
        for a, b in _REP.items(): x = x.replace(a, b)
        return re.sub(r"[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F]", "", x).strip()
    if isinstance(x, list): return [clean(v) for v in x]
    if isinstance(x, dict): return {k: clean(v) for k, v in x.items()}
    return x
LINES = clean(LINES)
for L in LINES:
    assert L["quien"] in ("chico", "robot"), L
if LINES[0].get("tarjeta", {}).get("tipo") == "titulo": LINES[0]["tarjeta"]["_gancho"] = True

# ---------------- audio ----------------
def read_wav(p):
    with wave.open(p) as w:
        sr = w.getframerate(); n = w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2: a = a.reshape(-1, 2).mean(1)
    if sr != SR:
        a = np.interp(np.linspace(0, len(a), int(len(a) * SR / sr), endpoint=False), np.arange(len(a)), a)
    return a

import soundfile as sf
from kokoro_onnx import Kokoro
KOK = Kokoro(f"{KOKORO_DIR}/kokoro-v1.0.onnx", f"{KOKORO_DIR}/voices-v1.0.bin")
def tts(i, spk, text):
    raw, out = f"{WORK}/l{i}_raw.wav", f"{WORK}/l{i}.wav"
    if spk == "chico":
        a, sr = KOK.create(text, voice="em_alex", speed=1.2, lang="es")
        flt = "asetrate=24000*1.06,aresample=24000,atempo=0.9434,highpass=f=90,acompressor=threshold=-18dB:ratio=3:attack=5:release=80"
    else:
        a, sr = KOK.create(text, voice="em_santa", speed=1.06, lang="es")
        flt = ("asetrate=24000*0.93,aresample=24000,atempo=1.0753,highpass=f=70,aecho=0.9:0.6:9:0.18,"
               "flanger=delay=0.6:depth=0.4:speed=0.3:width=40,acompressor=threshold=-18dB:ratio=3:attack=5:release=80")
    sf.write(raw, a, sr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", flt, "-ar", str(SR), "-ac", "1", out], check=True)
    a = read_wav(out); a = a / max(1e-6, np.abs(a).max()) * 0.8
    nz = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, nz[0] - 200): nz[-1] + 2000] if len(nz) else a

events, t = [], 0.05
for i, L in enumerate(LINES):
    a = tts(i, L["quien"], L.get("voz") or L["texto"])
    if i > 0 and LINES[i - 1]["quien"] != L["quien"]: t += 0.05
    if i > 0 and L.get("tarjeta"): t += 0.08
    if i > 0 and L.get("interrumpe"):
        # corta la línea anterior: se acorta su audio con un fundido y esta empieza encima
        pv = events[-1]; t -= 0.3
        keep = max(int(SR * 0.4), int((t - pv["start"] + 0.12) * SR))
        if keep < len(pv["audio"]):
            pv["audio"] = pv["audio"][:keep].copy(); pv["audio"][-int(SR * .1):] *= np.linspace(1, 0, int(SR * .1))
            pv["dur"] = len(pv["audio"]) / SR
    events.append(dict(L, i=i, start=t, dur=len(a) / SR, audio=a))
    t += len(a) / SR + 0.08
TOTAL = t + 1.2
assert TOTAL <= 89, f"vídeo demasiado largo ({TOTAL:.1f}s)"
N = int(TOTAL * FPS)
mix = np.zeros(int(TOTAL * SR) + SR)
def add(sig, at, gain=1.0):
    s = int(at * SR)
    if 0 <= s < len(mix): mix[s:s + len(sig)] += sig[: len(mix) - s] * gain
for e in events: add(e["audio"], e["start"], 0.95)

tt = lambda d: np.linspace(0, d, int(d * SR), endpoint=False)
def whoosh(d=0.4):
    n = np.random.randn(int(d * SR)); f = np.cumsum(n); f -= np.convolve(f, np.ones(40) / 40, "same")
    return f / np.abs(f).max() * np.hanning(len(n)) * 0.45
def ding(f=880, d=0.8): x = tt(d); return (np.sin(2*np.pi*f*x) + .4*np.sin(2*np.pi*f*2.01*x)) * np.exp(-x*5) * 0.25
def thud():
    x = tt(0.6); return (np.sin(2*np.pi*(45 + 90*np.exp(-x*20))*x) * np.exp(-x*6) + np.random.randn(len(x))*np.exp(-x*25)*.5) * 0.7
def buzz(d=0.35): x = tt(d); return np.sign(np.sin(2*np.pi*140*x)) * np.exp(-x*3) * 0.12
for e in events:
    if e["i"] == 0 or e.get("tarjeta"): add(whoosh(), max(0, e["start"] - 0.3), 0.6)
    elif events[e["i"] - 1]["quien"] != e["quien"]: add(whoosh(0.25), max(0, e["start"] - 0.15), 0.35)
    if e.get("tarjeta"): add(ding(660 + 80 * (e["i"] % 4)), e["start"] + 0.1, 0.7)
    if e.get("sello"): add(thud(), e["start"] + e["dur"] * 0.5, 0.9); add(buzz(), e["start"] + e["dur"] * 0.5 + .05, 1)
bpm = 92; beat = 60 / bpm; x = 0.0; b = 0
while x < TOTAL - 0.5:
    kx = tt(0.3); add(np.sin(2*np.pi*(48 + 110*np.exp(-kx*30))*kx) * np.exp(-kx*9) * .55, x, .45)
    if b % 2 == 1: add(np.random.randn(int(.12*SR)) * np.exp(-np.linspace(0, 9, int(.12*SR))) * .18, x, .45)
    for hh in range(2): add(np.random.randn(int(.025*SR)) * np.exp(-np.linspace(0, 8, int(.025*SR))) * .06, x + hh*beat/2, .45)
    px = tt(beat * .95); f0 = [110, 110, 98, 82.4][(b // 4) % 4]
    add((np.sin(2*np.pi*f0*px) + .3*np.sin(2*np.pi*f0*1.5*px)) * .05 * np.exp(-px*1.2), x, .45)
    x += beat; b += 1
mix = np.tanh(mix[: int(TOTAL * SR)] * 1.1) * 0.9
with wave.open(f"{WORK}/mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())

def level(e, ts):
    i = int((ts - e["start"]) * SR); a = e["audio"][max(0, i - 600): i + 600]
    return float(np.sqrt((a ** 2).mean())) if len(a) else 0.0

# ---------------- dibujo ----------------
fc = {}
def font(sz, wt="Bold"):
    if (sz, wt) not in fc:
        try: fc[(sz, wt)] = ImageFont.truetype(f"{FD}Inter-{wt}.otf", sz)
        except OSError: fc[(sz, wt)] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", sz)
    return fc[(sz, wt)]
GOLD, WHITE, GREY, DIM = (232, 186, 92), (244, 242, 236), (150, 148, 145), (88, 86, 84)
BLUE, RED, SKIN, HAIR = (52, 104, 214), (226, 68, 58), (214, 160, 118), (96, 58, 32)
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def make_bg():
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xs - W * .5) / W) ** 2 + ((ys - H * .62) / H * 1.3) ** 2)
    g = np.clip(1 - r * 1.6, 0, 1) ** 1.6
    img = np.array([9, 9, 11], np.float32) + g[..., None] * np.array([30, 26, 20], np.float32)
    im = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([60, 1740, 1020, 1744], 2, fill=(60, 50, 32))  # suelo dorado
    return im
BG = make_bg()

SS = 2
def sprite_chico(mood, mouth):
    w, h = 420, 560; im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    E = lambda cx, cy, rx, ry, f: d.ellipse([(cx-rx)*SS, (cy-ry)*SS, (cx+rx)*SS, (cy+ry)*SS], fill=f)
    R = lambda x0, y0, x1, y1, r, f: d.rounded_rectangle([x0*SS, y0*SS, x1*SS, y1*SS], r*SS, fill=f)
    face = SKIN if mood != "sufre" else (226, 130, 105)
    R(40, 370, 380, 600, 90, (20, 20, 24))              # camiseta
    E(78, 400, 52, 46, SKIN); E(342, 400, 52, 46, SKIN)  # hombros
    R(110, 360, 310, 420, 30, (20, 20, 24)); R(176, 300, 244, 380, 20, SKIN)  # cuello
    d.text((210*SS, 480*SS), "OLIMPIA", font=font(30*SS, "Black"), fill=GOLD, anchor="mm")
    E(210, 210, 118, 132, face); E(94, 220, 20, 30, face); E(326, 220, 20, 30, face)
    rnd = random.Random(3)
    for k in range(26):
        a = math.radians(10 + 160 * k / 25); r = rnd.randint(100, 122)
        E(210 + math.cos(a) * r, 150 - math.sin(a) * r * .55, rnd.randint(30, 40), rnd.randint(28, 36),
          tuple(int(c * rnd.uniform(.85, 1.2)) for c in HAIR))
    er = 20 if mood == "susto" else 15
    for s in (-1, 1):
        ex = 210 + s * 46
        if mood == "sufre": d.line([((ex-18)*SS, 214*SS), ((ex+18)*SS, 222*SS)], fill=(30, 20, 18), width=8*SS)
        else: E(ex, 216, er, er + 3, (28, 20, 18)); E(ex + 5, 210, 5, 5, (255, 255, 255))
        by = {"normal": 176, "orgullo": 170, "susto": 160, "sufre": 182}[mood]
        d.line([((ex-22)*SS, (by + (6 if mood == "sufre" and s < 0 else 0))*SS), ((ex+22)*SS, (by + (6 if mood == "sufre" and s > 0 else 0))*SS)], fill=(40, 26, 18), width=9*SS)
    d.polygon([(210*SS, 230*SS), (196*SS, 262*SS), (222*SS, 262*SS)], fill=tuple(int(c*.88) for c in face))
    if mood == "susto" or mouth > .5: E(210, 300, 30 if mood == "susto" else 26, 26 if mood == "susto" else 6 + 16 * mouth, (70, 20, 24))
    elif mood == "orgullo": d.arc([170*SS, 260*SS, 250*SS, 315*SS], 20, 160, fill=(70, 30, 30), width=7*SS)
    elif mood == "sufre": R(180, 288, 240, 312, 6, (245, 245, 245))
    else: d.line([(186*SS, 300*SS), (234*SS, 300*SS)], fill=(70, 30, 30), width=7*SS)
    if mood == "sufre":
        for j in range(3): E(110 + j * 20, 120 + j * 30, 7, 11, (140, 200, 255))
    return im.resize((w, h), Image.LANCZOS)

def sprite_robot(screen, mouth, blink):
    w, h = 420, 560; im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    R = lambda x0, y0, x1, y1, r, f: d.rounded_rectangle([x0*SS, y0*SS, x1*SS, y1*SS], r*SS, fill=f)
    cream = (236, 228, 208)
    R(70, 380, 350, 600, 60, (34, 34, 40)); R(110, 410, 310, 470, 16, (20, 20, 24))
    d.text((210*SS, 440*SS), "ENTRENADOR IA", font=font(22*SS, "Bold"), fill=GOLD, anchor="mm")
    R(190, 330, 230, 390, 10, (60, 60, 66))
    d.line([(210*SS, 70*SS), (210*SS, 30*SS)], fill=(90, 90, 96), width=8*SS)
    d.ellipse([196*SS, 14*SS, 224*SS, 42*SS], fill=GOLD)
    for s in (-1, 1): d.ellipse([(210 + s*168 - 24)*SS, 170*SS, (210 + s*168 + 24)*SS, 260*SS], fill=(22, 22, 26))
    R(40, 70, 380, 340, 40, cream); R(66, 96, 354, 314, 26, (8, 8, 12))
    g = (235, 245, 255); cx = 210
    if screen == "404":
        d.text((cx*SS, 170*SS), "ERROR", font=font(52*SS, "Black"), fill=RED, anchor="mm")
        d.text((cx*SS, 245*SS), "404", font=font(70*SS, "Black"), fill=RED, anchor="mm")
        return im.resize((w, h), Image.LANCZOS)
    for s in (-1, 1):
        ex = cx + s * 66
        if screen == "rayas":
            for k in range(3): R(ex - 36, 140 + k * 16, ex + 36, 147 + k * 16, 2, g)
        else:
            R(ex - 26, 136 + (20 if blink else 0), ex + 26, 190 - (20 if blink else 0), 4, g)
    mw = 50 + 56 * mouth; mh = 10 + 26 * mouth
    R(cx - mw, 250 - mh / 2, cx + mw, 250 + mh / 2, 3, g)
    return im.resize((w, h), Image.LANCZOS)

spr = {}
def get_spr(kind, *a):
    if (kind, a) not in spr: spr[(kind, a)] = (sprite_chico if kind == "chico" else sprite_robot)(*a)
    return spr[(kind, a)]

def card(d, x0, y0, x1, y1):
    d.rounded_rectangle([x0, y0, x1, y1], 22, fill=(20, 20, 23), outline=(48, 46, 42), width=2)

def fit(text, size, wt, maxw):
    while size > 20 and font(size, wt).getlength(text) > maxw: size -= 2
    return font(size, wt)

def draw_card(d, c, k):
    a = ease(k / .35); y0 = 520 + int(40 * (1 - a)); x0, x1 = 70, 1010
    tipo = c.get("tipo", "dato")
    if tipo == "dato":
        card(d, x0, y0, x1, y0 + 300)
        d.text((x0 + 34, y0 + 50), str(c.get("etiqueta", "")).upper(), font=fit(str(c.get("etiqueta", "")).upper(), 30, "SemiBold", 860), fill=GREY, anchor="lm")
        v = c.get("valor", "")
        try:
            vf = float(str(v).replace(",", ".")); cur = vf * ease(k / .7)
            vs = (f"{cur:.1f}".replace(".", ",") if (vf != int(vf)) else f"{int(round(cur))}")
        except ValueError: vs = str(v)
        fv = fit(vs, 150, "Black", 640)
        d.text((x0 + 34, y0 + 165), vs, font=fv, fill=GOLD, anchor="lm")
        d.text((x0 + 34 + fv.getlength(vs) + 16, y0 + 190), str(c.get("unidad", "")), font=font(54, "Bold"), fill=GOLD, anchor="lm")
        if c.get("nota"): d.text((x0 + 34, y0 + 260), c["nota"], font=fit(c["nota"], 34, "Medium", 870), fill=WHITE, anchor="lm")
    elif tipo == "lista":
        items = c.get("items", [])[:5]; hh = 110 + 62 * len(items)
        card(d, x0, y0, x1, y0 + hh)
        d.text((x0 + 34, y0 + 50), str(c.get("titulo", "")).upper(), font=fit(str(c.get("titulo", "")).upper(), 30, "SemiBold", 860), fill=GOLD, anchor="lm")
        for i, it in enumerate(items):
            on = ease((k - .25 - i * .45) / .25)
            if on <= 0: continue
            y = y0 + 115 + i * 62
            col = tuple(int(DIM[j] + (WHITE[j] - DIM[j]) * on) for j in range(3))
            d.text((x0 + 34, y), str(it[0]), font=fit(str(it[0]), 38, "Bold", 600), fill=col, anchor="lm")
            if len(it) > 1: d.text((x1 - 34, y), str(it[1]), font=fit(str(it[1]), 38, "Black", 280), fill=GOLD, anchor="rm")
    elif tipo == "titulo" and c.get("_gancho"):
        # gancho: visible desde el fotograma 0, enorme, con rebote
        sc = 1 + .25 * max(0, 1 - k / .12) * math.cos(k * 40); y0 = 470
        card(d, x0 - 20, y0, x1 + 20, y0 + 330)
        d.rounded_rectangle([x0 - 20, y0, x1 + 20, y0 + 12], 6, fill=RED)
        d.text((540, y0 + 140), c.get("texto", ""), font=fit(c.get("texto", ""), int(118 * sc), "Black", int(900 * sc)), fill=GOLD, anchor="mm",
               stroke_width=4, stroke_fill=(0, 0, 0))
        if c.get("sub"): d.text((540, y0 + 262), c["sub"], font=fit(c["sub"], 46, "Bold", 880), fill=WHITE, anchor="mm")
    elif tipo == "titulo":
        card(d, x0, y0, x1, y0 + 240)
        d.text((540, y0 + 105), c.get("texto", ""), font=fit(c.get("texto", ""), 84, "Black", 860), fill=GOLD, anchor="mm")
        if c.get("sub"): d.text((540, y0 + 185), c["sub"], font=fit(c["sub"], 36, "Medium", 860), fill=WHITE, anchor="mm")
    elif tipo == "cta":
        card(d, x0, y0, x1, y0 + 260)
        d.text((540, y0 + 62), c.get("arriba", "COMENTA"), font=font(34, "SemiBold"), fill=GREY, anchor="mm")
        d.text((540, y0 + 140), c.get("grande", ""), font=fit(c.get("grande", ""), 70, "Black", 860), fill=GOLD, anchor="mm")
        d.text((540, y0 + 212), c.get("abajo", ""), font=fit(c.get("abajo", ""), 34, "Medium", 860), fill=WHITE, anchor="mm")

def stamp(im, text, k):
    a = ease(k / .18); s = 1.6 - .6 * a
    f = fit(text, int(84 * s), "Black", 760)
    lay = Image.new("RGBA", (1000, 300), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    tw = f.getlength(text)
    ld.rounded_rectangle([500 - tw/2 - 30, 150 - 62*s, 500 + tw/2 + 30, 150 + 62*s], 18, outline=RED + (int(255*a),), width=10)
    ld.text((500, 150), text, font=f, fill=RED + (int(255*a),), anchor="mm")
    im.alpha_composite(lay.rotate(-8, resample=Image.BICUBIC), (40, 560))

def norm(w): return w.strip("¿?¡!.,:;\"'()").lower()
SUB_Y = 930
def chunks_of(words, kws):
    # bloques de 1-3 palabras; se corta tras puntuación y antes/después de una palabra clave larga
    f = font(84, "Black"); out, cur = [], []
    for i, w in enumerate(words):
        if cur and (len(cur) >= 3 or f.getlength(" ".join(x for _, x in cur + [(i, w)])) > 900): out.append(cur); cur = []
        cur.append((i, w))
        if w[-1] in ".,!?:;" : out.append(cur); cur = []
    if cur: out.append(cur)
    return out
def subtitle(d, e, ts):
    words = e["texto"].split(); kws = {norm(k) for k in e.get("clave", [])}
    if "_chunks" not in e: e["_chunks"] = chunks_of(words, kws)
    wts = [len(w) + 2 for w in words]; tot = sum(wts)
    p = (ts - e["start"]) / max(.1, e["dur"]); acc, spoken, wstart = 0, 0, e["start"]
    for i, w in enumerate(wts):
        if p >= acc / tot: spoken = i + 1; wstart = e["start"] + acc / tot * e["dur"]
        acc += w
    cur_w = max(0, spoken - 1)
    ch = next(c for c in e["_chunks"] if any(i == cur_w for i, _ in c))
    pop = 1 + .14 * max(0, 1 - (ts - wstart) / .09)
    f = font(84, "Black"); sp = 22
    ws = [(i, w, font(int(84 * (pop if i == cur_w else 1)), "Black").getlength(w) + (40 if norm(w) in kws else 0)) for i, w in ch]
    tw = sum(x for _, _, x in ws) + sp * (len(ws) - 1); x = W / 2 - tw / 2
    for i, w, wl in ws:
        iskw = norm(w) in kws; now = i == cur_w
        fz = font(int(84 * (pop if now else 1)), "Black")
        if iskw and i <= cur_w:
            d.rounded_rectangle([x - 4, SUB_Y - 56, x + wl + 4, SUB_Y + 54], 14, fill=GOLD)
            d.text((x + 20, SUB_Y), w, font=fz, fill=(12, 12, 14), anchor="lm")
        else:
            col = (255, 226, 92) if now else WHITE
            d.text((x + (20 if iskw else 0), SUB_Y), w, font=fz, fill=col, anchor="lm", stroke_width=7, stroke_fill=(0, 0, 0))
        x += wl + sp
    who = "EL CHICO" if e["quien"] == "chico" else "EL ROBOT"
    d.text((540, 140), who, font=font(30, "Bold"), fill=GOLD, anchor="mm")

def kw_hit(e, ts):
    # segundos desde que se dijo la última palabra clave de la línea (para el zoom de golpe)
    words = e["texto"].split(); kws = {norm(k) for k in e.get("clave", [])}
    if not kws: return 9
    tot = sum(len(w) + 2 for w in words); acc, best = 0, 9
    for w in words:
        at = e["start"] + acc / tot * e["dur"]
        if norm(w) in kws and at <= ts: best = ts - at
        acc += len(w) + 2
    return best

# ---------------- render ----------------
proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                         "-i", f"{WORK}/mix.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
                         "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
ONLY = [int(x) for x in os.environ.get("ONLY", "").split(",") if x]
cur_e, card_e, last_mood = events[0], None, "normal"
FIRST_ROBOT = next((e["i"] for e in events if e["quien"] == "robot"), 99)
for fi in (ONLY or range(N)):
    ts = fi / FPS
    for e in events:
        if ts >= e["start"] - 0.15: cur_e = e
    card_e = None
    for e in events:
        if e.get("tarjeta") and (ts >= e["start"] - .1 or e["i"] == 0): card_e = e
    # la tarjeta del gancho desaparece cuando entra el robot
    if card_e and card_e["i"] == 0 and cur_e["i"] >= FIRST_ROBOT: card_e = None
    im = BG.copy()
    talking = ts <= cur_e["start"] + cur_e["dur"]
    lv = level(cur_e, ts) if talking else 0
    mouth = min(1, lv * 10)
    k = ts - cur_e["start"]
    # chico (izquierda) y robot (derecha); quien habla se adelanta
    chico_e = max([e for e in events if e["quien"] == "chico" and e["start"] - .15 <= ts] or [None], key=lambda e: e["start"] if e else -1)
    robot_e = max([e for e in events if e["quien"] == "robot" and e["start"] - .15 <= ts] or [None], key=lambda e: e["start"] if e else -1)
    mood = (chico_e or {}).get("animo", "normal")
    screen = (robot_e or {}).get("pantalla", "ojos")
    if screen == "404" and int(ts * 3) % 3: screen = "rayas"
    for kind in ("chico", "robot"):
        active = cur_e["quien"] == kind
        sp = get_spr(kind, mood, round(mouth if active else 0, 1)) if kind == "chico" else \
             get_spr(kind, screen, round(mouth if active else 0, 1), (ts % 3.1) < .1)
        sc = 1.0 if active else 0.82
        pop = (1 + .06 * max(0, 1 - k * 5)) if active else 1
        s2 = sp.resize((int(sp.width * sc * pop), int(sp.height * sc * pop)), Image.BILINEAR)
        if not active:
            s2 = Image.blend(Image.new("RGBA", s2.size, (0, 0, 0, 0)), s2, .55)
        bob = math.sin(ts * (6 if active and talking else 2)) * (6 if active and talking else 3)
        shake = (8 * math.sin(ts * 70) if kind == "chico" and mood in ("susto", "sufre") and active else 0)
        cx = 290 if kind == "chico" else 790
        im.alpha_composite(s2, (int(cx - s2.width / 2 + shake), int(1742 - s2.height + bob)))
    # cámara: corte seco en cada línea. Gancho = primer plano fuerte; luego alterna primer plano del que
    # habla y plano general (cada 3ª línea) para que la imagen cambie cada 2-3 s.
    ci = cur_e["i"]
    if ci == 0: z, fx = 1.4, 290
    elif ci % 3 == 2: z, fx = 1.0, 540
    else: z, fx = 1.22, (290 if cur_e["quien"] == "chico" else 790)
    z *= 1.0 + 0.05 * max(0, 1 - k * 4)                     # golpe al entrar la línea
    z *= 1.0 + 0.07 * max(0, 1 - kw_hit(cur_e, ts) / .18)   # golpe en la palabra clave
    sello_k = k - cur_e["dur"] * .5 if cur_e.get("sello") else -1
    shx = int(18 * math.sin(ts * 90) * max(0, 1 - sello_k / .3)) if 0 <= sello_k < .3 else 0
    cw, ch = W / z, H / z   # el suelo (y=1742) queda siempre abajo, bajo los subtítulos
    bx0 = min(max(fx - cw / 2, 0), W - cw); by0 = min(max(1742 - 1800 / z, 0), H - ch)
    scene = im.resize((W, H), Image.BILINEAR, box=(bx0, by0, bx0 + cw, by0 + ch)) if z > 1.001 else im
    if shx: scene = scene.transform((W, H), Image.AFFINE, (1, 0, -shx, 0, 1, 0))
    im = scene.copy(); d = ImageDraw.Draw(im)
    if card_e: draw_card(d, card_e["tarjeta"], ts - card_e["start"])
    if cur_e.get("sello") and k > cur_e["dur"] * .5:
        stamp(im, cur_e["sello"], k - cur_e["dur"] * .5)
    subtitle(d, cur_e, max(ts, cur_e["start"] + .01))
    d.rectangle([0, H - 10, int(W * ts / TOTAL), H], fill=GOLD)   # barra de progreso
    frame = im.convert("RGB")
    if 0 <= sello_k < .08:   # destello blanco al poner el sello
        frame = Image.blend(frame, Image.new("RGB", (W, H), (255, 255, 255)), .55 * (1 - sello_k / .08))
    if ONLY: frame.save(f"{WORK}/f{fi:04d}.png"); continue
    proc.stdin.write(frame.tobytes())
proc.stdin.close(); rc = proc.wait()
if ONLY: sys.exit(0)
assert rc == 0 and os.path.getsize(OUT) > 200_000, "ffmpeg falló"
print(json.dumps({"ok": True, "salida": OUT, "duracion": round(TOTAL, 2), "frames": N, "mb": round(os.path.getsize(OUT) / 1e6, 2)}))
